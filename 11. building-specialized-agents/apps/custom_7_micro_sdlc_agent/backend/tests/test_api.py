"""
The HTTP/WebSocket surface and the ticket workflow, run offline.

TestClient is used without `with`, so the lifespan (database init) never runs. Database
calls are replaced by in-memory fakes and ClaudeSDKClient by a stub, so no agent starts.
"""

import asyncio
import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

sys.path.insert(0, str(Path(__file__).parent.parent))

import main  # noqa: E402
import modules.agent_orchestrator as orch  # noqa: E402
from claude_agent_sdk import AssistantMessage, TextBlock  # noqa: E402
from modules.config import DEFAULT_CODEBASE_PATH  # noqa: E402

FRONTEND = "http://127.0.0.1:5174"
FOREIGN = "https://evil.example"


@pytest.fixture
def tickets(monkeypatch):
    """Replace the ticket store with a dict; returns the dict."""
    store = {}

    async def create_ticket(**fields):
        ticket_id = len(store) + 1
        store[ticket_id] = {"id": ticket_id, "stage": "idle", **fields}
        return ticket_id

    async def get_ticket(ticket_id):
        return store.get(ticket_id)

    async def update_ticket_stage(ticket_id, stage):
        store[ticket_id]["stage"] = stage

    async def ignore(*args, **kwargs):
        return {}

    monkeypatch.setattr(main, "create_ticket", create_ticket)
    monkeypatch.setattr(main, "get_ticket", get_ticket)
    monkeypatch.setattr(main, "update_ticket_stage", update_ticket_stage)
    for name in ("update_ticket_plan", "update_ticket_build", "update_ticket_review", "append_agent_message"):
        monkeypatch.setattr(main, name, ignore)
    return store


def new_ticket(client, origin=None, **overrides):
    body = {"title": "t", "content_user_request_prompt": "do it", **overrides}
    headers = {"origin": origin} if origin else {}
    return client.post("/tickets", json=body, headers=headers)


# ---- Origin policy ----------------------------------------------------------


@pytest.mark.parametrize("headers", [{}, {"origin": FRONTEND}, {"origin": "http://localhost:5174"}])
def test_requests_without_origin_or_from_the_frontend_are_served(headers):
    assert TestClient(main.app).get("/health", headers=headers).status_code == 200


@pytest.mark.parametrize("origin", [FOREIGN, "null", "http://127.0.0.1:5174.evil.example"])
def test_requests_from_a_foreign_origin_are_rejected(origin):
    assert TestClient(main.app).get("/health", headers={"origin": origin}).status_code == 403


def test_a_foreign_page_cannot_create_a_ticket(tickets):
    response = new_ticket(TestClient(main.app), origin=FOREIGN)
    assert response.status_code == 403
    assert tickets == {}


def test_a_foreign_page_cannot_start_a_workflow(tickets, monkeypatch):
    started = []
    monkeypatch.setattr(main, "run_workflow", lambda ticket_id: started.append(ticket_id))
    client = TestClient(main.app)
    assert new_ticket(client).status_code == 200

    response = client.put("/tickets/1/stage", json={"stage": "plan"}, headers={"origin": FOREIGN})

    assert response.status_code == 403
    assert tickets[1]["stage"] == "idle"
    assert started == []


def test_websocket_from_the_frontend_connects():
    with TestClient(main.app).websocket_connect("/ws", headers={"origin": FRONTEND}):
        assert len(main.manager.active_connections) == 1
    assert main.manager.active_connections == []


def test_websocket_from_a_foreign_origin_is_refused():
    with pytest.raises(WebSocketDisconnect) as refused:
        with TestClient(main.app).websocket_connect("/ws", headers={"origin": FOREIGN}):
            pass
    assert refused.value.code == 1008
    assert main.manager.active_connections == []


@pytest.fixture
def configured_origins(monkeypatch):
    monkeypatch.setenv("MICRO_SDLC_ALLOWED_ORIGINS", "https://board.example, http://10.0.0.5:5174/")
    importlib.reload(main)
    yield
    monkeypatch.delenv("MICRO_SDLC_ALLOWED_ORIGINS")
    importlib.reload(main)


def test_allowed_origins_come_from_the_environment(configured_origins):
    client = TestClient(main.app)
    assert client.get("/health", headers={"origin": "https://board.example"}).status_code == 200
    assert client.get("/health", headers={"origin": "http://10.0.0.5:5174"}).status_code == 200
    assert client.get("/health", headers={"origin": FRONTEND}).status_code == 403


# ---- Ticket input validation ------------------------------------------------


@pytest.mark.parametrize("model", ["opus", "sonnet", "haiku"])
def test_model_aliases_are_accepted(tickets, model):
    assert new_ticket(TestClient(main.app), model=model).status_code == 200
    assert tickets[1]["model"] == model


@pytest.mark.parametrize("model", ["gpt-4", "claude-opus-latest", "", "SONNET"])
def test_other_models_are_rejected(tickets, model):
    assert new_ticket(TestClient(main.app), model=model).status_code == 422
    assert tickets == {}


def test_relative_codebase_paths_resolve_against_the_app_root(tickets):
    assert new_ticket(TestClient(main.app), parent_codebase_path="./frontend").status_code == 200
    assert tickets[1]["parent_codebase_path"] == str(Path(DEFAULT_CODEBASE_PATH, "frontend").resolve())


def test_absolute_codebase_path_is_stored_resolved(tickets, tmp_path):
    (tmp_path / "repo").mkdir()
    response = new_ticket(TestClient(main.app), parent_codebase_path=f"{tmp_path}/x/../repo")
    assert response.status_code == 200
    assert tickets[1]["parent_codebase_path"] == str((tmp_path / "repo").resolve())


@pytest.mark.parametrize("path", ["./does-not-exist", "main.py"])
def test_codebase_path_must_be_an_existing_directory(tickets, path):
    assert new_ticket(TestClient(main.app), parent_codebase_path=path).status_code == 422
    assert tickets == {}


# ---- The workflow uses the ticket's codebase -------------------------------


def test_every_agent_runs_in_the_tickets_codebase(tickets, monkeypatch, tmp_path):
    codebase = (tmp_path / "repo").resolve()
    codebase.mkdir()
    agent_options = []

    class FakeClient:
        def __init__(self, options):
            agent_options.append(options)

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def query(self, prompt):
            pass

        async def receive_response(self):
            yield AssistantMessage(content=[TextBlock(text="specs/plan.md")], model="stub")

    monkeypatch.setattr(orch, "ClaudeSDKClient", FakeClient)
    asyncio.run(main.create_ticket(
        title="t", content_user_request_prompt="p", model="haiku", parent_codebase_path=str(codebase),
    ))

    asyncio.run(main.run_workflow(1))

    assert tickets[1]["stage"] == "shipped"
    assert [o.cwd for o in agent_options] == [str(codebase)] * 3
    assert [o.model for o in agent_options] == ["haiku"] * 3

    builder_hook = agent_options[1].hooks["PreToolUse"][0].hooks[0]

    def builder_decision(file_path):
        out = asyncio.run(builder_hook({"tool_name": "Edit", "tool_input": {"file_path": file_path}}, None, None))
        return out.get("hookSpecificOutput", {}).get("permissionDecision", "allow")

    assert builder_decision(f"{codebase}/src/app.py") == "allow"
    assert builder_decision(f"{DEFAULT_CODEBASE_PATH}/backend/main.py") == "deny"
