"""
The ADW runner against real `uv run` subprocesses of dummy workflows in a temp adws/
directory: discovery, run.log capture, and cancel_adw stopping the whole process group.
Rows are an in-memory stand-in for the ai_developer_workflows table.
"""

import asyncio
import os
import time
from pathlib import Path

import pytest

from fakes import ADW_ID  # first: puts adws/ on sys.path

from adw_modules.adw_summarizer import summary_options
from adw_triggers.adw_scripts import (
    UnknownWorkflowError,
    cancel_adw,
    discover_workflows,
    start_workflow,
)

HEADER = '# /// script\n# requires-python = ">=3.11"\n# dependencies = []\n# ///\n'


def make_adws(tmp_path: Path, **workflows: str) -> Path:
    adws = tmp_path / "adws"
    (adws / "adw_workflows").mkdir(parents=True)
    for name, body in workflows.items():
        (adws / "adw_workflows" / f"adw_{name}.py").write_text(HEADER + body)
    return adws


def wait_for(predicate, timeout=60.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.05)
    return False


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    # A zombie still answers kill(0); it has exited.
    status = Path(f"/proc/{pid}/stat")
    return not (status.exists() and status.read_text().split(") ", 1)[1].startswith("Z"))


def test_discovers_the_real_workflows_with_their_step_counts():
    workflows = discover_workflows()
    assert {name: w.total_steps for name, w in workflows.items()} == {
        "plan_build": 2, "plan_build_review": 3, "plan_build_review_fix": 4,
    }


def test_files_without_total_steps_are_not_workflows(tmp_path):
    adws = make_adws(tmp_path, real='"""Real one."""\nTOTAL_STEPS = 1\n', helper='"""Not a workflow."""\n')
    assert list(discover_workflows(adws)) == ["real"]
    assert discover_workflows(adws)["real"].description == "Real one."


def test_unknown_type_and_bad_id_are_refused_before_spawning(tmp_path):
    adws = make_adws(tmp_path, real="TOTAL_STEPS = 1\n")
    with pytest.raises(UnknownWorkflowError, match="Available: real"):
        start_workflow(ADW_ID, "../../etc/passwd", adws)
    with pytest.raises(ValueError):
        start_workflow("../escape", "real", adws)
    assert not (tmp_path / "agents").exists()


def test_stdout_and_stderr_go_to_the_run_log(tmp_path):
    adws = make_adws(tmp_path, noisy=(
        "import sys\nTOTAL_STEPS = 1\n"
        "print('to stdout', flush=True)\n"
        "print('to stderr', file=sys.stderr, flush=True)\n"
        "raise SystemExit(3)\n"
    ))
    handle = start_workflow(ADW_ID, "noisy", adws)
    _, status = os.waitpid(handle.pid, 0)

    assert os.waitstatus_to_exitcode(status) == 3
    assert handle.log_path == tmp_path / "agents" / "adw" / ADW_ID / "run.log"
    log = handle.log_path.read_text()
    assert "to stdout" in log and "to stderr" in log
    assert handle.metadata() == {"pid": handle.pid, "log_path": str(handle.log_path)}


class Rows:
    def __init__(self, status: str, metadata: dict):
        self.row = {"status": status, "metadata": metadata}
        self.cancelled: list[str] = []

    async def get(self, adw_id):
        return self.row

    async def mark_cancelled(self, adw_id, message):
        self.row["status"] = "cancelled"
        self.cancelled.append(message)


def test_cancel_stops_the_whole_process_group_and_marks_the_row(tmp_path):
    child_pid_file = tmp_path / "child.pid"
    adws = make_adws(tmp_path, sleepy=(
        "import subprocess, sys, time\nTOTAL_STEPS = 1\n"
        "child = subprocess.Popen(['sleep', '120'])\n"
        f"open({str(child_pid_file)!r}, 'w').write(str(child.pid))\n"
        "time.sleep(120)\n"
    ))
    handle = start_workflow(ADW_ID, "sleepy", adws)
    assert wait_for(lambda: child_pid_file.exists() and child_pid_file.read_text())
    grandchild = int(child_pid_file.read_text())

    rows = Rows("in_progress", handle.metadata())
    result = asyncio.run(cancel_adw(ADW_ID, rows, grace_seconds=5))
    os.waitpid(handle.pid, 0)

    assert result.cancelled
    assert rows.row["status"] == "cancelled"
    assert rows.cancelled == [f"Cancelled (stopped process group {handle.pid})"]
    assert wait_for(lambda: not alive(grandchild), timeout=5)


def test_cancel_leaves_a_finished_adw_alone():
    rows = Rows("completed", {"pid": 999999})
    result = asyncio.run(cancel_adw(ADW_ID, rows))
    assert (result.cancelled, result.message) == (False, "ADW already completed")
    assert rows.cancelled == []


def test_summarizer_has_no_tools_one_turn_and_no_bypass():
    options = summary_options()
    assert options.tools == [] and options.allowed_tools == []
    assert options.max_turns == 1
    assert options.permission_mode != "bypassPermissions"
