#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""
Self-grading checks for the pillar labs. Each lab names the artifact you build and the
properties it must have; this script verifies them offline, with no model and no key.

Usage: labs/check_lab.py <lab-number> <path>
Exit status 0 when every check passes, 1 otherwise. Each failing check prints a reason.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import re
import sys
from collections.abc import Callable, Iterator
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
Check = Iterator[tuple[bool, str]]
ALIASES = {"opus", "sonnet", "haiku"}
READ_ONLY_TOOLS = {"Read", "Glob", "Grep"}


def frontmatter(text: str) -> tuple[dict, str]:
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not match:
        return {}, text
    meta = {}
    for line in match[1].splitlines():
        key, sep, value = line.partition(":")
        if sep and not line.startswith((" ", "\t")):
            meta[key.strip()] = value.strip()
    return meta, match[2]


def sections(body: str) -> set[str]:
    return {m.strip().lower() for m in re.findall(r"^#{1,3}\s+(.+)$", body, re.M)}


def lab1_context(project: Path) -> Check:
    claude_md = project / "CLAUDE.md"
    yield claude_md.is_file(), "CLAUDE.md exists"
    if claude_md.is_file():
        tokens = len(claude_md.read_text(encoding="utf-8")) // 4
        yield tokens <= 1500, f"CLAUDE.md is about {tokens} tokens (limit 1500): keep only universals"
    yield not (project / ".mcp.json").exists(), "no default .mcp.json (keep per-task .mcp.json.<server>_<N>k files)"
    primes = sorted((project / ".claude/commands").glob("prime*.md"))
    yield bool(primes), "at least one .claude/commands/prime*.md"
    for prime in primes:
        found = sections(frontmatter(prime.read_text(encoding="utf-8"))[1])
        missing = {"run", "read", "report"} - found
        yield not missing, f"{prime.name} has Run, Read and Report sections (missing: {sorted(missing) or 'none'})"
    styles = [json.loads(p.read_text()).get("outputStyle") for p in (project / ".claude").glob("settings*.json")]
    yield any(styles), "a .claude/settings*.json selects an outputStyle for build agents"


def lab2_prompt(command: Path) -> Check:
    meta, body = frontmatter(command.read_text(encoding="utf-8"))
    yield bool(meta.get("description")), "frontmatter has a description"
    yield bool(meta.get("argument-hint")), "frontmatter has an argument-hint"
    found = sections(body)
    for name in ("variables", "workflow", "report"):
        yield name in found, f"has a ## {name.title()} section"
    yield bool(re.search(r"^[A-Z][A-Z0-9_]+:\s*\$(?:\d|ARGUMENTS)", body, re.M)), \
        "a dynamic variable such as `USER_PROMPT: $1`"
    yield bool(re.search(r"^\s*1\.\s", body, re.M)), "the workflow has numbered steps"
    yield "STOP" in body, "an early-return condition written with STOP"
    loops = re.findall(r"<([a-z][\w-]*-loop)>", body)
    yield any(f"</{tag}>" in body for tag in loops), "a <name-loop> ... </name-loop> block"


def _options_call(tree: ast.AST) -> ast.Call | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", "")) == "ClaudeAgentOptions":
            return node
    return None


def _literal(node: ast.AST):
    try:
        return ast.literal_eval(node)
    except ValueError:
        return None


def lab3_sdk_agent(agent: Path) -> Check:
    source = agent.read_text(encoding="utf-8")
    tree = ast.parse(source)
    call = _options_call(tree)
    yield call is not None, "builds ClaudeAgentOptions(...)"
    if call is None:
        return
    kwargs = {k.arg: k.value for k in call.keywords}
    yield "system_prompt" in kwargs, "sets system_prompt"
    allowed = _literal(kwargs["allowed_tools"]) if "allowed_tools" in kwargs else None
    yield bool(allowed) and all(t.startswith("mcp__") for t in allowed), \
        "allowed_tools lists only your custom mcp__<server>__<tool> tools"
    denied = set(_literal(kwargs["disallowed_tools"]) or []) if "disallowed_tools" in kwargs else set()
    yield {"Bash", "Write", "Edit"} <= denied, "disallowed_tools denies at least Bash, Write and Edit"
    yield isinstance(_literal(kwargs.get("max_turns", ast.Constant(None))), int), "max_turns is a literal int"
    yield "bypassPermissions" not in source, "never uses bypassPermissions"
    submit_tools = [
        d.args[0].value for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        for d in n.decorator_list
        if isinstance(d, ast.Call) and getattr(d.func, "id", "") == "tool" and d.args
        and isinstance(d.args[0], ast.Constant) and str(d.args[0].value).startswith("submit_")
    ]
    yield bool(submit_tools), "returns its result through a @tool(\"submit_<thing>\", ...) tool"


