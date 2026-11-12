#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["claude-agent-sdk==0.2.163"]
# ///
"""A narrow analyst agent: reads bars through one tool and returns a typed signal proposal, never an order."""

import asyncio
import sys

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ToolUseBlock,
    create_sdk_mcp_server,
    tool,
)

BARS = {"SPY": [501.2, 503.9, 502.4, 506.8, 509.1], "QQQ": [433.0, 431.2, 428.7, 426.9, 425.5]}


@tool("get_bars", "Daily closes for a symbol, oldest first", {"symbol": str})
async def get_bars(args):
    closes = BARS.get(args["symbol"].upper())
    if closes is None:
        return {"content": [{"type": "text", "text": f"Unknown symbol {args['symbol']}"}], "is_error": True}
    return {"content": [{"type": "text", "text": ", ".join(map(str, closes))}]}


@tool("submit_signal", "Submit the final signal proposal",
      {"symbol": str, "side": str, "confidence": float, "rationale": str})
async def submit_signal(args):
    return {"content": [{"type": "text", "text": "recorded"}]}


OPTIONS = ClaudeAgentOptions(
    system_prompt="You are a signal analyst. Read bars with get_bars, then call submit_signal exactly once. "
                  "side is long, short or flat. You never place orders.",
    model="haiku",
    mcp_servers={"signals": create_sdk_mcp_server(name="signals", version="1.0.0", tools=[get_bars, submit_signal])},
    allowed_tools=["mcp__signals__get_bars", "mcp__signals__submit_signal"],
    disallowed_tools=["Bash", "Write", "Edit", "MultiEdit", "NotebookEdit", "Read", "Glob", "Grep",
                      "WebFetch", "WebSearch", "Task", "TodoWrite"],
    max_turns=4,
)


async def analyze(symbol: str) -> dict | None:
    async with ClaudeSDKClient(options=OPTIONS) as client:
        await client.query(f"Propose a signal for {symbol}.")
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, ToolUseBlock) and block.name == "mcp__signals__submit_signal":
                        return dict(block.input)
    return None


if __name__ == "__main__":
    print(asyncio.run(analyze(sys.argv[1] if len(sys.argv) > 1 else "SPY")))
