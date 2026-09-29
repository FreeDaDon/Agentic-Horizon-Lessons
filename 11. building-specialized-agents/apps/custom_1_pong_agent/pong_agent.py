#!/usr/bin/env python3
"""
Pong Agent - Level 0.1
The simplest possible agent that responds with 'pong' to any input.
This demonstrates the power of the system prompt and the absolute basics of the Claude Agent SDK.

Examples:
    # Default usage (sends "ping")
    python pong_agent.py

    # Custom prompt (still responds with "pong")
    python pong_agent.py --prompt "hello world"
    python pong_agent.py -p "what's 2+2?"
    python pong_agent.py --prompt "write a poem"

    # No matter what you send, it always responds with "pong"!
"""

import argparse
import asyncio
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    ResultMessage,
)

# Create a rich console for beautiful terminal output
console = Console()


def load_system_prompt() -> str:
    """
    Load the system prompt from the markdown file.
    Returns the content of the prompt file.
    """
    prompt_file = Path(__file__).parent / "prompts" / "PONG_AGENT_SYSTEM_PROMPT.md"

    with open(prompt_file, "r") as file:
        system_prompt = file.read().strip()

    return system_prompt


async def main():
    """
    The simplest pong agent with rich terminal output.
    This agent demonstrates:
    1. Basic SDK configuration
    2. Sending a query
    3. Handling responses
    4. Displaying results beautifully
    """

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Pong Agent - Always responds with 'pong'"
    )
    parser.add_argument(
        "--prompt",
        "-p",
        type=str,
        default="ping",
        help='The prompt to send (default: "ping"). Agent always responds with "pong" regardless.',
    )
    args = parser.parse_args()

    # Step 1: Configure the agent with a system prompt
    # Load the system prompt from the markdown file
    system_prompt = load_system_prompt()
    model = "claude-sonnet-4-20250514"

    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        model=model,
    )

    # Step 2: Display a beautiful startup message
    startup_message = "[bold cyan]🏓 Ping Agent Started[/bold cyan]"
    startup_panel = Panel.fit(startup_message, border_style="cyan")
    console.print(startup_panel)

    # Step 3: Show what we're sending
    input_prompt = args.prompt
    prompt_text = Text(input_prompt, style="bold yellow")
    prompt_panel = Panel(prompt_text, title="User Prompt", border_style="yellow")
    console.print(prompt_panel)
    console.print()  # Add some spacing

    # Step 4: Initialize tracking variables
    response_received = False
    session_stats = {}

    # Step 5: Send the query and process responses
    async for message in query(prompt=input_prompt, options=options):

        # Handle assistant messages (the actual response)
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    # Create a styled response panel
                    response_text = Text(block.text, style="bold green")
                    response_panel = Panel(
                        response_text, title="Agent Response", border_style="green"
                    )
                    console.print(response_panel)
                    response_received = True

        # Handle result messages (session metadata)
        elif isinstance(message, ResultMessage):
            # Extract and format session statistics
            session_id = message.session_id
            duration_ms = message.duration_ms
            cost_usd = message.total_cost_usd

            session_stats = {
                "Session ID": session_id,
                "Duration": f"{duration_ms}ms",
                "Cost": f"${cost_usd:.6f}" if cost_usd else "N/A",
            }

    # Step 6: Display session statistics in a formatted table
    if session_stats:
        console.print()  # Add spacing

        stats_table = Table(
            title="Session Stats", show_header=False, title_style="bold blue"
        )
        stats_table.add_column(style="cyan", no_wrap=True)
        stats_table.add_column(style="yellow")

        for stat_name, stat_value in session_stats.items():
            stats_table.add_row(stat_name, stat_value)

        console.print(stats_table)

    # Step 7: Display final result
    console.print()  # Add spacing

    if response_received:
        success_message = "[bold green]✅ Pong agent working correctly![/bold green]"
        console.print(success_message)
    else:
        error_message = "[bold red]❌ No response received[/bold red]"
        console.print(error_message)


if __name__ == "__main__":
    asyncio.run(main())
