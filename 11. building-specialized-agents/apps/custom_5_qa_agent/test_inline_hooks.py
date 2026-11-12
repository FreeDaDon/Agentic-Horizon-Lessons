#!/usr/bin/env python3
"""
The QA agent's inline security hooks, called the way the SDK calls them.

Runs under pytest or directly: uv run python test_inline_hooks.py
"""

import asyncio
import tempfile
from pathlib import Path

import qa_agent
from qa_agent import HookContext, block_bash_writes, block_env_files, log_tool_usage


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


ENV_BLOCKED = [
    ("Read", {"file_path": "/path/to/.env"}),
    ("Read", {"file_path": "config/.env.production"}),
    ("Read", {"file_path": "~/.env"}),
    ("Bash", {"command": "cat .env"}),
    ("Bash", {"command": "grep KEY ../.env"}),
    ("Bash", {"command": "cat .e*"}),
    ("Bash", {"command": 'cat .en""v'}),
    ("Bash", {"command": "cat .en''v"}),
    ("Bash", {"command": "cat .e\\nv"}),
    ("Bash", {"command": "cat .en?"}),
    ("Bash", {"command": "cat .[e]nv"}),
    ("Bash", {"command": "cat .{e,x}nv"}),
    ("Bash", {"command": "head -n 5 ./.env.local"}),
    ("Bash", {"command": "ls; cat $(echo .env)"}),
    ("Grep", {"pattern": "KEY", "path": ".env"}),
    ("Grep", {"pattern": "KEY", "path": ".", "glob": "*.env*"}),
]

ENV_ALLOWED = [
    ("Read", {"file_path": "/path/to/normal.py"}),
    ("Read", {"file_path": ".env.sample"}),
    ("Read", {"file_path": "src/environment.py"}),
    ("Bash", {"command": "cat .env.sample"}),
    ("Bash", {"command": "ls -la"}),
    ("Bash", {"command": "cat *"}),
    ("Bash", {"command": "git log --oneline -5"}),
    ("Grep", {"pattern": "def ", "path": "src"}),
    ("Glob", {"pattern": "**/*.py"}),
]

WRITES_BLOCKED = [
    "echo x > notes.txt",
    "echo x >> notes.txt",
    "ls &> listing.txt",
    "ls 2>&1 > out.log",
    "echo x | tee notes.txt",
    "sed -i s/a/b/ file.py",
    "sed -Ei s/a/b/ file.py",
    "sed --in-place s/a/b/ file.py",
    "rm notes.txt",
    "r''m notes.txt",
    "mv a.py b.py",
    "cp a.py b.py",
    "chmod +x run.sh",
    "sudo rm -rf build",
    "ls && touch marker",
    "find . -name '*.pyc' -delete",
    "find . -exec rm {} +",
    "xargs rm < files.txt",
    'bash -c "rm notes.txt"',
]

WRITES_ALLOWED = [
    "ls -la",
    "cat README.md",
    "grep -rn TODO src 2>/dev/null",
    "git log --oneline -5 2>&1",
    "sed -n 1,20p file.py",
    "find . -name '*.py'",
    "wc -l qa_agent.py > /dev/null",
    "head -n 3 a.txt | sort | uniq -c",
]


def test_env_access_is_blocked_for_every_file_reading_tool():
    for tool_name, tool_input in ENV_BLOCKED:
        assert denied(call(block_env_files, tool_name, tool_input)), (tool_name, tool_input)


def test_env_templates_and_normal_access_are_allowed():
    for tool_name, tool_input in ENV_ALLOWED:
        assert call(block_env_files, tool_name, tool_input) == {}, (tool_name, tool_input)


def test_a_symlink_to_an_env_file_is_blocked():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / ".env").write_text("KEY=x")
        (Path(tmp) / "notes.txt").symlink_to(Path(tmp) / ".env")
        assert denied(call(block_env_files, "Read", {"file_path": f"{tmp}/notes.txt"}))


def test_bash_cannot_change_files():
    for command in WRITES_BLOCKED:
        assert denied(call(block_bash_writes, "Bash", {"command": command})), command


def test_read_only_bash_is_allowed():
    for command in WRITES_ALLOWED:
        assert call(block_bash_writes, "Bash", {"command": command}) == {}, command


def test_write_hook_ignores_other_tools():
    assert call(block_bash_writes, "Read", {"file_path": "notes.txt"}) == {}


def test_the_agent_registers_both_guards_for_bash(monkeypatch):
    captured = {}

    class FakeClient:
        def __init__(self, options):
            captured["options"] = options

        async def connect(self):
            pass

    monkeypatch.setattr(qa_agent, "ClaudeSDKClient", FakeClient)
    agent = qa_agent.QAAgentREPL()
    asyncio.run(agent.initialize_client())

    pre_tool_use = captured["options"].hooks["PreToolUse"]
    bash_hooks = [h for m in pre_tool_use if m.matcher is None or "Bash" in m.matcher.split("|") for h in m.hooks]
    read_hooks = [h for m in pre_tool_use if m.matcher is None or "Read" in m.matcher.split("|") for h in m.hooks]
    assert block_env_files in bash_hooks and block_bash_writes in bash_hooks
    assert block_env_files in read_hooks


def test_logging_hook_never_blocks():
    assert call(log_tool_usage, "Read", {"file_path": "/path/to/file.txt"}) == {}


if __name__ == "__main__":
    for name, test in list(globals().items()):
        if name.startswith("test_") and "monkeypatch" not in test.__code__.co_varnames:
            test()
            print(f"PASS {name}")
    print("All tests completed!")
