"""
The stream agent loop and the HTTP/WebSocket origin policy, run offline.

ClaudeSDKClient is replaced by a stub whose turn calls the real stream tools the way the
agent would, so line counting and context clearing run through the production code.
"""

import asyncio
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import main  # noqa: E402
from claude_agent_sdk import ResultMessage  # noqa: E402

FRONTEND = "http://localhost:5175"
FOREIGN = "https://evil.example"


class FakeClient:
    """One instance per agent session; `turns` scripts what the agent does on each query."""

    instances: list["FakeClient"] = []
    turns: list[dict] = []

    def __init__(self, options):
        self.options = options
        self.disconnected = False
        FakeClient.instances.append(self)

    async def connect(self, prompt=None):
        pass

    async def disconnect(self):
        self.disconnected = True

    async def query(self, prompt):
        self.prompt = prompt

    async def receive_response(self):
        turn = FakeClient.turns.pop(0)
        start = int(self.prompt)
        for index in range(start, start + turn.get("lines", 0)):
            await main.produce_summarized_log.handler(
                {"line_index": index, "log_id": f"id-{index}", "log_summary": "s", "log_severity": "low"}
            )
        if turn.get("clear"):
            await main.clear_context.handler({})
        yield ResultMessage(
            subtype="success", duration_ms=1, duration_api_ms=1, is_error=False, num_turns=1,
            session_id=turn.get("session_id", "session-1"),
        )


@pytest.fixture
def stream_agent(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "db_path", str(tmp_path / "ultra_stream.db"))
    main.init_database()
    session = main.get_session_info()
    session.stream_agent_session_id = "earlier-session"
    main.update_session_info(session)

    monkeypatch.setattr(main, "ClaudeSDKClient", FakeClient)
    monkeypatch.setattr(main, "current_line_index", 0)
    monkeypatch.setattr(main, "lines_processed_in_session", 0)
    monkeypatch.setattr(main, "context_clear_requested", False)
    monkeypatch.setattr(main, "raw_log_cache", {})
    FakeClient.instances = []
    FakeClient.turns = []
    asyncio.run(main.initialize_stream_agent(resume_session=True))
    return FakeClient.instances[0]


def run_turns(*turns):
    FakeClient.turns = list(turns)
    for _ in turns:
        asyncio.run(main.run_stream_agent_turn())


def test_startup_resumes_the_stored_session(stream_agent):
    assert stream_agent.options.resume == "earlier-session"


def test_lines_processed_counts_each_summarized_line(stream_agent):
    run_turns({"lines": 3}, {"lines": 1}, {"lines": 0})
    assert main.lines_processed_in_session == 4
    assert main.current_line_index == 4
    assert len(FakeClient.instances) == 1


def test_clear_context_starts_a_fresh_session(stream_agent):
    run_turns({"lines": 2, "clear": True, "session_id": "session-1"})

    old, new = FakeClient.instances
    assert old.disconnected
    assert new.options.resume is None
    assert main.stream_agent_client is new
    assert main.get_session_info().stream_agent_session_id == ""
    assert main.lines_processed_in_session == 0
    assert not main.context_clear_requested


def test_the_fresh_session_continues_from_the_current_line(stream_agent):
    run_turns({"lines": 2, "clear": True}, {"lines": 1, "session_id": "session-2"})
    assert FakeClient.instances[1].prompt == "2"
    assert main.get_session_info().stream_agent_session_id == "session-2"


def test_reaching_the_line_budget_clears_context(stream_agent):
    run_turns({"lines": main.MAX_LINES_BEFORE_CONTEXT_CLEAR - 1})
    assert len(FakeClient.instances) == 1
    run_turns({"lines": 1})
    assert len(FakeClient.instances) == 2
    assert FakeClient.instances[1].options.resume is None


@pytest.mark.parametrize("headers", [{}, {"origin": FRONTEND}, {"origin": "http://127.0.0.1:5175"}])
def test_requests_without_origin_or_from_the_frontend_are_served(headers):
    assert TestClient(main.app).get("/", headers=headers).status_code == 200


@pytest.mark.parametrize("origin", [FOREIGN, "null", "http://localhost:5175.evil.example"])
def test_requests_from_a_foreign_origin_are_rejected(origin):
    assert TestClient(main.app).get("/", headers={"origin": origin}).status_code == 403


def test_a_foreign_page_cannot_query_the_inspector(monkeypatch):
    asked = []

    async def handle_inspector_query(query):
        asked.append(query)
        return "answer"

    monkeypatch.setattr(main, "handle_inspector_query", handle_inspector_query)
    response = TestClient(main.app).post(
        "/inspector/query", json={"query": "dump the logs"}, headers={"origin": FOREIGN}
    )
    assert response.status_code == 403
    assert asked == []


def test_websocket_from_a_foreign_origin_is_refused():
    with pytest.raises(WebSocketDisconnect) as refused:
        with TestClient(main.app).websocket_connect("/ws", headers={"origin": FOREIGN}):
            pass
    assert refused.value.code == 1008
    assert main.active_connections == []
