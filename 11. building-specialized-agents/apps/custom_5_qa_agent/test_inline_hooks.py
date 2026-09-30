#!/usr/bin/env python3
"""
Test script to verify inline hooks functionality

Runs under pytest or directly: uv run python test_inline_hooks.py
"""

import asyncio
import re
from pathlib import Path

from qa_agent import block_env_files, log_tool_usage, HookContext


def call(hook, tool_name, tool_input):
    return asyncio.run(
        hook(
            input_data={"tool_name": tool_name, "tool_input": tool_input},
            tool_use_id="test-id",
            context=HookContext(),
        )
    )


def denied(result):
    return result.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"


BLOCKED = [
    ("Read", {"file_path": "/path/to/.env"}),
    ("Read", {"file_path": ".env.sample"}),
    ("Bash", {"command": "cat .env"}),
    ("Bash", {"command": "grep KEY ../.env"}),
    ("Grep", {"pattern": "KEY", "path": ".env"}),
    ("Grep", {"pattern": "KEY", "path": ".", "glob": "*.env*"}),
]

ALLOWED = [
    ("Read", {"file_path": "/path/to/normal.py"}),
    ("Bash", {"command": "ls -la"}),
    ("Bash", {"command": "git log --oneline -5"}),
    ("Grep", {"pattern": "def ", "path": "src"}),
    ("Glob", {"pattern": "**/*.py"}),
]


def test_env_access_is_blocked_for_every_file_reading_tool():
    for tool_name, tool_input in BLOCKED:
        assert denied(call(block_env_files, tool_name, tool_input)), (tool_name, tool_input)


def test_normal_access_is_allowed():
    for tool_name, tool_input in ALLOWED:
        assert call(block_env_files, tool_name, tool_input) == {}, (tool_name, tool_input)


def test_hook_is_registered_for_read_grep_and_bash():
    source = Path(__file__).with_name("qa_agent.py").read_text()
    match = re.search(r'HookMatcher\(matcher="([^"]*)", hooks=\[block_env_files\]\)', source)
    assert match and set(match.group(1).split("|")) == {"Read", "Grep", "Bash"}


def test_logging_hook_never_blocks():
    assert call(log_tool_usage, "Read", {"file_path": "/path/to/file.txt"}) == {}


if __name__ == "__main__":
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            test()
            print(f"PASS {name}")
    print("All tests completed!")
