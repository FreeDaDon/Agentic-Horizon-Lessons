"""Every INSERT in the orchestrator and ADW code names columns that the migrations create.

The offline suites fake the database, so a column that exists only in the code passes them.
The manual ADW trigger inserted `orchestrator_agents.name` and `.model`, which no migration
ever created; the first live run against Postgres failed on it. This test catches that class
of bug without a database.
"""

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
LESSONS = ("12. multi-agent-orchestration", "13. agent-experts", "14.orchestrator-agent-with-adws-singularity")
CREATE = re.compile(r"CREATE TABLE IF NOT EXISTS (\w+)\s*\((.*?)\n\);", re.S | re.I)
ADD_COLUMN = re.compile(r"ALTER TABLE (\w+)\s+ADD COLUMN(?: IF NOT EXISTS)? (\w+)", re.I)
INSERT = re.compile(r"INSERT INTO (\w+)\s*\(([^)]*)\)", re.I)
NOT_COLUMNS = {"PRIMARY", "UNIQUE", "CONSTRAINT", "FOREIGN", "CHECK"}


def schema(lesson: str) -> dict[str, set[str]]:
    tables: dict[str, set[str]] = {}
    for sql in sorted((ROOT / lesson / "apps/orchestrator_db/migrations").glob("*.sql")):
        text = re.sub(r"--[^\n]*", "", sql.read_text(encoding="utf-8"))
        for table, body in CREATE.findall(text):
            cols = {line.split()[0].strip('"') for line in body.splitlines() if line.strip()}
            tables.setdefault(table.lower(), set()).update(c for c in cols if c.upper() not in NOT_COLUMNS)
        for table, column in ADD_COLUMN.findall(text):
            tables.setdefault(table.lower(), set()).add(column)
    return tables


def inserts(lesson: str):
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "*.py"],
                         cwd=ROOT / lesson, capture_output=True, text=True, check=True).stdout
    for rel in out.splitlines():
        if "/tests/" in rel or "adw_tests/" in rel:
            continue
        text = (ROOT / lesson / rel).read_text(encoding="utf-8", errors="replace")
        for table, columns in INSERT.findall(text):
            yield rel, table.lower(), [c.strip().strip('"') for c in columns.split(",") if c.strip()]


@pytest.mark.parametrize("lesson", LESSONS)
def test_inserted_columns_exist_in_the_migrations(lesson):
    tables = schema(lesson)
    assert "agents" in tables and "orchestrator_agents" in tables, "migration parsing found the core tables"
    problems = [
        f"{rel}: {table}.{column}"
        for rel, table, columns in inserts(lesson) if table in tables
        for column in columns if column not in tables[table]
    ]
    assert problems == [], "INSERT names columns no migration creates:\n" + "\n".join(problems)
