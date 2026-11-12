"""Worktree-per-agent lifecycle in a throwaway git repo, the path-confinement hook, and the docker argv."""

import asyncio
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "worktree_sandbox", Path(__file__).parent.parent / "09_sandboxing/worktree_sandbox.py")
sandbox = importlib.util.module_from_spec(SPEC)
sys.modules["worktree_sandbox"] = sandbox
SPEC.loader.exec_module(sandbox)


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false", *args],
        check=True, capture_output=True, text=True).stdout


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    (root / "app.py").write_text("print('hi')\n")
    git(root, "add", "app.py")
    git(root, "commit", "-q", "-m", "init")
    return root.resolve()


def test_create_is_idempotent_and_remove_cleans_up(repo):
    wt = sandbox.create_worktree(repo, "builder-1")
    assert wt.path == repo / ".worktrees/builder-1"
    assert git(wt.path, "branch", "--show-current").strip() == "agent/builder-1"
    assert (wt.path / "app.py").read_text() == "print('hi')\n"
    assert git(repo, "status", "--porcelain") == "", "main checkout stays clean"

    assert sandbox.create_worktree(repo, "builder-1") == wt
    assert sandbox.list_worktrees(repo) == [wt]

    sandbox.remove_worktree(wt, delete_branch=True)
    assert not wt.path.exists()
    assert sandbox.list_worktrees(repo) == []
    assert git(repo, "branch", "--list", "agent/builder-1") == ""
    sandbox.remove_worktree(wt)


def test_gitignored_secrets_never_reach_the_worktree(repo):
    (repo / ".gitignore").write_text(".env\n")
    git(repo, "add", ".gitignore")
    git(repo, "commit", "-q", "-m", "ignore env")
    (repo / ".env").write_text("ANTHROPIC_API_KEY=secret\n")
    wt = sandbox.create_worktree(repo, "builder-2")
    assert (wt.path / ".gitignore").is_file()
    assert not (wt.path / ".env").exists(), "an agent confined to its worktree has no .env to read"


def test_recreate_reuses_existing_branch_and_its_commits(repo):
    wt = sandbox.create_worktree(repo, "scout")
    (wt.path / "notes.md").write_text("found it\n")
    git(wt.path, "add", "notes.md")
    git(wt.path, "commit", "-q", "-m", "scout notes")
    sandbox.remove_worktree(wt)

    again = sandbox.create_worktree(repo, "scout")
    assert (again.path / "notes.md").read_text() == "found it\n"


def test_remove_refuses_uncommitted_work(repo):
    wt = sandbox.create_worktree(repo, "dirty")
    (wt.path / "app.py").write_text("changed\n")
    with pytest.raises(RuntimeError):
        sandbox.remove_worktree(wt)
    assert (wt.path / "app.py").read_text() == "changed\n"


@pytest.mark.parametrize("name", ["Builder", "../escape", "a/b", "-rf", "", "a b", "x" * 64])
def test_rejects_unsafe_agent_names(repo, name):
    with pytest.raises(ValueError):
        sandbox.create_worktree(repo, name)
    assert not (repo / ".worktrees").exists() or not any((repo / ".worktrees").iterdir())


def decide(root: Path, tool: str, **tool_input) -> str:
    hook = sandbox.confine_paths_hook(root)
    out = asyncio.run(hook({"tool_name": tool, "tool_input": tool_input}, None, None))
    return out.get("hookSpecificOutput", {}).get("permissionDecision", "allow")


@pytest.fixture
def jail(tmp_path):
    root = tmp_path / "jail"
    (root / "src").mkdir(parents=True)
    outside = tmp_path / "secrets"
    outside.mkdir()
    (root / "src/link").symlink_to(outside)
    return root


@pytest.mark.parametrize("tool,key", [("Write", "file_path"), ("Edit", "file_path"), ("Read", "file_path"),
                                      ("MultiEdit", "file_path"), ("NotebookEdit", "notebook_path")])
def test_hook_confines_file_tools(jail, tool, key):
    assert decide(jail, tool, **{key: "../x"}) == "deny"
    assert decide(jail, tool, **{key: "src/../../x"}) == "deny"
    assert decide(jail, tool, **{key: "/etc/passwd"}) == "deny"
    assert decide(jail, tool, **{key: "src/link/key.pem"}) == "deny"
    assert decide(jail, tool, **{key: "src/deep/new.py"}) == "allow"
    assert decide(jail, tool, **{key: str(jail / "src/a.py")}) == "allow"


@pytest.mark.parametrize("command", [
    "cd .. && ls", "cd /", "cd", "cat /etc/passwd", "echo x > ~/x", "cp src/a.py ../a.py",
    "python -m x --out=/tmp/x", "ls src/link/", "echo 'unclosed",
])
def test_hook_denies_bash_escapes(jail, command):
    assert decide(jail, "Bash", command=command) == "deny"


@pytest.mark.parametrize("command", ["ls src", "cd src && pytest -q 2>/dev/null", "grep -r TODO .", "git status"])
def test_hook_allows_bash_inside_root(jail, command):
    assert decide(jail, "Bash", command=command) == "allow"


def test_docker_command_isolates_network_and_filesystem(tmp_path):
    argv = sandbox.docker_command(tmp_path, "python:3.12-slim", ["pytest", "-q"])
    pairs = list(zip(argv, argv[1:]))
    assert argv[:3] == ["docker", "run", "--rm"]
    assert ("--network", "none") in pairs
    assert "--read-only" in argv
    assert ("-v", f"{tmp_path.resolve()}:/work") in pairs
    assert ("--user", f"{os.getuid()}:{os.getgid()}") in pairs
    assert argv[-3:] == ["python:3.12-slim", "pytest", "-q"]
