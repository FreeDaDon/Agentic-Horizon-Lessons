#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
Dangerous Command Blocker - Claude Code Hook
Prevents execution of dangerous commands like rm -rf /, force pushes and disk wipes.

The command is normalized (quotes and backslashes dropped) and split into simple
commands with shlex, so each rule sees the argv a shell would run.
"""

import json
import os
import re
import shlex
import sys
from datetime import datetime
from pathlib import Path
from typing import NamedTuple


HOME_DIR = os.path.expanduser("~")

# Removing any of these (or everything under them) wrecks the machine or the user's files.
ROOT_TARGETS = {
    "/", "~", "$HOME", "${HOME}", HOME_DIR,
    "/bin", "/boot", "/dev", "/etc", "/home", "/lib", "/lib64", "/opt", "/proc",
    "/root", "/sbin", "/srv", "/sys", "/usr", "/var",
    "/Applications", "/Library", "/System", "/Users",
}
# Recursive rm of these wipes the whole working directory (or its parent).
WORKDIR_TARGETS = {".", "..", "*", ".*"}

SHELLS = {"sh", "bash", "zsh", "dash", "ksh", "fish"}
FETCHERS = {"curl", "wget", "fetch"}
SQL_CLIENTS = {"psql", "mysql", "mariadb", "sqlite3", "sqlcmd"}
# Words that run the command after them, possibly with their own options first.
WRAPPERS = {
    "!", "{", "then", "do", "else", "elif", "if", "while", "until", "time", "exec",
    "command", "builtin", "nohup", "sudo", "doas", "env", "nice", "ionice", "xargs",
    "timeout", "stdbuf", "eval",
}
WRAPPER_OPTIONS_WITH_VALUES = {"-u", "-g", "-n", "-C", "-D", "-h", "-p", "-U", "-I", "-L", "-P", "-s", "-k"}
PUNCTUATION = set("();<>|&")


class Segment(NamedTuple):
    """One simple command: the operator that introduced it and its words."""

    op: str
    argv: list


def normalize(command: str) -> str:
    """Drop quotes and backslashes so r""m, r\\m and 'rm' all read as rm."""
    command = command.replace("\\\n", " ").replace("`", " ; ")
    return re.sub(r"[\"'\\]", "", command).replace("\n", " ; ")


def segments(command: str) -> list:
    lexer = shlex.shlex(normalize(command), posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    result, op, argv = [], "", []
    tokens = list(lexer)
    for i, token in enumerate(tokens):
        if token == "$" and i + 1 < len(tokens) and tokens[i + 1].startswith("("):
            continue
        if set(token) <= PUNCTUATION and not (">" in token or token in ("<", "<<", "<<<")):
            result.append(Segment(op, argv))
            op = "$(" if i and tokens[i - 1] == "$" else token
            argv = []
        else:
            argv.append(token)
    result.append(Segment(op, argv))
    return [s for s in result if s.argv]


def command_words(argv: list) -> list:
    """The words of the command a segment actually runs, past assignments and wrappers."""
    i = 0
    while i < len(argv):
        word = argv[i]
        if re.match(r"^[A-Za-z_]\w*=", word):
            i += 1
        elif word in WRAPPERS:
            i += 1
            while i < len(argv) and (argv[i].startswith("-") or re.match(r"^\d+(\.\d+)?[smhd]?$", argv[i])):
                i += 2 if argv[i] in WRAPPER_OPTIONS_WITH_VALUES else 1
        else:
            break
    words = argv[i:]
    if words and name(words[0]) in SHELLS:
        for j, word in enumerate(words[1:], 1):
            if re.match(r"^-[a-z]*c$", word) and j + 1 < len(words):
                return command_words(words[j + 1:])
    return words


def name(word: str) -> str:
    return os.path.basename(word)


def target(word: str) -> str:
    """/etc/ and /etc/* name /etc; ./ names ."""
    return re.sub(r"(/+\*?|/\.)+$", "", word) or "/"


def short_flags(args: list) -> str:
    return "".join(a[1:] for a in args if a.startswith("-") and not a.startswith("--"))


def rm_reason(args: list):
    if "--no-preserve-root" in args:
        return "rm --no-preserve-root"
    recursive = "--recursive" in args or set(short_flags(args)) & {"r", "R"}
    hit = [a for a in args if not a.startswith("-") and target(a) in ROOT_TARGETS | WORKDIR_TARGETS]
    if recursive and hit:
        return f"recursive rm of {hit[0]}"


def find_reason(args: list):
    deletes = "-delete" in args or any(
        a in ("-exec", "-execdir", "-ok", "-okdir") and i + 1 < len(args)
        and name(args[i + 1]) in ("rm", "shred", "unlink", "rmdir")
        for i, a in enumerate(args)
    )
    hit = [a for a in args if target(a) in ROOT_TARGETS]
    if deletes and hit:
        return f"find deleting under {hit[0]}"


def git_reason(args: list):
    i = 0
    while i < len(args) and args[i].startswith("-"):
        i += 2 if args[i] in ("-C", "-c", "--git-dir", "--work-tree", "--namespace") else 1
    if i >= len(args):
        return None
    sub, rest = args[i], args[i + 1:]
    flags = short_flags(rest)
    if sub == "clean":
        forced = "--force" in rest or "f" in flags
        dry_run = "--dry-run" in rest or "n" in flags
        if forced and not dry_run:
            return "git clean -f deletes untracked files"
    if sub == "push":
        if (
            "f" in flags
            or any(a.startswith(("--force", "--mirror")) for a in rest)
            or any(a.startswith("+") for a in rest)
        ):
            return "force push rewrites remote history"


def dd_reason(args: list):
    harmless = ("of=/dev/null", "of=/dev/zero", "of=/dev/stdout", "of=/dev/stderr")
    if any(a.startswith("of=/dev/") and a not in harmless for a in args):
        return "dd onto a device"


def chmod_reason(args: list):
    recursive = "--recursive" in args or "R" in short_flags(args)
    hit = [a for a in args if not a.startswith("-") and target(a) in ROOT_TARGETS]
    if recursive and hit:
        return f"recursive permission change on {hit[0]}"


def terraform_reason(args: list):
    positional = [a for a in args if not a.startswith("-")]
    if positional[:1] == ["destroy"] or (positional[:1] == ["apply"] and "-destroy" in args):
        return "terraform destroy"


RULES = {
    "rm": rm_reason,
    "find": find_reason,
    "git": git_reason,
    "dd": dd_reason,
    "chmod": chmod_reason,
    "chown": chmod_reason,
    "chgrp": chmod_reason,
    "terraform": terraform_reason,
    "tofu": terraform_reason,
}


def rmtree_reason(text: str):
    for match in re.finditer(r"rmtree\s*\(\s*([^,)]*)", text):
        argument = match.group(1).strip()
        if target(argument) in ROOT_TARGETS or re.search(r"expanduser|home\(|environ|getenv", argument):
            return f"shutil.rmtree({argument})"


def dangerous_command_reason(command: str):
    """Why a Bash command must not run, or None when it may."""
    parsed = segments(command)
    text = normalize(command)
    previous, fetch_in_pipeline = "", False
    for segment in parsed:
        words = command_words(segment.argv)
        command_name = name(words[0]) if words else ""
        args = words[1:]
        if segment.op not in ("|", "|&"):
            fetch_in_pipeline = False
        if command_name in RULES:
            reason = RULES[command_name](args)
            if reason:
                return reason
        if command_name.startswith("mkfs") or command_name in ("mke2fs", "wipefs"):
            return f"{command_name} formats a disk"
        if command_name == "dropdb" or (
            command_name in SQL_CLIENTS and re.search(r"\bdrop\s+(database|table|schema)\b", text, re.I)
        ):
            return "SQL DROP"
        if re.match(r"^python[\d.]*$", command_name):
            reason = rmtree_reason(text)
            if reason:
                return reason
        if command_name in SHELLS and fetch_in_pipeline:
            return "piping a download into a shell"
        if command_name in FETCHERS and segment.op in ("<(", "$(") and previous in SHELLS | {"source", "."}:
            return "running a download in a shell"
        fetch_in_pipeline = fetch_in_pipeline or command_name in FETCHERS
        previous = command_name
    return None


def suggest_safer_alternative(command: str) -> str:
    """Suggest a safer alternative to the dangerous command."""
    suggestions = []

    if 'rm -rf' in command or 'rm -fr' in command:
        suggestions.append("• Use 'rm -r' without -f for important deletions (allows prompting)")
        suggestions.append("• Specify exact paths instead of using wildcards")
        suggestions.append("• Consider using 'trash' command to move to trash instead")

    if '*' in command:
        suggestions.append("• List files first with 'ls' before using wildcards")
        suggestions.append("• Use specific file patterns instead of broad wildcards")

    return "\n".join(suggestions) if suggestions else "Consider a more specific, safer command"


def log_blocked_command(session_id: str, command: str, reason: str):
    """Log blocked commands for security audit."""
    try:
        project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
        log_dir = Path(project_dir) / "agents" / "security_logs" / session_id
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / "blocked_commands.jsonl"
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "reason": reason,
            "action": "blocked"
        }

        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception:
        # Silently fail logging - don't let it affect the blocking
        pass


def main():
    try:
        input_data = json.load(sys.stdin)

        if input_data.get("tool_name") != "Bash":
            sys.exit(0)

        command = input_data.get("tool_input", {}).get("command", "")
        if not command:
            sys.exit(0)

        reason = dangerous_command_reason(command)

        if reason:
            session_id = input_data.get("session_id", "unknown")
            log_blocked_command(session_id, command, reason)

            error_message = f"""BLOCKED: Dangerous command detected!

Command: {command}
Reason: {reason}

This command could cause irreversible data loss or system damage.

Safer alternatives:
{suggest_safer_alternative(command)}

Please reconsider your approach and use a safer command."""

            print(error_message, file=sys.stderr)
            sys.exit(2)  # Block execution and show stderr to Claude

        sys.exit(0)

    except Exception as e:
        # Fail closed: exit 1 would let the command run unchecked
        print(f"BLOCKED: dangerous command check could not run ({type(e).__name__}: {e})", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
