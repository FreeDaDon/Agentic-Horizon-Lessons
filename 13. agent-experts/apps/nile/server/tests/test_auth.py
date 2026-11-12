"""Offline tests for Nile's session-token auth.

`src.main` cannot be imported without ANTHROPIC_API_KEY (it builds the agent at import
time), so these tests mount the real routers on a minimal app the same way main.py
does, plus a WebSocket endpoint that guards itself exactly like `/ws/home/{user_id}`.
Nothing is faked. Each test gets its own SQLite file under pytest's tmp_path, and
`get_db` is pointed at it, so sessions are stored and checked in a real database.

Run: cd apps/nile/server && uv run pytest tests/test_auth.py
"""
import asyncio
import hashlib
import sqlite3

import pytest
from fastapi import Depends, FastAPI, WebSocket
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from starlette.websockets import WebSocketDisconnect

from src.config import API_PREFIX
from src.database import Base, get_db
from src.routers import (
    auth_router,
    cart_router,
    expertise_router,
    home_router,
    orders_router,
    products_router,
)
from src.sessions import (
    WS_CLOSE_FORBIDDEN,
    WS_CLOSE_UNAUTHORIZED,
    authorize_websocket,
    current_user_id,
    path_user_id,
)

ROUTERS = (auth_router, products_router, cart_router, orders_router, expertise_router, home_router)

PUBLIC_ROUTES = {
    f"{API_PREFIX}/auth/login",
    f"{API_PREFIX}/products",
    f"{API_PREFIX}/products/search",
    f"{API_PREFIX}/products/categories",
    f"{API_PREFIX}/products/brands",
    f"{API_PREFIX}/products/{{product_id}}",
    f"{API_PREFIX}/products/by-ids/{{product_ids}}",
}


def build_app(db_url: str) -> FastAPI:
    """A fresh app process stand-in: its own engine, no state shared with other builds."""
    engine = create_async_engine(db_url, poolclass=NullPool)
    sessions = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def tmp_db():
        async with sessions() as session:
            yield session

    app = FastAPI()
    for router in ROUTERS:
        app.include_router(router, prefix=API_PREFIX)
    app.dependency_overrides[get_db] = tmp_db

    @app.get("/probe/me")
    async def probe_me(user_id: int = Depends(current_user_id)):
        return {"user_id": user_id}

    @app.get("/probe/users/{user_id}")
    async def probe_user(user_id: int = Depends(path_user_id)):
        return {"user_id": user_id}

    @app.websocket("/probe/ws/{user_id}")
    async def probe_ws(websocket: WebSocket, user_id: int, db: AsyncSession = Depends(get_db)):
        if not await authorize_websocket(websocket, user_id, db):
            return
        await websocket.accept()
        await websocket.send_json({"user_id": user_id})
        await websocket.close()

    return app


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "nile.db"

    async def create_tables():
        engine = create_async_engine(f"sqlite+aiosqlite:///{path}", poolclass=NullPool)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

    asyncio.run(create_tables())
    return path


@pytest.fixture
def client(db_path):
    return TestClient(build_app(f"sqlite+aiosqlite:///{db_path}"))


def login(client: TestClient, name: str) -> tuple[int, str]:
    body = client.post(f"{API_PREFIX}/auth/login", json={"name": name}).json()
    return body["id"], body["token"]


@pytest.fixture
def tokens(client):
    alice_id, alice = login(client, "alice")
    bob_id, bob = login(client, "bob")
    assert (alice_id, bob_id) == (1, 2)
    return {1: alice, 2: bob}


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def sha256(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def session_rows(db_path) -> list[dict]:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute("SELECT * FROM user_sessions")]


def ws_close_code(client: TestClient, url: str) -> int:
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect(url):
            pass
    return excinfo.value.code


def user_scoped_requests():
    for router in ROUTERS:
        for route in router.routes:
            path = API_PREFIX + route.path
            if not isinstance(route, APIRoute) or path in PUBLIC_ROUTES:
                continue
            url = path.replace("{order_id}", "ORD-20240101000000-1")
            for name in ("user_id", "item_id"):
                url = url.replace(f"{{{name}}}", "1")
            for method in route.methods:
                yield pytest.param(method, url, id=f"{method} {path}")


def test_user_scoped_routes_are_enumerated():
    assert len(list(user_scoped_requests())) >= 13


@pytest.mark.parametrize("method,url", user_scoped_requests())
def test_every_user_scoped_route_rejects_missing_token(client, method, url):
    response = client.request(method, url, headers={"X-User-Id": "1"}, json={})
    assert response.status_code == 401, response.text
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("method,url", user_scoped_requests())
def test_every_user_scoped_route_rejects_unknown_token(client, method, url):
    response = client.request(method, url, headers=bearer("not-a-real-token"), json={})
    assert response.status_code == 401, response.text


def test_current_user_id_comes_from_the_token(client, tokens):
    assert client.get("/probe/me", headers=bearer(tokens[2])).json() == {"user_id": 2}


