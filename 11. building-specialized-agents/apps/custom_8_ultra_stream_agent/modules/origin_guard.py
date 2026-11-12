"""Reject requests and WebSocket handshakes sent from a disallowed browser origin.

CORS only decides whether a page may read a response. A browser still sends a
cross-site form POST or WebSocket handshake, so without this check any open web
page could drive the agents and read the processed logs.
"""

import os

from starlette.datastructures import Headers
from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.websockets import WebSocketClose


def allowed_origins(env_var: str, defaults: list[str]) -> list[str]:
    """Comma-separated origins from env_var, or defaults when it is unset or empty."""
    configured = [o.strip().rstrip("/") for o in os.environ.get(env_var, "").split(",")]
    return [o for o in configured if o] or defaults


class RejectDisallowedOrigins:
    """ASGI middleware: 403 (HTTP) or close 1008 (WebSocket) when Origin is present and not allowed.

    Requests without an Origin header (curl, scripts, same-origin GETs) pass through.
    """

    def __init__(self, app: ASGIApp, allowed: list[str]):
        self.app = app
        self.allowed = frozenset(allowed)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in ("http", "websocket"):
            origin = Headers(scope=scope).get("origin")
            if origin is not None and origin not in self.allowed:
                if scope["type"] == "http":
                    reject = PlainTextResponse("Origin not allowed", status_code=403)
                else:
                    reject = WebSocketClose(code=1008)
                await reject(scope, receive, send)
                return
        await self.app(scope, receive, send)
