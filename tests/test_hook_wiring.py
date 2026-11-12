"""
Run each lesson's hook commands exactly as Claude Code does: the command string from
.claude/settings.json through `sh -c`, with CLAUDE_PROJECT_DIR pointing at a copy of the
lesson whose path contains a space (every lesson folder name has one).

test_guard_hooks.py proves the hook logic. This file proves the wiring: a hook that
cannot start exits 126/127, which Claude Code treats as a non-blocking error, so the
tool call it was meant to guard runs unchecked.
"""

import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
LESSONS = sorted(p.parent.parent for p in ROOT.glob("*/.claude/settings.json"))
GUARDED = {"11. building-specialized-agents", "12. multi-agent-orchestration",
           "13. agent-experts", "14.orchestrator-agent-with-adws-singularity"}


def hook_commands(lesson: Path):
    settings = json.loads((lesson / ".claude/settings.json").read_text())
    for event, matchers in settings.get("hooks", {}).items():
        for matcher in matchers:
            for hook in matcher["hooks"]:
                yield event, matcher.get("matcher", "*"), hook["command"]


@pytest.fixture(scope="module", params=LESSONS, ids=lambda p: p.name)
def spaced_lesson(request, tmp_path_factory):
    project = tmp_path_factory.mktemp("wiring") / f"copy of {request.param.name}"
    shutil.copytree(request.param / ".claude", project / ".claude",
                    ignore=shutil.ignore_patterns("__pycache__"))
    return request.param, project


def run(command: str, project: Path, payload: dict) -> subprocess.CompletedProcess:
    env = {"CLAUDE_PROJECT_DIR": str(project), "PATH": os.environ["PATH"],
           "HOME": os.environ.get("HOME", str(project))}
    return subprocess.run(["sh", "-c", command], input=json.dumps(payload), text=True,
                          capture_output=True, cwd=project, env=env, timeout=120)


def test_every_hook_script_exists_at_its_expanded_path(spaced_lesson):
    _, project = spaced_lesson
    for event, _, command in hook_commands(spaced_lesson[0]):
        argv = shlex.split(command.replace("$CLAUDE_PROJECT_DIR", str(project)))
        scripts = [a for a in argv if a.endswith(".py")]
        assert scripts, f"{event}: no script in {command!r}"
        assert Path(scripts[0]).is_file(), f"{event}: {scripts[0]} does not exist"


def test_pre_tool_use_hooks_start_and_guards_block(spaced_lesson):
    lesson, project = spaced_lesson
    payload = {"session_id": "wiring-test", "hook_event_name": "PreToolUse",
               "tool_name": "Bash", "tool_input": {"command": "rm -rf /"}}
    codes = []
    for event, matcher, command in hook_commands(lesson):
        if event != "PreToolUse" or matcher not in ("*", "", "Bash") and "Bash" not in matcher:
            continue
        proc = run(command, project, payload)
        assert proc.returncode not in (126, 127), f"{command!r} did not start: {proc.stderr}"
        codes.append(proc.returncode)
    if lesson.name in GUARDED:
        assert 2 in codes, f"no PreToolUse hook blocked a recursive rm of / (exit codes {codes})"
