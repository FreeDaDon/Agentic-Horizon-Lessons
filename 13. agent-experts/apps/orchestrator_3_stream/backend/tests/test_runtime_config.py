"""
Offline tests for settings read from the environment and for the compaction
token reset.

The database tests swap asyncpg's pool for a recorder (the external
boundary) and check what the real database module sends to it.
"""

import os
import subprocess
import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from modules import config, database  # noqa: E402


def settings_with_env(**env):
    code = "from modules import config; print(config.FAST_MODEL, config.DATABASE_POOL_SIZE)"
    out = subprocess.run(
        [sys.executable, "-c", code], cwd=BACKEND_DIR, env={**os.environ, **env},
        capture_output=True, text=True, check=True,
    )
    return out.stdout.split()


def test_fast_model_and_pool_size_come_from_the_environment():
    assert settings_with_env(FAST_MODEL="sonnet", DATABASE_POOL_SIZE="7") == ["sonnet", "7"]


class RecordingConnection:
    def __init__(self):
        self.statements = []

    async def execute(self, sql, *args):
        self.statements.append(" ".join(sql.split()))


class RecordingPool:
    def __init__(self):
        self.conn = RecordingConnection()

    @asynccontextmanager
    async def acquire(self):
        yield self.conn


@pytest.fixture
def pool(monkeypatch):
    recording = RecordingPool()
    monkeypatch.setattr(database, "_pool", recording)
    return recording


@pytest.mark.asyncio
async def test_compaction_resets_tokens_but_keeps_cost(pool):
    await database.reset_agent_tokens(uuid.uuid4())

    (statement,) = pool.conn.statements
    assert "input_tokens = 0" in statement
    assert "output_tokens = 0" in statement
    assert "total_cost" not in statement


@pytest.mark.asyncio
async def test_pool_size_setting_caps_the_pool(monkeypatch):
    created = {}

    async def create_pool(url, **kwargs):
        created.update(kwargs)
        return object()

    monkeypatch.setattr(database, "_pool", None)
    monkeypatch.setattr(database.asyncpg, "create_pool", create_pool)
    monkeypatch.setattr(config, "DATABASE_POOL_SIZE", 3)

    await database.init_pool("postgresql://localhost/test")

    assert created["max_size"] == 3
    assert created["min_size"] <= 3
