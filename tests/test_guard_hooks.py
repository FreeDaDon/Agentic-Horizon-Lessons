"""
The PreToolUse guard hooks, run as subprocesses the way Claude Code runs them.

Exit code 2 blocks the tool call; any other exit code lets it run.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
L11_BLOCKER = ROOT / "11. building-specialized-agents/.claude/hooks/dangerous_command_blocker.py"


def run_hook(hook: Path, payload: str, cwd: Path) -> int:
    proc = subprocess.run(
        [sys.executable, str(hook)], input=payload, text=True, capture_output=True,
        cwd=cwd, env={"CLAUDE_PROJECT_DIR": str(cwd), "PATH": "/usr/bin:/bin"}, timeout=30,
    )
    return proc.returncode


def bash(command: str) -> str:
    return json.dumps({"session_id": "test", "tool_name": "Bash", "tool_input": {"command": command}})


@pytest.mark.parametrize("command", [
    "rm -rf /",
    "rm -fR /",
    "rm -r -f /etc",
    "rm --recursive --force /",
    # Uppercase -R split from -f used to slip past the fallback checks
    "rm -R -f /",
    "rm -R -f ~",
    "rm -f -R ~",
    "rm -R -f $HOME",
])
def test_l11_blocker_blocks_recursive_rm_on_critical_paths(command, tmp_path):
    assert run_hook(L11_BLOCKER, bash(command), tmp_path) == 2


@pytest.mark.parametrize("command", [
    "ls -la",
    "git status",
    "rm notes.txt",
    "rm -r build",
    "rm -R build",
    "echo hello > out.txt",
    "python -m pytest -q",
])
def test_l11_blocker_allows_ordinary_commands(command, tmp_path):
    assert run_hook(L11_BLOCKER, bash(command), tmp_path) == 0


PRE_TOOL_USE = [
    ROOT / lesson / ".claude/hooks/pre_tool_use.py"
    for lesson in ("12. multi-agent-orchestration", "13. agent-experts", "14.orchestrator-agent-with-adws-singularity")
]
ALL_GUARDS = [L11_BLOCKER, *PRE_TOOL_USE]
GUARD_IDS = [h.parts[-4] for h in ALL_GUARDS]


@pytest.mark.parametrize("hook", ALL_GUARDS, ids=GUARD_IDS)
@pytest.mark.parametrize("payload", [
    '{"tool_name": "Bash", "tool_input": {"command": "rm -rf /"',  # truncated
    "not json",
    "",
])
def test_guards_block_when_they_cannot_check_the_call(hook, payload, tmp_path):
    assert run_hook(hook, payload, tmp_path) == 2


@pytest.mark.parametrize("hook", PRE_TOOL_USE, ids=GUARD_IDS[1:])
@pytest.mark.parametrize("command", ["rm -rf /", "rm -R -f ~", "rm -r -f /etc", "rm --recursive --force /"])
def test_pre_tool_use_blocks_recursive_rm(hook, command, tmp_path):
    assert run_hook(hook, bash(command), tmp_path) == 2


@pytest.mark.parametrize("hook", PRE_TOOL_USE, ids=GUARD_IDS[1:])
@pytest.mark.parametrize("payload", [
    bash("ls -la"),
    bash("git status"),
    json.dumps({"tool_name": "Read", "tool_input": {"file_path": "README.md"}}),
])
def test_pre_tool_use_allows_ordinary_calls_and_logs_them(hook, payload, tmp_path):
    assert run_hook(hook, payload, tmp_path) == 0
    assert json.loads((tmp_path / "logs" / "pre_tool_use.json").read_text())[-1] == json.loads(payload)


@pytest.mark.parametrize("hook", PRE_TOOL_USE, ids=GUARD_IDS[1:])
def test_pre_tool_use_logging_failure_never_blocks(hook, tmp_path):
    (tmp_path / "logs").write_text("a file where the log directory should be")
    assert run_hook(hook, bash("ls -la"), tmp_path) == 0
    assert run_hook(hook, bash("rm -rf /"), tmp_path) == 2