def test_non_bearer_scheme_is_rejected(client, tokens):
    response = client.get("/probe/me", headers={"Authorization": f"Basic {tokens[1]}"})
    assert response.status_code == 401


def test_path_user_route_rejects_missing_token(client):
    assert client.get("/probe/users/1").status_code == 401


def test_path_user_route_rejects_other_users_token(client, tokens):
    response = client.get("/probe/users/1", headers=bearer(tokens[2]))
    assert response.status_code == 403


def test_path_user_route_accepts_own_token(client, tokens):
    response = client.get("/probe/users/1", headers=bearer(tokens[1]))
    assert response.status_code == 200
    assert response.json() == {"user_id": 1}


def test_get_user_route_rejects_other_users_token(client, tokens):
    response = client.get(f"{API_PREFIX}/auth/user/1", headers=bearer(tokens[2]))
    assert response.status_code == 403


def test_tokens_are_unique_per_login(client):
    _, first = login(client, "alice")
    _, second = login(client, "alice")
    assert first != second
    assert len(first) >= 32


def test_token_survives_a_restart(client, db_path, tokens):
    restarted = TestClient(build_app(f"sqlite+aiosqlite:///{db_path}"))
    assert restarted.get("/probe/me", headers=bearer(tokens[1])).json() == {"user_id": 1}
    assert restarted.get("/probe/users/1", headers=bearer(tokens[2])).status_code == 403
    with restarted.websocket_connect(f"/probe/ws/1?token={tokens[1]}") as websocket:
        assert websocket.receive_json() == {"user_id": 1}


def test_logout_revokes_the_token(client, db_path, tokens):
    assert client.post(f"{API_PREFIX}/auth/logout", headers=bearer(tokens[1])).status_code == 200
    assert client.get("/probe/me", headers=bearer(tokens[1])).status_code == 401
    assert ws_close_code(client, f"/probe/ws/1?token={tokens[1]}") == WS_CLOSE_UNAUTHORIZED
    assert client.get("/probe/me", headers=bearer(tokens[2])).json() == {"user_id": 2}
    revoked = {row["token_hash"]: row["revoked_at"] for row in session_rows(db_path)}
    assert revoked[sha256(tokens[1])] is not None
    assert revoked[sha256(tokens[2])] is None


def test_expired_token_is_rejected(client, db_path, tokens):
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE user_sessions SET expires_at = '2000-01-01 00:00:00.000000' WHERE token_hash = ?",
            (sha256(tokens[1]),),
        )
    response = client.get("/probe/me", headers=bearer(tokens[1]))
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert ws_close_code(client, f"/probe/ws/1?token={tokens[1]}") == WS_CLOSE_UNAUTHORIZED
    assert client.get("/probe/me", headers=bearer(tokens[2])).json() == {"user_id": 2}


def test_next_login_deletes_expired_sessions(client, db_path, tokens):
    with sqlite3.connect(db_path) as conn:
        conn.execute("UPDATE user_sessions SET expires_at = '2000-01-01 00:00:00.000000' WHERE user_id = 1")
    login(client, "carol")
    assert sha256(tokens[1]) not in {row["token_hash"] for row in session_rows(db_path)}
    assert sha256(tokens[2]) in {row["token_hash"] for row in session_rows(db_path)}


def test_database_stores_only_the_token_hash(db_path, tokens):
    rows = session_rows(db_path)
    assert {row["token_hash"]: row["user_id"] for row in rows} == {
        sha256(tokens[1]): 1,
        sha256(tokens[2]): 2,
    }
    for row in rows:
        assert all(token not in str(value) for token in tokens.values() for value in row.values())
    raw = db_path.read_bytes()
    assert all(token.encode() not in raw for token in tokens.values())


def test_sessions_expire_after_seven_days_by_default(db_path, tokens):
    with sqlite3.connect(db_path) as conn:
        lifetimes = conn.execute(
            "SELECT julianday(expires_at) - julianday(created_at) FROM user_sessions"
        ).fetchall()
    assert [round(days, 6) for (days,) in lifetimes] == [7, 7]


def test_websocket_without_token_is_closed_unauthorized(client):
    assert ws_close_code(client, "/probe/ws/1") == WS_CLOSE_UNAUTHORIZED


def test_websocket_with_unknown_token_is_closed_unauthorized(client):
    assert ws_close_code(client, "/probe/ws/1?token=not-a-real-token") == WS_CLOSE_UNAUTHORIZED


def test_websocket_with_other_users_token_is_closed_forbidden(client, tokens):
    assert ws_close_code(client, f"/probe/ws/1?token={tokens[2]}") == WS_CLOSE_FORBIDDEN


def test_websocket_with_own_token_is_accepted(client, tokens):
    with client.websocket_connect(f"/probe/ws/1?token={tokens[1]}") as websocket:
        assert websocket.receive_json() == {"user_id": 1}
