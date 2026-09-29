#!/usr/bin/env python3
"""
Echo Agent - Level 1.1
Demonstrates creating a custom tool with parameters.
Key new concept: Custom tools with @tool decorator and MCP server
"""

import asyncio
import sys
from pathlib import Path
from typing import Any
import argparse
from rich.console import Console
from rich.panel import Panel
from claude_agent_sdk import (
    tool,
    create_sdk_mcp_server,
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
)

console = Console()


def load_system_prompt() -> str:
    """
    Load the system prompt from the markdown file.
    Returns the content of the prompt file.
    """
    prompt_file = Path(__file__).parent / "prompts" / "ECHO_AGENT_SYSTEM_PROMPT.md"

    with open(prompt_file, "r") as file:
        system_prompt = file.read().strip()

    return system_prompt


@tool(
    "echo",
    "Echo a message with transformations",
    {"message": str, "repeat": int, "transform": str},
)
async def echo_tool(args: dict[str, Any]) -> dict[str, Any]:
    """
    Custom tool with parameters - the NEW feature over pong agent.
    """
    # Extract parameters
    message = args["message"]
    repeat = args.get("repeat", 1)
    transform = args.get("transform", "none")

    # Transform
    if transform == "uppercase":
        message = message.upper()
    elif transform == "lowercase":
        message = message.lower()
    elif transform == "reverse":
        message = message[::-1]

    # Repeat
    result = " ".join([message] * repeat)

    # Show what happened
    console.print(Panel(f"{result}", title="🔧 Echo Tool", border_style="blue"))

    return {"content": [{"type": "text", "text": result}]}


async def main():
    """
    Echo agent with custom tool.
    NEW: Using ClaudeSDKClient because query() doesn't support custom tools!
    """

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Echo Agent with optional follow-up")
    parser.add_argument(
        "--follow-up", action="store_true", help="Add conversation summary at the end"
    )
    parser.add_argument("prompt", nargs="*", help="The prompt to send to the agent")

    args = parser.parse_args()
    follow_up = args.follow_up

    # Determine user prompt
    if args.prompt:
        user_prompt = " ".join(args.prompt)
    else:
        user_prompt = "Echo 'Hello World' 3 times in uppercase"

    console.print(
        Panel.fit("[bold magenta]🔊 Echo Agent[/bold magenta]", border_style="magenta")
    )

    # Create MCP server with our tool
    echo_server = create_sdk_mcp_server(
        name="echo_server", version="1.0.0", tools=[echo_tool]
    )

    # Configure with MCP server
    # Load the system prompt from the markdown file
    system_prompt = load_system_prompt()

    options = ClaudeAgentOptions(
        mcp_servers={"echo": echo_server},
        allowed_tools=["mcp__echo__echo"],  # Format: mcp__<server>__<tool>
        system_prompt=system_prompt,
        model="claude-3-5-haiku-20241022",
        # model="claude-sonnet-4-20250514",
    )

    # Use ClaudeSDKClient for custom tools
    async with ClaudeSDKClient(options=options) as client:

        console.print(
            Panel(f"{user_prompt}", title="User Prompt", border_style="yellow")
        )

        # Send query
        await client.query(user_prompt)

        # Get response
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, ToolUseBlock):
                        console.print(
                            Panel(
                                f"{block.name}",
                                title="Tool Called",
                                border_style="cyan",
                                style="dim",
                            )
                        )
                    elif isinstance(block, TextBlock):
                        console.print(
                            Panel(
                                block.text, title="Agent Response", border_style="green"
                            )
                        )

        # Follow-up functionality
        if follow_up:
            follow_up_prompt = "Concisely summarize our conversation in bullet points"

            console.print(
                Panel(
                    f"{follow_up_prompt}",
                    title="Follow-up Prompt",
                    border_style="yellow",
                )
            )

            # Send follow-up query
            await client.query(follow_up_prompt)

            # Get follow-up response
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, ToolUseBlock):
                            console.print(
                                Panel(
                                    f"{block.name}",
                                    title="Follow-up Tool Called",
                                    border_style="cyan",
                                    style="dim",
                                )
                            )
                        elif isinstance(block, TextBlock):
                            console.print(
                                Panel(
                                    block.text,
                                    title="Follow-up Response",
                                    border_style="green",
                                )
                            )

    console.print("[green]✅ Done![/green]")


if __name__ == "__main__":
    asyncio.run(main())
