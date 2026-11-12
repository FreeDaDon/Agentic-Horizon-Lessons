# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
ADW Runner - Discover, start and cancel AI Developer Workflow processes.

Stdlib only, so the orchestrator backend and the manual trigger can both import it.
The adws directory is resolved from this file's location, never from a caller's
working directory, so every caller sees the same workflows.

Each workflow runs as `uv run adws/adw_workflows/adw_<type>.py --adw-id <id>` in its
own process group, with stdout and stderr appended to agents/adw/<adw_id>/run.log
under the project root. Callers store RunHandle.metadata() in the ADW row's
metadata; cancel_adw reads the pid back from there.

Usage:
    from adw_triggers.adw_scripts import discover_workflows, start_workflow, cancel_adw

    handle = start_workflow(adw_id, "plan_build")
    result = await cancel_adw(adw_id, rows)
"""

from __future__ import annotations

import ast
import asyncio
import os
import signal
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

ADWS_DIR = Path(__file__).resolve().parent.parent
TERMINAL_STATUSES = frozenset({"completed", "failed", "cancelled"})


@dataclass(frozen=True)
class WorkflowInfo:
    workflow_type: str
    path: Path
    total_steps: int
    description: str


def discover_workflows(adws_dir: Path = ADWS_DIR) -> dict[str, WorkflowInfo]:
    """Workflow files adw_workflows/adw_<type>.py that declare a literal TOTAL_STEPS.

    Read with ast rather than imported: workflow modules pull in the SDK and the DB.
    """
    workflows: dict[str, WorkflowInfo] = {}
    for path in sorted((adws_dir / "adw_workflows").glob("adw_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), str(path))
        total_steps = next(
            (
                node.value.value
                for node in tree.body
                if isinstance(node, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "TOTAL_STEPS" for t in node.targets)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, int)
            ),
            None,
        )
        if total_steps is None:
            continue
        workflow_type = path.stem.removeprefix("adw_")
        doc = (ast.get_docstring(tree) or "").strip().splitlines()
        workflows[workflow_type] = WorkflowInfo(
            workflow_type=workflow_type,
            path=path,
            total_steps=total_steps,
            description=doc[0] if doc else f"ADW workflow: {workflow_type.replace('_', ' ')}",
        )
    return workflows


class UnknownWorkflowError(ValueError):
    pass


def require_workflow(workflow_type: str, adws_dir: Path = ADWS_DIR) -> WorkflowInfo:
    workflows = discover_workflows(adws_dir)
    if workflow_type not in workflows:
        available = ", ".join(workflows) or "none"
        raise UnknownWorkflowError(f"Unknown workflow type {workflow_type!r}. Available: {available}")
    return workflows[workflow_type]


@dataclass(frozen=True)
class RunHandle:
    pid: int
    log_path: Path

    def metadata(self) -> dict[str, Any]:
        """What callers merge into ai_developer_workflows.metadata."""
        return {"pid": self.pid, "log_path": str(self.log_path)}


def run_log_path(adw_id: str, adws_dir: Path = ADWS_DIR) -> Path:
    return adws_dir.parent / "agents" / "adw" / adw_id / "run.log"


def start_workflow(adw_id: str, workflow_type: str, adws_dir: Path = ADWS_DIR) -> RunHandle:
    """Spawn the workflow in its own process group. Raises UnknownWorkflowError or
    ValueError (adw_id not a UUID) before spawning anything."""
    if str(uuid.UUID(adw_id)) != adw_id:
        raise ValueError(f"adw_id must be a canonical UUID string: {adw_id!r}")
    info = require_workflow(workflow_type, adws_dir)
    log_path = run_log_path(adw_id, adws_dir)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "ab") as log:
        process = subprocess.Popen(
            ["uv", "run", str(info.path), "--adw-id", adw_id],
            cwd=str(adws_dir.parent),
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    return RunHandle(pid=process.pid, log_path=log_path)


def stop_process_group(pid: int, grace_seconds: float = 5.0) -> bool:
    """SIGTERM the group led by pid, SIGKILL whatever is left after the grace period.
    Returns False if the group was already gone."""
    try:
        os.killpg(pid, signal.SIGTERM)
    except ProcessLookupError:
        return False
    deadline = time.monotonic() + grace_seconds
    while time.monotonic() < deadline:
        try:
            os.killpg(pid, 0)
        except ProcessLookupError:
            return True
        time.sleep(0.1)
    try:
        os.killpg(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    return True


class AdwRows(Protocol):
    """The two ADW-row operations cancel_adw needs, over whatever DB layer the caller has."""

    async def get(self, adw_id: str) -> dict[str, Any] | None:
        """Return the row's status and metadata, or None if there is no such ADW."""
        ...

    async def mark_cancelled(self, adw_id: str, message: str) -> None: ...


@dataclass(frozen=True)
class CancelResult:
    cancelled: bool
    message: str


async def cancel_adw(adw_id: str, rows: AdwRows, grace_seconds: float = 5.0) -> CancelResult:
    """Stop a running ADW's process group (pid from the row's metadata) and mark it cancelled."""
    row = await rows.get(adw_id)
    if row is None:
        return CancelResult(False, f"ADW not found: {adw_id}")
    status = row.get("status")
    if status in TERMINAL_STATUSES:
        return CancelResult(False, f"ADW already {status}")

    pid = (row.get("metadata") or {}).get("pid")
    if pid is None:
        stopped = "no process recorded"
    elif await asyncio.to_thread(stop_process_group, int(pid), grace_seconds):
        stopped = f"stopped process group {pid}"
    else:
        stopped = f"process group {pid} had already exited"
    await rows.mark_cancelled(adw_id, f"Cancelled ({stopped})")
    return CancelResult(True, f"Cancelled ADW {adw_id}: {stopped}")


__all__ = [
    "ADWS_DIR",
    "AdwRows",
    "CancelResult",
    "RunHandle",
    "UnknownWorkflowError",
    "WorkflowInfo",
    "cancel_adw",
    "discover_workflows",
    "require_workflow",
    "run_log_path",
    "start_workflow",
    "stop_process_group",
]
