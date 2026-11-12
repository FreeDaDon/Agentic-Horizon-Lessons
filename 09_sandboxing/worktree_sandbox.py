#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
One git worktree per agent, a path-confinement hook, and a no-network container command.

A worktree gives each agent its own checkout and its own branch (`agent/<slug>`), so
concurrent agents never write the same files. The hook keeps an agent's file tools inside
that checkout. `docker_command` builds the argv to run untrusted commands against the
worktree with no network and a read-only root filesystem.

Usage:
  worktree_sandbox.py create <agent> [--repo .] [--base HEAD]   # prints the worktree path
  worktree_sandbox.py remove <agent> [--repo .] [--delete-branch]
  worktree_sandbox.py list [--repo .]
"""

from __future__ import annotations

import argparse
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SLUG = re.compile(r"[a-z0-9][a-z0-9-]{0,62}")
WORKTREE_DIR = ".worktrees"
BRANCH_PREFIX = "agent/"
OUTSIDE_ALLOWED = frozenset({"/dev/null", "/dev/stdin", "/dev/stdout", "/dev/stderr"})

PATH_KEYS = {
    "Read": "file_path",
    "Write": "file_path",
    "Edit": "file_path",
    "MultiEdit": "file_path",
    "NotebookEdit": "notebook_path",
    "Glob": "path",
    "Grep": "path",
}


@dataclass(frozen=True)
class Worktree:
    repo: Path
    slug: str
    branch: str
    path: Path


def validate_slug(agent_name: str) -> str:
    if not SLUG.fullmatch(agent_name):
        raise ValueError(f"agent name {agent_name!r} must match {SLUG.pattern} (lowercase, digits, hyphens)")
    return agent_name


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def repo_root(repo: Path | str) -> Path:
    return Path(git(Path(repo), "rev-parse", "--show-toplevel").strip()).resolve()


def checked_out_branches(repo: Path) -> dict[Path, str | None]:
    """Map each worktree path to its checked-out branch (None when detached)."""
    entries: dict[Path, str | None] = {}
    path: Path | None = None
    for line in git(repo, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            path = Path(line.removeprefix("worktree ")).resolve()
            entries[path] = None
        elif line.startswith("branch ") and path is not None:
            entries[path] = line.removeprefix("branch refs/heads/")
    return entries


def branch_exists(repo: Path, branch: str) -> bool:
    return subprocess.run(["git", "-C", str(repo), "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"]).returncode == 0


def exclude_worktree_dir(repo: Path) -> None:
    # Keeps .worktrees/ out of the main checkout's `git status` and `git add -A`
    # without touching a tracked .gitignore.
    exclude = Path(git(repo, "rev-parse", "--git-path", "info/exclude").strip())
    exclude = exclude if exclude.is_absolute() else repo / exclude
    exclude.parent.mkdir(parents=True, exist_ok=True)
    lines = exclude.read_text().splitlines() if exclude.exists() else []
    if f"/{WORKTREE_DIR}/" not in lines:
        exclude.write_text("\n".join([*lines, f"/{WORKTREE_DIR}/"]) + "\n")


def worktree_for(repo: Path | str, agent_name: str) -> Worktree:
    root = repo_root(repo)
    slug = validate_slug(agent_name)
    return Worktree(repo=root, slug=slug, branch=BRANCH_PREFIX + slug, path=root / WORKTREE_DIR / slug)


def create_worktree(repo: Path | str, agent_name: str, base: str = "HEAD") -> Worktree:
    """Create (or reuse) `<repo>/.worktrees/<slug>` on branch `agent/<slug>`."""
    wt = worktree_for(repo, agent_name)
    root = wt.repo
    exclude_worktree_dir(root)

    existing = checked_out_branches(root)
    if wt.path in existing:
        if existing[wt.path] != wt.branch:
            raise RuntimeError(f"{wt.path} is a worktree on {existing[wt.path]!r}, not {wt.branch!r}")
        return wt
    if wt.path.exists():
        raise RuntimeError(f"{wt.path} exists but is not a registered worktree; remove it first")

    if branch_exists(root, wt.branch):
        git(root, "worktree", "add", str(wt.path), wt.branch)
    else:
        git(root, "worktree", "add", "-b", wt.branch, str(wt.path), base)
    return wt


def remove_worktree(wt: Worktree, delete_branch: bool = False) -> None:
    """Remove the worktree. Git refuses if it has uncommitted changes, so agent work is never
    silently discarded. `delete_branch` uses `git branch -D`, which drops unmerged commits."""
    if wt.path in checked_out_branches(wt.repo):
        git(wt.repo, "worktree", "remove", str(wt.path))
    git(wt.repo, "worktree", "prune")
    if delete_branch and branch_exists(wt.repo, wt.branch):
        git(wt.repo, "branch", "-D", wt.branch)


def list_worktrees(repo: Path | str) -> list[Worktree]:
    root = repo_root(repo)
    found = []
    for path, branch in checked_out_branches(root).items():
        if path.parent == root / WORKTREE_DIR and branch == BRANCH_PREFIX + path.name:
            found.append(Worktree(repo=root, slug=path.name, branch=branch, path=path))
    return sorted(found, key=lambda wt: wt.slug)


def _deny(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def _bash_escapes(command: str, root: Path) -> str | None:
    """Return the first path-like token that resolves outside root.

    A heuristic. It resolves every token that looks like a path, so it catches `cd ..`,
    `cat /etc/passwd`, `> ~/x` and a symlink inside root that points out. It does not catch
    `$HOME`, `$(...)`, `eval`, or a script that opens paths itself. Pair it with a container
    (rung 4) when commands are untrusted.
    """
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return "an unparseable command"
    for i, token in enumerate(tokens):
        if token == "cd" and (i + 1 == len(tokens) or tokens[i + 1] in {";", "&&", "||", "|", "&"}):
            return "cd (home directory)"
        for candidate in (token, token.partition("=")[2]):
            if (candidate.startswith(("~", "..")) or "/" in candidate) and candidate not in OUTSIDE_ALLOWED:
                target = Path(os.path.expanduser(candidate))
                if not (root / target).resolve().is_relative_to(root):
                    return candidate
    return None


def confine_paths_hook(root: Path | str):
    """An SDK PreToolUse hook that denies file tools and Bash paths outside `root`.

    Wire it with `hooks={"PreToolUse": [HookMatcher(hooks=[confine_paths_hook(wt.path)])]}`.
    """
    root = Path(root).resolve()

    async def hook(input_data: dict[str, Any], tool_use_id: str | None, context: Any) -> dict[str, Any]:
        tool = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input") or {}
        if tool in PATH_KEYS:
            raw = tool_input.get(PATH_KEYS[tool])
            if raw and not (root / os.path.expanduser(raw)).resolve().is_relative_to(root):
                return _deny(f"{tool} is confined to {root}; {raw} resolves outside it")
        elif tool == "Bash":
            escape = _bash_escapes(tool_input.get("command", ""), root)
            if escape:
                return _deny(f"Bash is confined to {root}; {escape!r} points outside it")
        return {}

    return hook


def docker_command(worktree: Worktree | Path | str, image: str, cmd: list[str]) -> list[str]:
    """Build (not run) the argv for running `cmd` in `image` against the worktree.

    No network, read-only root filesystem, writable /tmp, the worktree mounted at /work,
    no Linux capabilities, and the host user's uid so files written to /work stay yours.
    """
    path = worktree.path if isinstance(worktree, Worktree) else Path(worktree).resolve()
    return [
        "docker", "run", "--rm",
        "--network", "none",
        "--read-only",
        "--tmpfs", "/tmp",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--user", f"{os.getuid()}:{os.getgid()}",
        "-v", f"{path}:/work",
        "-w", "/work",
        image, *cmd,
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="action", required=True)
    for action in ("create", "remove", "list"):
        p = sub.add_parser(action)
        p.add_argument("--repo", default=".")
        if action != "list":
            p.add_argument("agent")
        if action == "create":
            p.add_argument("--base", default="HEAD")
        if action == "remove":
            p.add_argument("--delete-branch", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.action == "create":
            print(create_worktree(args.repo, args.agent, args.base).path)
        elif args.action == "remove":
            remove_worktree(worktree_for(args.repo, args.agent), args.delete_branch)
        else:
            for wt in list_worktrees(args.repo):
                print(f"{wt.slug}\t{wt.branch}\t{wt.path}")
    except (ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
