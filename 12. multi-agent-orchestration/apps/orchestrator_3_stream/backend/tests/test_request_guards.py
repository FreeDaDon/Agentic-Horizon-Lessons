"""
Offline tests for the request guards in main.py.

TestClient is used without its context manager, so the app's lifespan (which
needs PostgreSQL) never runs. /send_chat and /load_chat get a recording
stand-in for app.state.orchestrator_service, whose real work is the Claude
SDK and the database; the tests check only which orchestrator id the
endpoints hand it.
"""

import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

sys.path.insert(0, str(Path(__file__).parent.parent))

import main  # noqa: E402
from modules import config  # noqa: E402

ALLOWED_ORIGIN = "http://127.0.0.1:5175"


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "CORS_ORIGINS", [ALLOWED_ORIGIN])
    monkeypatch.setattr(config, "IDE_ENABLED", True)
    monkeypatch.setattr(config, "IDE_COMMAND", "true")
    config.set_working_dir(str(tmp_path))
    yield TestClient(main.app)
    config.set_working_dir(config.ORCHESTRATOR_WORKING_DIR)


def test_websocket_from_allowed_origin_connects(client):
    with client.websocket_connect("/ws", headers={"origin": ALLOWED_ORIGIN}) as ws:
        assert ws.receive_json()["type"] == "connection_established"


def test_websocket_without_origin_connects(client):
    with client.websocket_connect("/ws") as ws:
        assert ws.receive_json()["type"] == "connection_established"


def test_websocket_from_other_origin_is_refused(client):
    with pytest.raises(WebSocketDisconnect) as refused:
        with client.websocket_connect("/ws", headers={"origin": "https://evil.example"}):
            pass
    assert refused.value.code == 1008
    assert main.ws_manager.get_connection_count() == 0


def test_open_file_inside_working_dir_is_opened(client, tmp_path):
    (tmp_path / "notes.md").write_text("hi")

    response = client.post("/api/open-file", json={"file_path": "notes.md"})

    assert response.json()["status"] == "success"
    assert response.json()["file_path"] == str(tmp_path / "notes.md")


@pytest.mark.parametrize("path", ["/etc/passwd", "../outside.txt", "sub/../../outside.txt"])
def test_open_file_outside_working_dir_is_refused(client, tmp_path, path):
    (tmp_path.parent / "outside.txt").write_text("secret")

    response = client.post("/api/open-file", json={"file_path": path})

    assert response.json()["status"] == "error"
    assert response.json()["message"] == "File is outside the orchestrator working directory"


class RecordingService:
    def __init__(self):
        self.orchestrator_ids = []

    async def process_user_message(self, user_message, orchestrator_agent_id):
        self.orchestrator_ids.append(orchestrator_agent_id)

    async def load_chat_history(self, orchestrator_agent_id, limit):
        self.orchestrator_ids.append(orchestrator_agent_id)
        return {"messages": [], "turn_count": 0}


@pytest.fixture
def orchestrator(client):
    service = RecordingService()
    own_id = uuid.uuid4()
    main.app.state.orchestrator_service = service
    main.app.state.orchestrator = SimpleNamespace(id=own_id)
    return service, str(own_id)


def test_send_chat_uses_the_servers_orchestrator(client, orchestrator):
    service, own_id = orchestrator

    response = client.post("/send_chat", json={"message": "hi", "orchestrator_agent_id": str(uuid.uuid4())})

    assert response.status_code == 200
    assert service.orchestrator_ids == [own_id]


def test_load_chat_uses_the_servers_orchestrator(client, orchestrator):
    service, own_id = orchestrator

    response = client.post("/load_chat", json={"orchestrator_agent_id": str(uuid.uuid4())})

    assert response.status_code == 200
    assert service.orchestrator_ids == [own_id]
