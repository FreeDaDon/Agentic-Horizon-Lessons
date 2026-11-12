#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""
Deterministic drift check for agent expertise files.

An expertise.yaml claims facts about the code: a file exists, it has N lines, a function
lives at lines a-b. Self-improve prompts repair those claims with a model; this script
detects when they have gone stale, with no model and no key, so CI can catch drift the
day the code moves.

Checks, per expertise file:
  missing-file   a `file:` path (or a path-like string) resolves to nothing
  missing-symbol a key with `lines: "a-b"` under a `file:` names a def/class not in that file
  moved-symbol   that def/class exists but starts outside a-b (beyond --tolerance lines)
  line-count     `lines: <int>` next to `file:` is off by more than --count-tolerance

Usage:
  check_expertise.py [--tolerance 15] [--count-tolerance 0.15] [--json] [--fix] [PATH ...]
With no PATH, checks every tracked */expertise.yaml under .claude/commands/experts/, except the
deliberately broken lab starters.
Exit status: 0 clean, 1 drift found, 2 unreadable or invalid YAML.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import yaml

PATH_RE = re.compile(r"^[\w./-]+\.(?:py|ts|vue|sql|md|yaml|json|sh)$")
RANGE_RE = re.compile(r"^\s*(\d+)\s*-\s*(\d+)")
IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class Finding:
    expertise: str
    kind: str
    where: str
    detail: str
    fix: str | None = None


def project_roots(expertise: Path) -> list[Path]:
    """Directories a relative path in this expertise file may be relative to: the project
    that owns the .claude/ folder, the lesson root above it, and each app under apps/."""
    roots: list[Path] = []
    for parent in expertise.parents:
        if (parent / ".claude").is_dir() and parent not in roots:
            roots.append(parent)
        if parent.name[:1].isdigit() or (parent / ".git").exists():
            break
    for root in list(roots):
        roots += sorted(p for p in (root / "apps").glob("*") if p.is_dir() and p not in roots)
    return roots


def resolve(path: str, roots: list[Path]) -> Path | None:
    for root in roots:
        if (root / path).is_file():
            return root / path
    if "/" not in path:
        matches = {m for root in roots for m in root.rglob(path)
                   if m.is_file() and not {"node_modules", ".venv"} & set(m.parts)}
        if matches:
            return sorted(matches)[0]
    return None


def definition_lines(source: str, name: str) -> list[int]:
    pattern = re.compile(
        rf"^\s*(?:export\s+)?(?:async\s+def|def|class|interface|type|enum|(?:async\s+)?function|const|let)\s+{re.escape(name)}\b"
    )
    return [i for i, line in enumerate(source.splitlines(), 1) if pattern.search(line)]


def check_file(expertise: Path, tolerance: int, count_tolerance: float) -> list[Finding]:
    rel = str(expertise)
    try:
        data = yaml.safe_load(expertise.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise SystemExit(f"{rel}: cannot parse: {exc}") from exc
    roots = project_roots(expertise.resolve())
    findings: list[Finding] = []
    seen_missing: set[str] = set()

    def missing(path: str, where: str) -> None:
        if path not in seen_missing:
            seen_missing.add(path)
            findings.append(Finding(rel, "missing-file", where, path))

    def walk(node, where: str, current_file: Path | None) -> None:
        if isinstance(node, dict):
            file_value = node.get("file")
            if isinstance(file_value, str):
                resolved = resolve(file_value, roots)
                if resolved is None:
                    missing(file_value, where)
                current_file = resolved
                total = node.get("lines")
                if resolved and isinstance(total, int):
                    actual = len(resolved.read_text(encoding="utf-8", errors="replace").splitlines())
                    if abs(actual - total) > max(5, count_tolerance * actual):
                        findings.append(Finding(rel, "line-count", f"{where}.lines",
                                                f"{file_value}: claims {total} lines, has {actual}",
                                                fix=str(actual)))
            for key, value in node.items():
                child = f"{where}.{key}" if where else str(key)
                if (isinstance(value, dict) and current_file is not None and IDENT_RE.match(str(key))
                        and isinstance(value.get("lines"), str) and "file" not in value):
                    span = RANGE_RE.match(value["lines"])
                    if span:
                        check_symbol(str(key), int(span[1]), int(span[2]), current_file, child)
                walk(value, child, current_file)
        elif isinstance(node, list):
            for i, item in enumerate(node):
                walk(item, f"{where}[{i}]", current_file)
        elif isinstance(node, str) and PATH_RE.match(node) and "/" in node:
            if resolve(node, roots) is None:
                missing(node, where)

    def check_symbol(name: str, start: int, end: int, file: Path, where: str) -> None:
        lines = definition_lines(file.read_text(encoding="utf-8", errors="replace"), name)
        if not lines:
            findings.append(Finding(rel, "missing-symbol", where, f"{name} not defined in {file.name}"))
        elif not any(start - tolerance <= n <= end + tolerance for n in lines):
            fix = f'"{lines[0]}-{lines[0] + end - start}"' if len(lines) == 1 else None
            findings.append(Finding(rel, "moved-symbol", f"{where}.lines",
                                    f"{name} claimed at {start}-{end} in {file.name}, defined at {lines}",
                                    fix=fix))

    walk(data, "", None)
    return findings


KEY_RE = re.compile(r"^(\s*)([\w-]+):(\s*)(.*)$")


def apply_fixes(expertise: Path, findings: list[Finding]) -> int:
    """Rewrite the `lines:` values named by fixable findings, keeping every other byte."""
    wanted = {f.where: f.fix for f in findings if f.fix is not None}
    if not wanted:
        return 0
    out, stack, applied = [], [], 0
    for line in expertise.read_text(encoding="utf-8").splitlines(keepends=True):
        match = KEY_RE.match(line)
        if match:
            indent = len(match[1])
            while stack and stack[-1][0] >= indent:
                stack.pop()
            stack.append((indent, match[2]))
            path = ".".join(key for _, key in stack)
            if path in wanted and match[4].strip():
                comment = re.search(r"\s+#.*$", match[4])
                line = f"{match[1]}{match[2]}:{match[3]}{wanted.pop(path)}{comment[0] if comment else ''}\n"
                applied += 1
        out.append(line)
    expertise.write_text("".join(out), encoding="utf-8")
    return applied


def tracked_expertise_files() -> list[Path]:
    out = subprocess.run(["git", "ls-files", "*/.claude/commands/experts/*/expertise.yaml"],
                         capture_output=True, text=True, check=True).stdout
    return [Path(p) for p in out.splitlines() if not p.startswith("labs/starters/")]  # starters drift on purpose


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--tolerance", type=int, default=15)
    parser.add_argument("--count-tolerance", type=float, default=0.15)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fix", action="store_true",
                        help="rewrite stale line counts and single-definition line ranges in place")
    args = parser.parse_args(argv)

    files = args.paths or tracked_expertise_files()
    findings = [f for path in files for f in check_file(path, args.tolerance, args.count_tolerance)]
    if args.fix:
        fixed = sum(apply_fixes(path, [f for f in findings if f.expertise == str(path)]) for path in files)
        findings = [f for path in files for f in check_file(path, args.tolerance, args.count_tolerance)]
        print(f"fixed {fixed} line references")
    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        for f in findings:
            print(f"{f.expertise}: {f.kind}: {f.where}: {f.detail}")
        print(f"{len(files)} expertise files checked, {len(findings)} drift findings")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
