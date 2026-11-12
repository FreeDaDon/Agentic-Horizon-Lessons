"""
Offline tests for WebSocketManager.broadcast.

The sockets are stand-ins for Starlette WebSocket objects, the external
boundary; the manager is the real one.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.websocket_manager import WebSocketManager  # noqa: E402

pytestmark = pytest.mark.asyncio


class Socket:
    def __init__(self, on_send=None):
        self.received = []
        self.on_send = on_send

    async def send_json(self, data):
        if self.on_send:
            self.on_send()
        self.received.append(data["type"])


class DeadSocket:
    async def send_json(self, data):
        raise RuntimeError("connection closed")


async def test_broadcast_reaches_every_client_when_one_disconnects_mid_broadcast():
    manager = WebSocketManager()
    first = Socket()
    second = Socket()
    # The first client's handler disconnects while the broadcast is suspended in its send
    first.on_send = lambda: manager.disconnect(first)
    manager.active_connections.extend([first, second])

    await manager.broadcast({"type": "agent_created"})

    assert first.received == ["agent_created"]
    assert second.received == ["agent_created"]


async def test_broadcast_drops_dead_connections_and_keeps_live_ones():
    manager = WebSocketManager()
    live = Socket()
    dead = DeadSocket()
    manager.active_connections.extend([dead, live])

    await manager.broadcast({"type": "heartbeat"})

    assert live.received == ["heartbeat"]
    assert manager.active_connections == [live]
