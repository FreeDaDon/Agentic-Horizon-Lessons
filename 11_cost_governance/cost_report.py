#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Print the spend dashboard (dashboard.sql) as markdown tables.

Runs each `-- name:` section through `psql` against DATABASE_URL, read-only.

Usage:
  DATABASE_URL=postgres://... cost_report.py                # every section
  DATABASE_URL=postgres://... cost_report.py top_adws daily_spend
  cost_report.py --list                                     # section names, no database
"""

from __future__ import annotations

import argparse
import csv
import io
import os
import re
import subprocess
import sys
from pathlib import Path

DASHBOARD = Path(__file__).with_name("dashboard.sql")
SECTION = re.compile(r"^-- name: (\w+)\s*$", re.MULTILINE)


def parse_sections(text: str) -> dict[str, str]:
    """Map each `-- name: x` header to the SQL that follows it, up to the next header."""
    parts = SECTION.split(text)
    return {name: body.strip() for name, body in zip(parts[1::2], parts[2::2])}


def to_markdown(rows: list[list[str]]) -> str:
    """Render CSV rows (header first) as a markdown table."""
    if not rows:
        return "_no columns_"
    header, body = rows[0], rows[1:]

    def line(cells: list[str]) -> str:
        return "| " + " | ".join(cell.replace("|", "\\|") for cell in cells) + " |"

    table = [line(header), "|" + "---|" * len(header), *map(line, body)]
    return "\n".join(table) if body else "\n".join([*table, "", "_no rows_"])


def run_psql(database_url: str, sql: str) -> list[list[str]]:
    proc = subprocess.run(
        ["psql", database_url, "--csv", "--no-psqlrc", "-v", "ON_ERROR_STOP=1",
         "-c", "SET default_transaction_read_only = on", "-c", sql],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip())
    # psql prints the SET command tag before the query's CSV.
    output = proc.stdout.split("\n", 1)[1] if proc.stdout.startswith("SET") else proc.stdout
    return list(csv.reader(io.StringIO(output)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print dashboard.sql sections as markdown tables.")
    parser.add_argument("sections", nargs="*", help="section names (default: all)")
    parser.add_argument("--list", action="store_true", help="print section names and exit")
    parser.add_argument("--sql", type=Path, default=DASHBOARD)
    args = parser.parse_args(argv)

    sections = parse_sections(args.sql.read_text())
    if args.list:
        print("\n".join(sections))
        return 0
    unknown = [name for name in args.sections if name not in sections]
    if unknown:
        parser.error(f"unknown sections {unknown}; choose from {list(sections)}")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        parser.error("DATABASE_URL is not set")

    for name in args.sections or sections:
        try:
            rows = run_psql(database_url, sections[name])
        except (RuntimeError, FileNotFoundError) as exc:
            print(f"error in section {name}: {exc}", file=sys.stderr)
            return 1
        print(f"## {name}\n\n{to_markdown(rows)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
