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
