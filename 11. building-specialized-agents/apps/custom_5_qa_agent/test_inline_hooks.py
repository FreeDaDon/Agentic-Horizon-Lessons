#!/usr/bin/env python3
"""
The QA agent's inline security hooks, called the way the SDK calls them.

Runs under pytest or directly: uv run python test_inline_hooks.py
"""

import asyncio
import tempfile
from pathlib import Path

import qa_agent
from qa_agent import HookContext, block_env_files, enforce_read_only_bash, log_tool_usage


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
    "grep -n TODO qa_agent.py 2>/dev/null",
    "git log --oneline -5 2>&1",
    "git diff HEAD~1 --stat",
    "find . -name '*.py'",
    "wc -l qa_agent.py > /dev/null",
    "head -n 3 a.txt | sort | cut -c1-5",
    "rg TODO .",
]

# Bypasses a denylist cannot close: variable indirection, ANSI-C quoting, interpreters,
# command substitution, recursive reads that sweep in .env.
ENV_ESCAPES_BLOCKED = [
    "f=.e; cat ${f}nv",
    "cat $'\\x2eenv'",
    "cat $(ls -a | grep env)",
    "cat `ls -a | grep env`",
    'python -c "print(open(chr(46)+\'env\').read())"',
    "node -e 'require(\"fs\").readFileSync(\".env\")'",
    "awk '{print}' .en''v",
    "sed -n p README.md",
    "grep -r SECRET .",
    "grep -Rn KEY .",
    "rg --hidden SECRET",
    "rg -uu SECRET",
    "git config --list",
    "sort -o out.txt a.txt",
    "while read l; do echo $l; done < .env",
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
        assert denied(call(enforce_read_only_bash, "Bash", {"command": command})), command


def test_read_only_bash_is_allowed():
    for command in WRITES_ALLOWED:
        assert call(enforce_read_only_bash, "Bash", {"command": command}) == {}, command


def test_bash_cannot_reach_env_files_through_indirection():
    for command in ENV_ESCAPES_BLOCKED:
        assert denied(call(enforce_read_only_bash, "Bash", {"command": command})), command


def test_bash_argument_symlinked_to_an_env_file_is_blocked(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / ".env").write_text("KEY=x")
        (Path(tmp) / "config.txt").symlink_to(Path(tmp) / ".env")
        monkeypatch.chdir(tmp)
        assert denied(call(enforce_read_only_bash, "Bash", {"command": "cat config.txt"}))
        assert call(enforce_read_only_bash, "Bash", {"command": "ls"}) == {}


def test_write_hook_ignores_other_tools():
    assert call(enforce_read_only_bash, "Read", {"file_path": "notes.txt"}) == {}


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
    assert block_env_files in bash_hooks and enforce_read_only_bash in bash_hooks
    assert block_env_files in read_hooks


def test_logging_hook_never_blocks():
    assert call(log_tool_usage, "Read", {"file_path": "/path/to/file.txt"}) == {}


if __name__ == "__main__":
    for name, test in list(globals().items()):
        if name.startswith("test_") and "monkeypatch" not in test.__code__.co_varnames:
            test()
            print(f"PASS {name}")
    print("All tests completed!")
