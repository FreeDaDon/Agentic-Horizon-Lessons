"""Session tokens for Nile.

Login issues an opaque random token (`secrets.token_urlsafe`) and stores one
`UserSession` row in Nile's database. The row keeps only the sha256 hex digest of
the token, so a copy of the database cannot be replayed as a login. Tokens survive
server restarts and are shared by every worker that uses the same database.

A token is valid until `expires_at` (`SESSION_LIFETIME`, set with the
`SESSION_LIFETIME_HOURS` env var, default 7 days) or until logout sets
`revoked_at`. An expired or revoked token gets a 401, and the client sends the user
back to the login page. Rows past their expiry are deleted on the next login.

HTTP routes read the token from `Authorization: Bearer <token>`. Browsers cannot
set headers on a WebSocket handshake, so WebSocket routes read `?token=` instead.
"""
import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, WebSocket
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .config import SESSION_LIFETIME
from .database import get_db
from .models import UserSession

WS_CLOSE_UNAUTHORIZED = 4401
WS_CLOSE_FORBIDDEN = 4403

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class _Caller:
    token: str
    user_id: int


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _utcnow() -> datetime:
    """Naive UTC, matching how the other models store timestamps in SQLite."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def issue_token(db: AsyncSession, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    now = _utcnow()
    await db.execute(delete(UserSession).where(UserSession.expires_at <= now))
    db.add(
        UserSession(
            token_hash=_hash(token),
            user_id=user_id,
            created_at=now,
            expires_at=now + SESSION_LIFETIME,
        )
    )
    await db.commit()
    return token


async def revoke_token(db: AsyncSession, token: str) -> None:
    await db.execute(
        update(UserSession)
        .where(UserSession.token_hash == _hash(token), UserSession.revoked_at.is_(None))
        .values(revoked_at=_utcnow())
    )
    await db.commit()


async def _user_id_for(db: AsyncSession, token: str) -> int | None:
    """The token's user while it is unexpired and unrevoked, else None."""
    return await db.scalar(
        select(UserSession.user_id).where(
            UserSession.token_hash == _hash(token),
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > _utcnow(),
        )
    )


async def _caller(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> _Caller:
    """401 when the bearer token is missing, unknown, expired or revoked."""
    user_id = None if credentials is None else await _user_id_for(db, credentials.credentials)
    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Missing, unknown, expired or revoked session token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _Caller(token=credentials.credentials, user_id=user_id)


async def session_token(caller: _Caller = Depends(_caller)) -> str:
    return caller.token


async def current_user_id(caller: _Caller = Depends(_caller)) -> int:
    return caller.user_id


async def path_user_id(user_id: int, caller_id: int = Depends(current_user_id)) -> int:
    """The `{user_id}` path parameter, 403 unless it is the caller's own id."""
    if user_id != caller_id:
        raise HTTPException(status_code=403, detail="Token does not belong to this user")
    return user_id


async def authorize_websocket(websocket: WebSocket, user_id: int, db: AsyncSession) -> bool:
    """Close the handshake unless `?token=` belongs to `user_id`; True when allowed."""
    caller_id = await _user_id_for(db, websocket.query_params.get("token", ""))
    if caller_id is None:
        await websocket.close(code=WS_CLOSE_UNAUTHORIZED)
        return False
    if caller_id != user_id:
        await websocket.close(code=WS_CLOSE_FORBIDDEN)
        return False
    return True
