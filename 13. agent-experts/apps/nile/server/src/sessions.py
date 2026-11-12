"""Session tokens for Nile.

Login issues an opaque random token (`secrets.token_urlsafe`). Tokens live only in
the in-memory `_sessions` dict below, keyed by token. That is a demo shortcut:
every token is lost when the server restarts (including uvicorn `--reload`), and
tokens are not shared between processes, so run Nile as a single uvicorn worker.
After a restart the client gets a 401 and sends the user back to the login page.

HTTP routes read the token from `Authorization: Bearer <token>`. Browsers cannot
set headers on a WebSocket handshake, so WebSocket routes read `?token=` instead.
"""
import secrets

from fastapi import Depends, HTTPException, WebSocket
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

WS_CLOSE_UNAUTHORIZED = 4401
WS_CLOSE_FORBIDDEN = 4403

_sessions: dict[str, int] = {}
_bearer = HTTPBearer(auto_error=False)


def issue_token(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    _sessions[token] = user_id
    return token


def revoke_token(token: str) -> None:
    _sessions.pop(token, None)


async def session_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """The caller's token; 401 when the bearer token is missing or unknown."""
    if credentials is None or credentials.credentials not in _sessions:
        raise HTTPException(
            status_code=401,
            detail="Missing or unknown session token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


async def current_user_id(token: str = Depends(session_token)) -> int:
    return _sessions[token]


async def path_user_id(user_id: int, caller_id: int = Depends(current_user_id)) -> int:
    """The `{user_id}` path parameter, 403 unless it is the caller's own id."""
    if user_id != caller_id:
        raise HTTPException(status_code=403, detail="Token does not belong to this user")
    return user_id


async def authorize_websocket(websocket: WebSocket, user_id: int) -> bool:
    """Close the handshake unless `?token=` belongs to `user_id`; True when allowed."""
    caller_id = _sessions.get(websocket.query_params.get("token", ""))
    if caller_id is None:
        await websocket.close(code=WS_CLOSE_UNAUTHORIZED)
        return False
    if caller_id != user_id:
        await websocket.close(code=WS_CLOSE_FORBIDDEN)
        return False
    return True
