"""
Offline tests for the psql command lines the orchestrator_db scripts build.
Nothing here runs psql or needs a database.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from drop_table import AVAILABLE_TABLES, drop_table_sql  # noqa: E402
from psql_cli import psql_invocation  # noqa: E402

URL = "postgresql://orch:s3cr%40t@db.example.com:5432/orchestrator?sslmode=require"


def test_password_goes_to_pgpassword_not_argv():
    argv, env = psql_invocation(URL, "-f", "1_agents.sql")

    assert env["PGPASSWORD"] == "s3cr@t"
    assert not any("s3cr" in arg for arg in argv)
    assert "postgresql://orch@db.example.com:5432/orchestrator?sslmode=require" in argv


def test_psql_stops_on_the_first_error():
    argv, _ = psql_invocation(URL, "-f", "1_agents.sql")

    assert argv[:3] == ["psql", "-v", "ON_ERROR_STOP=1"]
    assert argv[-2:] == ["-f", "1_agents.sql"]


def test_url_without_password_is_passed_through(monkeypatch):
    monkeypatch.delenv("PGPASSWORD", raising=False)
    argv, env = psql_invocation("postgresql://localhost/orchestrator", "-c", "SELECT 1")

    assert "postgresql://localhost/orchestrator" in argv
    assert "PGPASSWORD" not in env


def test_known_tables_get_a_drop_statement():
    for table in AVAILABLE_TABLES:
        assert drop_table_sql(table) == f"DROP TABLE IF EXISTS {table} CASCADE;"


@pytest.mark.parametrize("name", ["agents; DROP SCHEMA public", "pg_catalog.pg_user", ""])
def test_unknown_table_names_never_reach_sql(name):
    with pytest.raises(ValueError):
        drop_table_sql(name)

