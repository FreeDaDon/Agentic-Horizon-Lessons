"""Offline tests for Nile's session-token auth.

`src.main` cannot be imported without ANTHROPIC_API_KEY (it builds the agent at import
time), so these tests mount the real routers on a minimal app the same way main.py
does, plus a WebSocket endpoint that guards itself exactly like `/ws/home/{user_id}`.
Nothing is faked. Every request asserted here is rejected or answered before a route
reaches the database, so no database file is opened.

Run: cd apps/nile/server && uv run pytest tests/test_auth.py
"""
import pytest
from fastapi import Depends, FastAPI, WebSocket
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from src.config import API_PREFIX
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
    issue_token,
    path_user_id,
    revoke_token,
)

PUBLIC_ROUTES = {
    f"{API_PREFIX}/auth/login",
    f"{API_PREFIX}/products",
    f"{API_PREFIX}/products/search",
    f"{API_PREFIX}/products/categories",
    f"{API_PREFIX}/products/brands",
    f"{API_PREFIX}/products/{{product_id}}",
    f"{API_PREFIX}/products/by-ids/{{product_ids}}",
}

app = FastAPI()
for router in (auth_router, products_router, cart_router, orders_router, expertise_router, home_router):
    app.include_router(router, prefix=API_PREFIX)


@app.get("/probe/me")
async def probe_me(user_id: int = Depends(current_user_id)):
    return {"user_id": user_id}


@app.get("/probe/users/{user_id}")
async def probe_user(user_id: int = Depends(path_user_id)):
    return {"user_id": user_id}


@app.websocket("/probe/ws/{user_id}")
async def probe_ws(websocket: WebSocket, user_id: int):
    if not await authorize_websocket(websocket, user_id):
        return
    await websocket.accept()
    await websocket.send_json({"user_id": user_id})
    await websocket.close()


client = TestClient(app)


@pytest.fixture
def tokens():
    issued = {1: issue_token(1), 2: issue_token(2)}
    yield issued
    for token in issued.values():
        revoke_token(token)


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def user_scoped_requests():
    for route in app.routes:
        if not isinstance(route, APIRoute) or not route.path.startswith(API_PREFIX):
            continue
        if route.path in PUBLIC_ROUTES:
            continue
        url = route.path.replace("{order_id}", "ORD-20240101000000-1")
        for name in ("user_id", "item_id"):
            url = url.replace(f"{{{name}}}", "1")
        for method in route.methods:
            yield pytest.param(method, url, id=f"{method} {route.path}")


def test_user_scoped_routes_are_enumerated():
    assert len(list(user_scoped_requests())) >= 13


@pytest.mark.parametrize("method,url", user_scoped_requests())
def test_every_user_scoped_route_rejects_missing_token(method, url):
    response = client.request(method, url, headers={"X-User-Id": "1"}, json={})
    assert response.status_code == 401, response.text
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("method,url", user_scoped_requests())
def test_every_user_scoped_route_rejects_unknown_token(method, url):
    response = client.request(method, url, headers=bearer("not-a-real-token"), json={})
    assert response.status_code == 401, response.text


def test_current_user_id_comes_from_the_token(tokens):
    assert client.get("/probe/me", headers=bearer(tokens[2])).json() == {"user_id": 2}


def test_non_bearer_scheme_is_rejected(tokens):
    response = client.get("/probe/me", headers={"Authorization": f"Basic {tokens[1]}"})
    assert response.status_code == 401


def test_path_user_route_rejects_missing_token():
    assert client.get("/probe/users/1").status_code == 401


def test_path_user_route_rejects_other_users_token(tokens):
    response = client.get("/probe/users/1", headers=bearer(tokens[2]))
    assert response.status_code == 403


def test_path_user_route_accepts_own_token(tokens):
    response = client.get("/probe/users/1", headers=bearer(tokens[1]))
    assert response.status_code == 200
    assert response.json() == {"user_id": 1}


def test_get_user_route_rejects_other_users_token(tokens):
    response = client.get(f"{API_PREFIX}/auth/user/1", headers=bearer(tokens[2]))
    assert response.status_code == 403


def test_logout_revokes_the_token():
    token = issue_token(1)
    assert client.post(f"{API_PREFIX}/auth/logout", headers=bearer(token)).status_code == 200
    assert client.get("/probe/me", headers=bearer(token)).status_code == 401


def test_tokens_are_unique_per_login():
    first, second = issue_token(1), issue_token(1)
    try:
        assert first != second
        assert len(first) >= 32
    finally:
        revoke_token(first)
        revoke_token(second)


def test_websocket_without_token_is_closed_unauthorized():
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect("/probe/ws/1"):
            pass
    assert excinfo.value.code == WS_CLOSE_UNAUTHORIZED


def test_websocket_with_unknown_token_is_closed_unauthorized():
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect("/probe/ws/1?token=not-a-real-token"):
            pass
    assert excinfo.value.code == WS_CLOSE_UNAUTHORIZED


def test_websocket_with_other_users_token_is_closed_forbidden(tokens):
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect(f"/probe/ws/1?token={tokens[2]}"):
            pass
    assert excinfo.value.code == WS_CLOSE_FORBIDDEN


def test_websocket_with_own_token_is_accepted(tokens):
    with client.websocket_connect(f"/probe/ws/1?token={tokens[1]}") as websocket:
        assert websocket.receive_json() == {"user_id": 1}
