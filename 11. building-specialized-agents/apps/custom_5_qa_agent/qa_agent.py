#!/usr/bin/env python3
"""
QA Agent - Level 2
A specialized REPL agent for codebase question answering with parallel search capabilities.

Features:
- Interactive REPL with conversation continuity
- Rich terminal output with panels for all message types
- Controlled tool access (only codebase tools allowed)
- Inline hook-based security for subagent monitoring
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Rich imports for beautiful terminal output
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner
from rich.prompt import Prompt
from rich.columns import Columns
from rich.markdown import Markdown

# Claude Agent SDK imports
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    ThinkingBlock,
    ToolUseBlock,
    ToolResultBlock,
    ResultMessage,
    SystemMessage,
    UserMessage,
    HookMatcher,
    HookContext,
)


# Initialize console for rich output
console = Console()


async def block_env_files(
    input_data: dict[str, Any], tool_use_id: str | None, context: HookContext
) -> dict[str, Any]:
    """
    Hook to block .env file access from both main agent and subagents.

    This security hook prevents reading of environment files that may contain secrets.
    Read, Grep and Bash can all read a file, so each one is checked.
    """

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # What each file-reading tool would touch
    if tool_name == "Read":
        file_path = tool_input.get("file_path", "")
    elif tool_name == "Grep":
        file_path = f"{tool_input.get('path', '')} {tool_input.get('glob', '')}"
    elif tool_name == "Bash":
        file_path = tool_input.get("command", "")
    else:
        return {}

    # Block .env files
    if ".env" in file_path:
        console.print(
            Panel(
                f"Blocked access to: {file_path}\n\n"
                "[yellow]Environment files contain sensitive credentials and are prohibited.[/yellow]",
                title="🔒 SECURITY HOOK",
                border_style="red",
                expand=False,
            )
        )
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": "Security policy: .env files are blocked for credential protection. Do not attempt to access .env files.",
            }
        }

    # Warn about other sensitive files
    sensitive_patterns = [
        "credentials",
        "secrets",
        "password",
        "token",
        "api_key",
        "private_key",
        ".pem",
        ".key",
        ".crt",
    ]

    file_lower = file_path.lower()
    for pattern in sensitive_patterns:
        if pattern in file_lower:
            console.print(
                Panel(
                    f"Accessing potentially sensitive file:\n{file_path}",
                    title="⚠️ Hook Warning",
                    border_style="yellow",
                    expand=False,
                )
            )
            # Allow but warn
            break

    return {}


async def log_tool_usage(
    input_data: dict[str, Any], tool_use_id: str | None, context: HookContext
) -> dict[str, Any]:
    """
    Hook to log all tool usage for security auditing.
    """

    tool_name = input_data.get("tool_name", "")

    # Only log certain tools to reduce noise
    if tool_name in ["Read", "Write", "Edit", "Bash"]:
        timestamp = datetime.now().strftime("%H:%M:%S")
        console.print(
            Panel(
                f"[{timestamp}] {tool_name}",
                title="🔍 Tool Audit",
                border_style="dark_orange",
                style="dim",
                expand=False,
            )
        )

    return {}


def load_system_prompt() -> str:
    """
    Load the QA Agent system prompt from the markdown file.

    Returns:
        The content of the system prompt file.
    """
    prompt_file = Path(__file__).parent / "prompts" / "QA_AGENT_SYSTEM_PROMPT.md"

    if not prompt_file.exists():
        console.print(
            "[red]Error: System prompt file not found![/red]", style="bold red"
        )
        sys.exit(1)

    with open(prompt_file, "r") as file:
        system_prompt = file.read().strip()

    return system_prompt


def load_mcp_config() -> str:
    """
    Load MCP server configuration path.

    Returns:
        Path to the MCP configuration file.
    """
    mcp_config = Path(__file__).parent / ".mcp.json.firecrawl_6k"

    if mcp_config.exists():
        return str(mcp_config)
    else:
        console.print(
            "[yellow]Warning: MCP config not found, proceeding without Firecrawl[/yellow]"
        )
        return ""


def display_startup_banner():
    """Display a beautiful startup banner for the QA Agent."""

    banner = Panel(
        "[bold cyan]🔍 QA Agent - Codebase Question & Answer System[/bold cyan]\n\n"
        "[dim]Specialized for parallel codebase search and analysis[/dim]\n"
        "[dim cyan]📝 Custom slash command: /qa_agent <question>[/dim cyan]\n"
        "[dim yellow]🔒 Security: Hook-based .env blocking for all agents[/dim yellow]",
        title="[bold]Welcome[/bold]",
        border_style="cyan",
    )
    console.print(banner)
    console.print()


def display_help():
    """Display help information for the REPL."""

    help_table = Table(title="Available Commands", title_style="bold cyan")
    help_table.add_column("Command", style="yellow", no_wrap=True)
    help_table.add_column("Description", style="white")

    help_table.add_row("Any question", "Automatically wrapped in /qa_agent command")
    help_table.add_row("/qa_agent <question>", "Explicit slash command usage")
    help_table.add_row("/help", "Show this help message")
    help_table.add_row("/stats", "Show session statistics")
    help_table.add_row("/clear", "Clear conversation history")
    help_table.add_row("/exit or quit", "Exit the QA Agent")

    console.print(help_table)
    console.print()


def display_tool_use(block: ToolUseBlock):
    """Display tool use information in a formatted panel."""

    # Display the tool call panel similar to calc_agent
    console.print(
        Panel(f"{block.name}", title="Tool Called", border_style="cyan", style="dim")
    )

    # Show parameters in a separate panel if they exist and are complex
    if block.input:
        # Create title with tool name
        params_title = f"{block.name} Params"

        # For simple parameters, show inline
        if len(json.dumps(block.input)) <= 100:
            params_text = json.dumps(block.input, indent=2)
            console.print(
                Panel(params_text, title=params_title, border_style="dim", expand=False)
            )
        else:
            # For complex parameters, use syntax highlighting
            console.print(
                Panel(
                    Syntax(
                        json.dumps(block.input, indent=2),
                        "json",
                        theme="monokai",
                        line_numbers=False,
                    ),
                    title=params_title,
                    border_style="dim",
                    expand=False,
                )
            )


def display_tool_result(block: ToolResultBlock, tool_name: str = None):
    """Display tool result information in a formatted panel."""

    # Determine result status
    status = "✅" if not block.is_error else "❌"
    status_color = "green" if not block.is_error else "red"

    # Format content
    if block.content:
        if isinstance(block.content, str):
            content = block.content
        elif isinstance(block.content, list):
            content = json.dumps(block.content, indent=2)
        else:
            content = str(block.content)

        # Truncate if too long
        if len(content) > 1000:
            content = content[:997] + "..."
    else:
        content = "No output"

    # Create title with tool name if available
    if tool_name:
        title = f"{status} {tool_name} Result"
    else:
        title = f"{status} Tool Result"

    panel = Panel(content, title=title, border_style=status_color, expand=False)
    console.print(panel)


def display_thinking(block: ThinkingBlock):
    """Display thinking block in a subtle panel."""

    panel = Panel(
        Text(block.thinking, style="italic purple"),
        title="[yellow]💭 Thinking[/yellow]",
        border_style="dim",
        expand=False,
    )
    console.print(panel)


def display_text(block: TextBlock):
    """Display text content in an Agent Response panel."""

    # Display the agent's text response in a panel
    console.print(Panel(block.text, title="Agent Response", border_style="green"))


def display_session_stats(stats: Dict[str, Any]):
    """Display session statistics in a formatted table."""

    stats_table = Table(title="📊 Session Statistics", title_style="bold blue")
    stats_table.add_column("Metric", style="cyan", no_wrap=True)
    stats_table.add_column("Value", style="yellow")

    stats_table.add_row("Session ID", stats.get("session_id", "N/A"))
    stats_table.add_row("Duration", f"{stats.get('duration_ms', 0)}ms")
    stats_table.add_row("API Duration", f"{stats.get('duration_api_ms', 0)}ms")
    stats_table.add_row("Turns", str(stats.get("num_turns", 0)))

    if stats.get("total_cost_usd"):
        cost = f"${stats['total_cost_usd']:.6f}"
    else:
        cost = "N/A"
    stats_table.add_row("Cost", cost)

    console.print(stats_table)


class QAAgentREPL:
    """Interactive REPL for the QA Agent."""

    def __init__(self):
        """Initialize the QA Agent REPL."""

        self.client: Optional[ClaudeSDKClient] = None
        self.session_id: Optional[str] = None
        self.session_stats: Dict[str, Any] = {}
        self.conversation_count = 0

        # Load configurations
        self.system_prompt = load_system_prompt()
        self.mcp_config_path = load_mcp_config()

        # Setup allowed and disallowed tools
        self.allowed_tools = [
            "Read",
            "WebSearch",
            "WebFetch",
            "Bash",
            "Task",
            "Glob",
            "Grep",
        ]

        # Add Firecrawl tools if MCP is configured
        if self.mcp_config_path:
            self.allowed_tools.extend(
                [
                    "mcp__firecrawl-mcp__firecrawl_scrape",
                    "mcp__firecrawl-mcp__firecrawl_search",
                    "mcp__firecrawl-mcp__firecrawl_crawl",
                ]
            )

        # Explicitly disallow all editing tools
        self.disallowed_tools = [
            "Edit",
            "MultiEdit",
            "Write",
            "NotebookEdit",
            "TodoWrite",
            "ExitPlanMode",
            "BashOutput",
            "KillShell",
        ]

    async def initialize_client(self, resume_session: Optional[str] = None):
        """Initialize or reinitialize the Claude SDK client."""

        # Close existing client if any
        if self.client:
            await self.client.disconnect()

        # Configure inline hooks for security
        hooks = {
            "PreToolUse": [
                HookMatcher(matcher="Read|Grep|Bash", hooks=[block_env_files]),
                HookMatcher(hooks=[log_tool_usage]),  # Applies to all tools
            ],
            "PostToolUse": [HookMatcher(hooks=[log_tool_usage])],
        }

        # Configure options
        options = ClaudeAgentOptions(
            system_prompt=self.system_prompt,
            allowed_tools=self.allowed_tools,
            disallowed_tools=self.disallowed_tools,
            model="sonnet",  # Claude fast model
            resume=resume_session,  # Resume previous session if provided
            hooks=hooks,  # Inline hooks for security (works for subagents!)
        )

        # Add MCP server configuration if available
        if self.mcp_config_path:
            options.mcp_servers = self.mcp_config_path

        # Create new client
        self.client = ClaudeSDKClient(options)
        await self.client.connect()

        console.print("[green]✓ Client initialized with hook-based security[/green]")
        console.print()

    async def process_query(self, query: str):
        """Process a query using the QA Agent."""

        if not self.client:
            console.print("[red]Error: Client not initialized![/red]")
            return

        self.conversation_count += 1

        # Display the user's prompt in a panel
        console.print(Panel(query, title="User Prompt", border_style="yellow"))

        # Show processing indicator
        with console.status("[cyan]Processing query...[/cyan]", spinner="dots"):
            # Wrap in /qa_agent command if not already a command
            if not query.startswith("/"):
                query = f"/qa_agent {query}"

            # Send the query
            await self.client.query(query, session_id=self.session_id)

        # Track tool uses to match with results
        tool_use_map = {}

        async for message in self.client.receive_response():

            # Handle different message types
            if isinstance(message, AssistantMessage):
                # Process each content block
                for block in message.content:
                    if isinstance(block, TextBlock):
                        display_text(block)
                    elif isinstance(block, ToolUseBlock):
                        display_tool_use(block)
                        # Store tool name for result display
                        tool_use_map[block.id] = block.name
                    elif isinstance(block, ToolResultBlock):
                        # Pass tool name if available
                        tool_name = tool_use_map.get(block.tool_use_id)
                        display_tool_result(block, tool_name)
                    elif isinstance(block, ThinkingBlock):
                        display_thinking(block)

            elif isinstance(message, SystemMessage):
                # Display system messages
                console.print(
                    Panel(
                        Text(str(message), style="dim"),
                        title="[dim]System Message[/dim]",
                        border_style="dim",
                    )
                )

            elif isinstance(message, ResultMessage):
                # Store session information
                self.session_id = message.session_id
                self.session_stats = {
                    "session_id": message.session_id,
                    "duration_ms": message.duration_ms,
                    "duration_api_ms": message.duration_api_ms,
                    "num_turns": message.num_turns,
                    "total_cost_usd": message.total_cost_usd,
                    "is_error": message.is_error,
                }

    async def run(self):
        """Run the interactive REPL."""

        display_startup_banner()

        # Initialize client
        await self.initialize_client()

        console.print("[dim]Type '/help' for commands, '/exit' to quit[/dim]\n")

        # Main REPL loop
        while True:
            try:
                # Get user input
                user_input = Prompt.ask(
                    f"[bold cyan]QA[{self.conversation_count}][/bold cyan]"
                )

                # Handle special commands
                if user_input.lower() in ["/exit", "exit", "quit", "/quit"]:
                    console.print("\n[yellow]Goodbye! 👋[/yellow]")
                    break

                elif user_input.lower() in ["/help", "help"]:
                    display_help()
                    continue

                elif user_input.lower() == "/stats":
                    if self.session_stats:
                        display_session_stats(self.session_stats)
                    else:
                        console.print(
                            "[yellow]No session statistics available yet[/yellow]"
                        )
                    continue

                elif user_input.lower() == "/clear":
                    # Reinitialize client to clear conversation
                    console.print("[yellow]Clearing conversation history...[/yellow]")
                    await self.initialize_client()
                    self.conversation_count = 0
                    self.session_stats = {}
                    console.print("[green]✓ Conversation cleared[/green]")
                    continue

                elif not user_input.strip():
                    continue

                # Process the query
                await self.process_query(user_input)

                # Show brief stats after each query
                if self.session_stats:
                    console.print()
                    console.print(
                        f"[dim]Duration: {self.session_stats.get('duration_ms', 0)}ms | "
                        f"Cost: ${self.session_stats.get('total_cost_usd', 0):.6f}[/dim]"
                    )
                console.print()

            except KeyboardInterrupt:
                console.print("\n[yellow]Use '/exit' to quit properly[/yellow]")
                continue

            except Exception as e:
                console.print(
                    Panel(
                        f"[red]Error: {str(e)}[/red]",
                        title="[red]Exception[/red]",
                        border_style="red",
                    )
                )

        # Clean up
        if self.client:
            await self.client.disconnect()
            console.print("[dim]Client disconnected[/dim]")


async def main():
    """Main entry point for the QA Agent."""

    repl = QAAgentREPL()

    try:
        await repl.run()
    except Exception as e:
        console.print(
            Panel(
                f"[red]Fatal error: {str(e)}[/red]",
                title="[red]Error[/red]",
                border_style="red",
            )
        )
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
