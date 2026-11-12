"""
Fakes for the offline ADW tests (imported by the test modules, not a conftest, so the
stdlib-only tests next to them still run without the SDK installed).

The lesson CLAUDE.md says "do not mock tests"; that rule is for live tests against a
real database and real agents. These tests run keyless in CI, so they replace only
the two outside systems:

- The Claude CLI: ReplayClient stands in for ClaudeSDKClient and replays recorded
  SDK message streams. MCP tool calls in those streams go through the SDK's own
  in-process MCP bridge, the same path the CLI's tool calls take.
- PostgreSQL: MemorySink records what the run would have written to the ADW tables.

Everything between those two boundaries is the real code.
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_agent_sdk import (  # noqa: E402
    AssistantMessage,
    ResultError,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)
from claude_agent_sdk._internal.sdk_mcp_bridge import SdkMcpBridge  # noqa: E402


# =============================================================================
# SDK boundary: recorded message streams
# =============================================================================


def init_message(session_id: str = "sess-1") -> SystemMessage:
    return SystemMessage(subtype="init", data={"session_id": session_id, "tools": [], "slash_commands": []})


def assistant(*blocks: Any, message_id: str = "msg-1", usage: dict | None = None) -> AssistantMessage:
    return AssistantMessage(content=list(blocks), model="claude-opus", message_id=message_id, usage=usage)


def tool_call(name: str, tool_input: dict[str, Any], call_id: str = "tool-1") -> AssistantMessage:
    return assistant(ToolUseBlock(id=call_id, name=name, input=tool_input), message_id=f"msg-{call_id}")


def result(
    subtype: str = "success",
    *,
    is_error: bool = False,
    text: str | None = "done",
    cost: float = 0.5,
    turns: int = 3,
    errors: list[str] | None = None,
) -> ResultMessage:
    return ResultMessage(
        subtype=subtype, duration_ms=10, duration_api_ms=8, is_error=is_error,
        num_turns=turns, session_id="sess-1", total_cost_usd=cost, result=text,
        usage={"input_tokens": 100, "output_tokens": 50}, errors=errors,
    )


@dataclass
class Stall:
    """A pause in the stream, for wall clock tests."""

    seconds: float


class ReplayClient:
    """Plays a recorded stream in place of ClaudeSDKClient.

    After an assistant message with an mcp__<server>__<tool> call, it calls that tool
    through the SDK's MCP bridge and plays the tool result back, as the CLI would.
    After an error result it raises ResultError, as the SDK does when the CLI exits.
    """

    def __init__(self, script: list[Any], options: Any):
        self.script = script
        self.options = options
        self.prompt: str | None = None
        self.tool_results: list[ToolResultBlock] = []
        self._bridges: dict[str, SdkMcpBridge] = {}
        self._next_id = 1

    async def __aenter__(self) -> "ReplayClient":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        for bridge in self._bridges.values():
            await bridge.aclose()

    async def query(self, prompt: str) -> None:
        self.prompt = prompt

    async def receive_response(self):
        for item in self.script:
            if isinstance(item, Stall):
                await asyncio.sleep(item.seconds)
                continue
            yield item
            if isinstance(item, ResultMessage) and item.is_error:
                raise ResultError(f"Claude Code returned an error result: {item.subtype}", data={"subtype": item.subtype})
            if isinstance(item, AssistantMessage):
                for block in item.content:
                    if isinstance(block, ToolUseBlock) and block.name.startswith("mcp__"):
                        tool_result = await self._call_mcp(block)
                        self.tool_results.append(tool_result)
                        yield UserMessage(content=[tool_result])

    async def _rpc(self, bridge: SdkMcpBridge, method: str, params: dict[str, Any]) -> dict[str, Any]:
        self._next_id += 1
        response = await bridge.handle({"jsonrpc": "2.0", "id": self._next_id, "method": method, "params": params})
        assert response is not None
        return response

    async def _call_mcp(self, block: ToolUseBlock) -> ToolResultBlock:
        _, server, tool = block.name.split("__", 2)
        bridge = self._bridges.get(server)
        if bridge is None:
            bridge = self._bridges[server] = SdkMcpBridge(server, self.options.mcp_servers[server]["instance"])
            await self._rpc(bridge, "initialize", {
                "protocolVersion": "2025-06-18", "capabilities": {},
                "clientInfo": {"name": "replay", "version": "0"},
            })
            await bridge.handle({"jsonrpc": "2.0", "method": "notifications/initialized"})
        response = await self._rpc(bridge, "tools/call", {"name": tool, "arguments": block.input})
        payload = response["result"]
        text = "".join(c.get("text", "") for c in payload["content"])
        return ToolResultBlock(tool_use_id=block.id, content=text, is_error=payload["isError"])


class Replays:
    """client_factory that hands out one recorded script per query, in order."""

    def __init__(self, *scripts: list[Any]):
        self.scripts = list(scripts)
        self.clients: list[ReplayClient] = []

    def __call__(self, options: Any) -> ReplayClient:
        client = ReplayClient(self.scripts.pop(0), options)
        self.clients.append(client)
        return client


# =============================================================================
# DB boundary: an in-memory record of the ADW tables
# =============================================================================


class MemorySink:
    """Same async methods as adw_steps.DbSink. With fail=True every logging and
    agent-row call raises, as it would with the database down."""

    def __init__(self, row: dict[str, Any] | None = None, fail: bool = False):
        self.row = row
        self.fail = fail
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.output: dict[str, Any] = {}

    def _record(self, name: str, kwargs: dict[str, Any]) -> None:
        self.calls.append((name, kwargs))
        if self.fail:
            raise RuntimeError(f"database unavailable ({name})")

    def named(self, name: str) -> list[dict[str, Any]]:
        return [kw for n, kw in self.calls if n == name]

    @property
    def final_status(self) -> dict[str, Any]:
        return self.named("update_status")[-1]

    async def open(self) -> None:
        self.calls.append(("open", {}))

    async def close(self) -> None:
        self.calls.append(("close", {}))

    async def load(self, adw_id: str) -> dict[str, Any] | None:
        self.calls.append(("load", {"adw_id": adw_id}))
        return self.row

    async def update_status(self, **kw: Any) -> bool:
        self._record("update_status", kw)
        return True

    async def merge_output(self, adw_id: str, data: dict[str, Any]) -> bool:
        self._record("merge_output", {"adw_id": adw_id, "data": data})
        self.output.update(data)
        return True

    async def create_agent(self, **kw: Any) -> str:
        self._record("create_agent", kw)
        return str(uuid.uuid4())

    async def update_agent(self, **kw: Any) -> bool:
        self._record("update_agent", kw)
        return True

    async def log_event(self, **kw: Any) -> str:
        self._record("log_event", kw)
        return str(uuid.uuid4())

    async def log_step_start(self, **kw: Any) -> str:
        self._record("log_step_start", kw)
        return str(uuid.uuid4())

    async def log_step_end(self, **kw: Any) -> str:
        self._record("log_step_end", kw)
        return str(uuid.uuid4())

    async def log_system(self, **kw: Any) -> str:
        self._record("log_system", kw)
        return str(uuid.uuid4())

    async def summarize(self, adw_id: str, log_id: str, event_data: dict[str, Any], event_type: str) -> None:
        self.calls.append(("summarize", {"log_id": log_id, "event_type": event_type}))


ADW_ID = "6f1c2a7e-0b8d-4a39-9f3e-2d5b8c7a1e40"


def adw_row(working_dir: Path, **input_overrides: Any) -> dict[str, Any]:
    return {
        "orchestrator_agent_id": uuid.UUID("11111111-2222-3333-4444-555555555555"),
        "input_data": {"prompt": "Add a login form", "working_dir": str(working_dir), **input_overrides},
    }


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """A target project with one plan file already written."""
    plan = tmp_path / "specs" / "login form.md"
    plan.parent.mkdir()
    plan.write_text("# Plan: login form\n")
    return tmp_path
