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


def test_run_migrations_runs_each_file_with_stop_on_error_and_no_password_in_argv(tmp_path, monkeypatch):
    import subprocess

    import run_migrations

    script_dir = tmp_path / "apps" / "orchestrator_db"
    (script_dir / "migrations").mkdir(parents=True)
    for name in run_migrations.MIGRATIONS:
        (script_dir / "migrations" / name).write_text("SELECT 1;")
    (tmp_path / ".env").write_text(f"DATABASE_URL={URL}\n")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(run_migrations, "__file__", str(script_dir / "run_migrations.py"))

    calls = []

    def recording_run(argv, **kwargs):
        calls.append((argv, kwargs.get("env") or {}))
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(run_migrations.subprocess, "run", recording_run)

    run_migrations.main()

    migration_calls = [(argv, env) for argv, env in calls if "-f" in argv]
    assert len(migration_calls) == len(run_migrations.MIGRATIONS)
    for argv, env in migration_calls:
        assert argv[:3] == ["psql", "-v", "ON_ERROR_STOP=1"]
        assert not any("s3cr" in arg for arg in argv)
        assert env["PGPASSWORD"] == "s3cr@t"
