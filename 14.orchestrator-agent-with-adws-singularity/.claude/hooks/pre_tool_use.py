#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

import json
import os
import re
import shlex
import sys
from fnmatch import fnmatchcase
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


def is_env_file_name(base: str) -> bool:
    return base == ".env" or (base.startswith(".env.") and base != ".env.sample")


def brace_expansions(word: str) -> list:
    match = re.search(r"\{([^{}]*,[^{}]*)\}", word)
    if not match:
        return [word]
    head, tail = word[: match.start()], word[match.end():]
    return [x for part in match.group(1).split(",") for x in brace_expansions(head + part + tail)]


def could_name_env_file(word: str, shell_glob: bool = False) -> bool:
    """True for .env, .env.local, and globs or brace forms like .e*, .en?, .{e,x}nv that reach them.

    A shell glob only matches a dotfile when the pattern itself starts with a dot, so `cat *`
    is fine; other globs (Grep's) can match dotfiles from a leading `*`.
    """
    for candidate in brace_expansions(word):
        base = re.split(r"[/=:]", candidate.rstrip("/"))[-1]
        if is_env_file_name(base):
            return True
        if shell_glob and not base.startswith("."):
            continue
        if any(c in base for c in "*?[") and any(fnmatchcase(f, base) for f in (".env", ".env.local")):
            return True
    return False


def is_env_file_access(tool_name: str, tool_input: dict) -> bool:
    if tool_name in ("Read", "Edit", "MultiEdit", "Write", "NotebookEdit"):
        path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
        return bool(path) and (
            could_name_env_file(path) or is_env_file_name(os.path.basename(os.path.realpath(path)))
        )
    if tool_name == "Grep":
        return any(could_name_env_file(tool_input.get(k) or "") for k in ("path", "glob"))
    if tool_name == "Bash":
        return any(could_name_env_file(w, shell_glob=True) for s in segments(tool_input.get("command", "")) for w in s.argv)
    return False


def main():
    try:
        input_data = json.load(sys.stdin)

        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})

        if is_env_file_access(tool_name, tool_input):
            print("BLOCKED: Access to .env files containing sensitive data is prohibited", file=sys.stderr)
            print("Use .env.sample for template files instead", file=sys.stderr)
            sys.exit(2)  # Exit code 2 blocks tool call and shows error to Claude

        if tool_name == "Bash":
            reason = dangerous_command_reason(tool_input.get("command", ""))
            if reason:
                print(f"BLOCKED: Dangerous command detected and prevented ({reason})", file=sys.stderr)
                sys.exit(2)

    except Exception as e:
        # Fail closed: a guard that cannot read or check the call must not let it run
        print(f"BLOCKED: pre_tool_use check could not run ({type(e).__name__})", file=sys.stderr)
        sys.exit(2)

    try:
        # Ensure log directory exists
        log_dir = Path.cwd() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "pre_tool_use.json"

        # Read existing log data or initialize empty list
        if log_path.exists():
            with open(log_path, "r") as f:
                try:
                    log_data = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    log_data = []
        else:
            log_data = []

        # Append new data
        log_data.append(input_data)

        # Write back to file with formatting
        with open(log_path, "w") as f:
            json.dump(log_data, f, indent=2)

    except Exception:
        # Logging is best effort; it never blocks a tool call
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
