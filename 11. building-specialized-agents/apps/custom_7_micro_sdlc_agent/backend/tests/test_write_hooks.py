"""
The planner, builder, and reviewer write hooks, captured from the real run_*_agent functions.

ClaudeSDKClient is replaced by a stub that records the options and stops before any
agent starts, so the hook under test is the exact closure the agent would get.
"""

import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import modules.agent_orchestrator as orch  # noqa: E402


class _Stop(Exception):
    pass


def capture_options(monkeypatch, kind: str, project: Path):
    captured = {}

    class FakeClient:
        def __init__(self, options):
            captured["options"] = options

        async def __aenter__(self):
            raise _Stop

        async def __aexit__(self, *exc):
            return False

    monkeypatch.setattr(orch, "ClaudeSDKClient", FakeClient)
    if kind == "planner":
        asyncio.run(orch.run_planner_agent("x", codebase_path=str(project)))
    elif kind == "builder":
        asyncio.run(orch.run_builder_agent("specs/p.md", codebase_path=str(project)))
    else:
        asyncio.run(orch.run_reviewer_agent("specs/p.md", "t", codebase_path=str(project)))
    return captured["options"]


def capture_hook(monkeypatch, kind: str, project: Path):
    return capture_options(monkeypatch, kind, project).hooks["PreToolUse"][0].hooks[0]


def decision(hook, file_path: str, tool: str = "Write") -> str:
    field = "notebook_path" if tool == "NotebookEdit" else "file_path"
    out = asyncio.run(hook({"tool_name": tool, "tool_input": {field: file_path}}, None, None))
    return out.get("hookSpecificOutput", {}).get("permissionDecision", "allow")


WRITE_TOOLS = ["Write", "Edit", "MultiEdit", "NotebookEdit"]


@pytest.fixture
def project(tmp_path):
    root = (tmp_path / "proj").resolve()
    root.mkdir()
    return root


@pytest.mark.parametrize("tool", WRITE_TOOLS)
@pytest.mark.parametrize("kind,directory", [("planner", "specs"), ("reviewer", "reviews")])
def test_writes_inside_the_directory_are_allowed(monkeypatch, project, kind, directory, tool):
    hook = capture_hook(monkeypatch, kind, project)
    assert decision(hook, f"{project}/{directory}/out.md", tool) == "allow"
    assert decision(hook, f"{directory}/out.md", tool) == "allow"
    assert decision(hook, f"{directory}/nested/out.md", tool) == "allow"


@pytest.mark.parametrize("tool", WRITE_TOOLS)
@pytest.mark.parametrize("kind,directory", [("planner", "specs"), ("reviewer", "reviews")])
@pytest.mark.parametrize("template", [
    "{project}/main.py",
    "{project}/{directory}_evil/x.md",
    "{project}/{directory}/../main.py",
    "{directory}/../main.py",
    "/etc/{directory}/cron.d/job",
    "{directory}heet.py",
    "/home/u/.bashrc_{directory}",
])
def test_writes_outside_the_directory_are_denied(monkeypatch, project, kind, directory, template, tool):
    hook = capture_hook(monkeypatch, kind, project)
    assert decision(hook, template.format(project=project, directory=directory), tool) == "deny"


def test_symlink_out_of_the_directory_is_denied(monkeypatch, project, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (project / "specs").mkdir()
    (project / "specs" / "link").symlink_to(outside)
    hook = capture_hook(monkeypatch, "planner", project)
    assert decision(hook, f"{project}/specs/link/x.md") == "deny"


def test_other_tools_are_not_affected(monkeypatch, project):
    hook = capture_hook(monkeypatch, "planner", project)
    out = asyncio.run(hook({"tool_name": "Read", "tool_input": {"file_path": "/etc/passwd"}}, None, None))
    assert out == {}


def test_builder_does_not_bypass_permissions(monkeypatch, project):
    assert capture_options(monkeypatch, "builder", project).permission_mode == "acceptEdits"


@pytest.mark.parametrize("tool", WRITE_TOOLS)
def test_builder_may_write_anywhere_inside_the_codebase(monkeypatch, project, tool):
    hook = capture_hook(monkeypatch, "builder", project)
    assert decision(hook, f"{project}/backend/main.py", tool) == "allow"
    assert decision(hook, "frontend/src/App.vue", tool) == "allow"
    assert decision(hook, "specs/../README.md", tool) == "allow"


@pytest.mark.parametrize("tool", WRITE_TOOLS)
@pytest.mark.parametrize("template", [
    "../outside.py",
    "backend/../../outside.py",
    "{project}/../outside.py",
    "{project}_evil/x.py",
    "/etc/cron.d/job",
    "~/.bashrc",
])
def test_builder_writes_outside_the_codebase_are_denied(monkeypatch, project, template, tool):
    hook = capture_hook(monkeypatch, "builder", project)
    assert decision(hook, template.format(project=project), tool) == "deny"


@pytest.mark.parametrize("tool", WRITE_TOOLS)
def test_builder_symlink_out_of_the_codebase_is_denied(monkeypatch, project, tmp_path, tool):
    outside = tmp_path / "outside"
    outside.mkdir()
    (project / "link").symlink_to(outside)
    hook = capture_hook(monkeypatch, "builder", project)
    assert decision(hook, "link/x.py", tool) == "deny"
    assert decision(hook, f"{project}/link/x.py", tool) == "deny"