def lab4_fleet_template(template: Path) -> Check:
    meta, body = frontmatter(template.read_text(encoding="utf-8"))
    yield meta.get("name") == template.stem, "frontmatter name matches the file name"
    yield len(str(meta.get("description", ""))) >= 40, "description says what the agent does and when to use it"
    tools = {t.strip() for t in str(meta.get("tools", "")).split(",") if t.strip()}
    yield bool(tools) and tools <= READ_ONLY_TOOLS, f"tools are read-only (allowed: {sorted(READ_ONLY_TOOLS)}, got: {sorted(tools)})"
    yield meta.get("model") in ALIASES, "model is an alias: opus, sonnet or haiku"
    found = sections(body)
    for name in ("purpose", "workflow"):
        yield name in found, f"has a ## {name.title()} section"
    yield any(s.startswith("report") for s in found), "has a ## Report section"


def lab5_expertise(expertise: Path) -> Check:
    text = expertise.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        yield False, f"parses as YAML ({exc})"
        return
    yield isinstance(data, dict), "is a YAML mapping"
    yield len(text.splitlines()) <= 1000, "stays within MAX_LINES (1000)"
    for key in ("overview", "core_implementation"):
        yield isinstance(data, dict) and key in data, f"has a top-level `{key}`"
    yield "file:" in text, "pins at least one `file:` path"
    spec = importlib.util.spec_from_file_location("check_expertise", ROOT / "08_expertise_drift/check_expertise.py")
    checker = importlib.util.module_from_spec(spec)
    sys.modules["check_expertise"] = checker
    spec.loader.exec_module(checker)
    findings = checker.check_file(expertise, 15, 0.15)
    yield not findings, "drift check is clean" + "".join(f"\n      {f.kind}: {f.where}: {f.detail}" for f in findings)


ADW_STEPS = ROOT / "14.orchestrator-agent-with-adws-singularity/adws/adw_modules/adw_steps.py"


def lab6_adw(workflow: Path) -> Check:
    source = workflow.read_text(encoding="utf-8")
    header = re.search(r"^# /// script\n(.*?)^# ///$", source, re.S | re.M)
    block = re.search(r"dependencies\s*=\s*\[(.*?)\]", header[1], re.S) if header else None
    deps = re.findall(r'"([^"]+)"', block[1]) if block else []
    yield bool(deps), "has a PEP 723 header listing its dependencies"
    yield bool(deps) and all("==" in d for d in deps), f"every dependency is pinned with == (got {deps})"
    tree = ast.parse(source)
    available = {n.name for n in ast.parse(ADW_STEPS.read_text(encoding="utf-8")).body
                 if isinstance(n, ast.AsyncFunctionDef) and not n.name.startswith("_")
                 and [a.arg for a in n.args.args] == ["run"]}
    imported = {a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)
                and n.module == "adw_modules.adw_steps" for a in n.names}
    assigned = {t.id: n.value for n in tree.body if isinstance(n, ast.Assign) for t in n.targets
                if isinstance(t, ast.Name)}
    steps = [e.id for e in getattr(assigned.get("STEPS"), "elts", []) if isinstance(e, ast.Name)]
    yield bool(steps), "defines STEPS as a list of step functions"
    yield bool(steps) and set(steps) <= available & imported, \
        f"every step is imported from adw_modules.adw_steps (known steps: {sorted(available)})"
    yield "plan" in steps and "build" in steps and steps.index("plan") < steps.index("build"), "plans before it builds"
    yield bool(steps) and "review" in steps[-1], "ends on a review gate, so a failing review fails the ADW"
    total = _literal(assigned["TOTAL_STEPS"]) if "TOTAL_STEPS" in assigned else None
    yield isinstance(total, int) and total >= len(steps), "TOTAL_STEPS is a literal covering every step"
    yield "run_cli(STEPS, TOTAL_STEPS)" in source and '__name__ == "__main__"' in source, \
        "hands STEPS to run_cli under if __name__ == \"__main__\""
    yield "subprocess" not in imported and "subprocess" not in source, \
        "chains agents through adw_steps, not ad hoc subprocess calls"


LABS: dict[int, Callable[[Path], Check]] = {
    1: lab1_context, 2: lab2_prompt, 3: lab3_sdk_agent, 4: lab4_fleet_template, 5: lab5_expertise,
    6: lab6_adw,
}


def grade(lab: int, path: Path) -> list[tuple[bool, str]]:
    return list(LABS[lab](path))


def main(argv: list[str]) -> int:
    if len(argv) != 2 or not argv[0].isdigit() or int(argv[0]) not in LABS:
        print(__doc__.strip().splitlines()[-2])
        print(f"labs: {sorted(LABS)}")
        return 2
    results = grade(int(argv[0]), Path(argv[1]))
    for ok, message in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {message}")
    passed = sum(ok for ok, _ in results)
    print(f"lab {argv[0]}: {passed}/{len(results)} checks passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
