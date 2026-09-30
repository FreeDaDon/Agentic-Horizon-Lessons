#!/usr/bin/env python3
"""
Agent Orchestrator Module
Handles the execution of planner, builder, and reviewer agents
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
import json as json_module
from .config import PLAN_DIRECTORY, REVIEW_DIRECTORY

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    HookMatcher,
    HookContext,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
    ResultMessage,
    ThinkingBlock,
)

console = Console()


# Constants imported from config.py
MAX_THINKING_DISPLAY = 100  # Maximum characters to show for thinking content


def load_prompt(prompt_path: str, variables: Dict[str, str]) -> str:
    """Load a prompt file and replace variables"""

    # Go up to backend directory where prompts are stored
    prompt_file = Path(__file__).parent.parent / prompt_path
    with open(prompt_file, "r") as f:
        content = f.read()

    # Replace variables
    for key, value in variables.items():
        content = content.replace(f"{{{key}}}", str(value))

    return content


def is_inside_directory(file_path: str, directory: str, working_dir: str) -> bool:
    """True if file_path, resolved from the agent's working directory, lies inside directory.

    Resolving follows `..` and symlinks, so `specs/../main.py`, `specs_evil/x.md` and a
    symlink out of specs/ are all outside. `directory` must already be resolved.
    """
    return Path(working_dir, file_path).resolve().is_relative_to(directory)


def get_message_emoji(message_type: str) -> str:
    """Get emoji for message type"""

    emoji_map = {
        "text": "💬",
        "thinking": "🤔",
        "tool_use": "🔧",
        "tool_result": "📋",
        "system": "⚙️",
        "error": "❌",
        "result": "✅",
    }
    return emoji_map.get(message_type, "📝")


def log_tool_call(
    agent_name: str, tool_name: str, tool_input: Dict[str, Any], stage: str
):
    """Log a tool call with rich formatting"""
    title = f"[bold cyan]{agent_name.upper()}: {tool_name}[/bold cyan]"

    # Extract key info based on tool type
    key_info = ""
    if tool_name == "Write":
        key_info = f"📝 Writing to: {tool_input.get('file_path', 'Unknown')}"
    elif tool_name == "Read":
        key_info = f"📖 Reading: {tool_input.get('file_path', 'Unknown')}"
    elif tool_name == "Edit" or tool_name == "MultiEdit":
        key_info = f"✏️ Editing: {tool_input.get('file_path', 'Unknown')}"
    elif tool_name == "Bash":
        cmd = tool_input.get("command", "")
        if len(cmd) > 60:
            cmd = cmd[:57] + "..."
        key_info = f"💻 Command: {cmd}"
    elif tool_name == "Glob":
        key_info = f"🔍 Pattern: {tool_input.get('pattern', 'Unknown')}"
    elif tool_name == "Grep":
        key_info = f"🔎 Searching for: {tool_input.get('pattern', 'Unknown')}"
    elif tool_name == "TodoWrite":
        todos = tool_input.get("todos", [])
        key_info = f"📋 Managing {len(todos)} tasks"
    else:
        # Generic tool
        key_info = f"🔧 Parameters: {list(tool_input.keys())[:3]}"

    # Create panel with tool details
    panel_content = key_info

    console.print(Panel(panel_content, title=title, border_style="cyan", expand=True))


def log_thinking_block(agent_name: str, thinking_text: str, stage: str):
    """Log a thinking block with rich formatting"""
    title = f"[bold magenta]{agent_name.upper()}: THINKING[/bold magenta]"

    # Truncate long thinking text for display
    display_text = thinking_text.strip()
    if len(display_text) > MAX_THINKING_DISPLAY:
        display_text = display_text[: MAX_THINKING_DISPLAY - 3] + "..."

    # Show "Thinking..." if no content, otherwise show actual thinking
    if not display_text:
        panel_content = "[italic]Thinking...[/italic]"
    else:
        panel_content = f"[italic]{display_text}[/italic]"

    console.print(
        Panel(panel_content, title=title, border_style="magenta", expand=True)
    )


def format_agent_message(
    message: Any, stage: str, agent_name: str = "Agent"
) -> Dict[str, Any]:
    """Format an agent message for storage and log it"""

    emoji = ""
    content = ""
    message_type = ""

    if isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, TextBlock):
                emoji = "💬"
                content = block.text
                message_type = "text"
                # Display agent response in a rich panel
                if len(content.strip()) > 0:
                    # Determine panel color based on agent
                    if agent_name == "PLANNER":
                        border_style = "blue"
                    elif agent_name == "BUILDER":
                        border_style = "green"
                    elif agent_name == "REVIEWER":
                        border_style = "yellow"
                    else:
                        border_style = "cyan"

                    console.print(
                        Panel(
                            content,
                            title=f"{agent_name} Response",
                            border_style=border_style,
                            expand=True,
                        )
                    )
                break
            elif isinstance(block, ToolUseBlock):
                emoji = "🔧"
                content = f"Tool: {block.name} - {block.input}"
                message_type = "tool_use"
                # Log tool call with rich formatting
                log_tool_call(agent_name, block.name, block.input, stage)
                break
            elif isinstance(block, ThinkingBlock):
                emoji = "🤔"
                thinking_text = ""
                # ThinkingBlock has 'thinking' attribute in the SDK
                if hasattr(block, "thinking"):
                    thinking_text = block.thinking
                elif hasattr(block, "text"):
                    thinking_text = block.text
                elif hasattr(block, "content"):
                    thinking_text = block.content
                else:
                    thinking_text = "Thinking..."

                # Truncate for storage in agent_messages
                content = thinking_text[:MAX_THINKING_DISPLAY] + (
                    "..." if len(thinking_text) > MAX_THINKING_DISPLAY else ""
                )
                message_type = "thinking"
                # Log thinking block with rich formatting
                log_thinking_block(agent_name, thinking_text, stage)
                break
    elif isinstance(message, ResultMessage):
        emoji = "✅" if not message.is_error else "❌"
        content = message.result or "Task completed"
        message_type = "result"
        # Log result
        status_emoji = "✅" if not message.is_error else "❌"
        console.print(
            Panel.fit(
                f"{status_emoji} {agent_name.upper()}: Session completed\n[dim]Session ID: {message.session_id}[/dim]",
                border_style="green" if not message.is_error else "red",
            )
        )

    return {
        "stage": stage,
        "type": message_type,
        "emoji": emoji,
        "content": content,
        "timestamp": asyncio.get_event_loop().time(),
    }


async def run_planner_agent(
    user_prompt: str,
    model: str = "sonnet",
    codebase_path: str = ".",
    resume_session_id: Optional[str] = None,
    message_callback: Optional[callable] = None,
) -> Dict[str, Any]:
    """Run the planner agent"""

    console.print(
        Panel.fit(
            "[bold blue]🎯 Starting Planner Agent[/bold blue]", border_style="blue"
        )
    )

    # Determine working directory and construct full plan directory path
    # Always use the provided codebase_path (agents work in that directory)
    working_dir = codebase_path
    full_plan_directory = str(Path(working_dir) / PLAN_DIRECTORY)

    # Normalize the path for clarity
    full_plan_directory = str(Path(full_plan_directory).resolve())

    # Display paths in a formatted panel
    path_info = Table(show_header=False, box=None, padding=(0, 1))
    path_info.add_column("Label", style="cyan", no_wrap=True)
    path_info.add_column("Path", style="dim")
    path_info.add_row("📂 Working directory:", str(working_dir))
    path_info.add_row("📂 Plan output directory:", str(full_plan_directory))

    console.print(
        Panel(path_info, title="Planner Configuration", border_style="dim", expand=True)
    )

    # Load custom instructions to append to Claude Code's system prompt
    planner_custom_instructions = load_prompt(
        "system_prompts/PLANNER_AGENT_SYSTEM_PROMPT.md",
        {"PLAN_DIRECTORY": full_plan_directory},
    )

    user_prompt_text = load_prompt(
        "user_prompts/PLANNER_AGENT_USER_PROMPT.md",
        {"USER_PROMPT": user_prompt, "PLAN_OUTPUT_DIRECTORY": full_plan_directory},
    )

    # Configure hooks for Write tool restrictions (works for subagents too!)
    async def planner_write_hook(
        input_data: Dict[str, Any], tool_use_id: str | None, context: HookContext
    ) -> Dict[str, Any]:
        """Hook to control Write tool access for planner and its subagents"""
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})

        # Log tool interception in a panel
        hook_info = f"Tool: {tool_name}\nInput preview: {json_module.dumps(tool_input, indent=2)[:200]}"
        console.print(
            Panel(
                hook_info, title="🔧 Hook Intercepted", border_style="cyan", style="dim"
            )
        )

        if tool_name == "Write":
            file_path = tool_input.get("file_path", "")
            content = tool_input.get("content", "")[:100]  # First 100 chars

            write_info = Table(show_header=False, box=None, padding=(0, 1))
            write_info.add_column("Field", style="yellow", no_wrap=True)
            write_info.add_column("Value", style="white")
            write_info.add_row("Path:", file_path)
            write_info.add_row("Content preview:", f"{content}...")
            write_info.add_row("Working dir:", str(working_dir))
            write_info.add_row("Full plan dir:", str(full_plan_directory))

            console.print(
                Panel(write_info, title="📝 Write Request", border_style="yellow")
            )

            # Check if file is in the plan directory
            if not is_inside_directory(file_path, full_plan_directory, working_dir):
                console.print(
                    Panel(
                        f"Write blocked: Planner can only write to {full_plan_directory}",
                        title="❌ Permission Denied",
                        border_style="red",
                    )
                )
                return {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": f"Planner can only write to {full_plan_directory}",
                    }
                }

            console.print(
                Panel(
                    f"Allowing write to plan directory: {file_path}",
                    title="✅ Write Allowed",
                    border_style="green",
                    style="dim",
                )
            )

        # Allow all other tools
        console.print(
            Panel(
                f"Tool: {tool_name}",
                title="✅ Tool Allowed",
                border_style="green",
                style="dim",
            )
        )
        return {}  # Empty dict = allow

    # Configure hooks
    hooks = {
        "PreToolUse": [HookMatcher(hooks=[planner_write_hook])]  # Applies to all tools
    }

    # Configure system prompt to use Claude Code's default + append custom instructions
    planner_system_prompt = {
        "type": "preset",
        "preset": "claude_code",
        "append": planner_custom_instructions,
    }

    options = ClaudeAgentOptions(
        system_prompt=planner_system_prompt,
        model=model,
        cwd=working_dir,  # Use ticket's codebase path
        hooks=hooks,  # Use hooks instead of can_use_tool
        permission_mode="acceptEdits",  # Auto-accept all edits
        resume=resume_session_id,  # Reuse session if provided
    )

    if resume_session_id:
        console.print(
            Panel(
                f"Session ID: {resume_session_id}",
                title="♻️ Resuming Session",
                border_style="dim",
            )
        )

    messages = []
    plan_path = None
    session_id = None

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(user_prompt_text)

            async for message in client.receive_response():
                # Format and store message with logging
                formatted = format_agent_message(message, "plan", "PLANNER")
                if formatted["content"]:
                    messages.append(formatted)
                    # Call callback for real-time processing
                    if message_callback:
                        await message_callback(formatted, "plan")

                # Extract plan path from response
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            # Look for plan file path
                            if PLAN_DIRECTORY in block.text and ".md" in block.text:
                                # Extract path
                                lines = block.text.split("\n")
                                for line in lines:
                                    if PLAN_DIRECTORY in line and ".md" in line:
                                        plan_path = line.strip()
                                        if not plan_path.startswith(PLAN_DIRECTORY):
                                            # Extract just the path part
                                            import re

                                            match = re.search(r"specs/[\w-]+\.md", line)
                                            if match:
                                                plan_path = match.group()
                                        break

                # Get session ID
                if isinstance(message, ResultMessage):
                    session_id = message.session_id

    except Exception as e:
        console.print(
            Panel.fit(f"[bold red]❌ Planner Error: {e}[/bold red]", border_style="red")
        )
        messages.append(
            {"stage": "plan", "type": "error", "emoji": "❌", "content": str(e)}
        )

    return {"plan_path": plan_path, "messages": messages, "session_id": session_id}


async def run_builder_agent(
    plan_path: str,
    model: str = "sonnet",
    codebase_path: str = ".",
    resume_session_id: Optional[str] = None,
    message_callback: Optional[callable] = None,
) -> Dict[str, Any]:
    """Run the builder agent"""

    console.print(
        Panel.fit(
            "[bold green]🔨 Starting Builder Agent[/bold green]", border_style="green"
        )
    )

    # Determine working directory
    # Always use the provided codebase_path (agents work in that directory)
    working_dir = codebase_path

    # Construct full plan path if relative
    if not Path(plan_path).is_absolute():
        full_plan_path = str(Path(working_dir) / plan_path)
    else:
        full_plan_path = plan_path

    # Normalize the path for clarity
    full_plan_path = str(Path(full_plan_path).resolve())

    # Display paths in a formatted panel
    path_info = Table(show_header=False, box=None, padding=(0, 1))
    path_info.add_column("Label", style="cyan", no_wrap=True)
    path_info.add_column("Path", style="dim")
    path_info.add_row("📂 Working directory:", str(working_dir))
    path_info.add_row("📂 Plan file path:", str(full_plan_path))

    console.print(
        Panel(path_info, title="Builder Configuration", border_style="dim", expand=True)
    )

    # Load user prompt with full path
    user_prompt_text = load_prompt(
        "user_prompts/BUILDER_AGENT_USER_PROMPT.md", {"PATH_TO_PLAN": full_plan_path}
    )

    # Configure system prompt to use Claude Code's default
    builder_system_prompt = {
        "type": "preset",
        "preset": "claude_code",
    }

    # Configure options with session resumption for BUILDER (no write restrictions)
    options = ClaudeAgentOptions(
        system_prompt=builder_system_prompt,
        model=model,
        cwd=working_dir,  # Use ticket's codebase path
        permission_mode="bypassPermissions",
        resume=resume_session_id,  # Reuse session if provided
    )

    if resume_session_id:
        console.print(
            Panel(
                f"Session ID: {resume_session_id}",
                title="♻️ Resuming Session",
                border_style="dim",
            )
        )

    messages = []
    session_id = None
    build_output = ""

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(user_prompt_text)

            async for message in client.receive_response():
                # Format and store message with logging
                formatted = format_agent_message(message, "build", "BUILDER")
                if formatted["content"]:
                    messages.append(formatted)
                    # Capture the build output
                    if formatted["type"] == "text":
                        build_output += formatted["content"] + "\n"
                    # Call callback for real-time processing
                    if message_callback:
                        await message_callback(formatted, "build")

                # Get session ID
                if isinstance(message, ResultMessage):
                    session_id = message.session_id

    except Exception as e:
        console.print(
            Panel.fit(f"[bold red]❌ Builder Error: {e}[/bold red]", border_style="red")
        )
        messages.append(
            {"stage": "build", "type": "error", "emoji": "❌", "content": str(e)}
        )

    return {
        "build_response": build_output.strip(),
        "messages": messages,
        "session_id": session_id,
    }


async def run_reviewer_agent(
    plan_path: str,
    ticket_title: str,
    model: str = "sonnet",
    codebase_path: str = ".",
    resume_session_id: Optional[str] = None,
    message_callback: Optional[callable] = None,
) -> Dict[str, Any]:
    """Run the reviewer agent"""

    console.print(
        Panel.fit(
            "[bold yellow]📋 Starting Reviewer Agent[/bold yellow]",
            border_style="yellow",
        )
    )

    # Determine working directory and construct full review directory path
    # Always use the provided codebase_path (agents work in that directory)
    working_dir = codebase_path
    full_review_directory = str(Path(working_dir) / REVIEW_DIRECTORY)

    # Construct full plan path if relative
    if not Path(plan_path).is_absolute():
        full_plan_path = str(Path(working_dir) / plan_path)
    else:
        full_plan_path = plan_path

    # Normalize the paths for clarity
    full_review_directory = str(Path(full_review_directory).resolve())
    full_plan_path = str(Path(full_plan_path).resolve())

    # Display paths in a formatted panel
    path_info = Table(show_header=False, box=None, padding=(0, 1))
    path_info.add_column("Label", style="cyan", no_wrap=True)
    path_info.add_column("Path", style="dim")
    path_info.add_row("📂 Working directory:", str(working_dir))
    path_info.add_row("📂 Plan file path:", str(full_plan_path))
    path_info.add_row("📂 Review output directory:", str(full_review_directory))

    console.print(
        Panel(
            path_info, title="Reviewer Configuration", border_style="dim", expand=True
        )
    )

    # Load custom instructions to append to Claude Code's system prompt
    reviewer_custom_instructions = load_prompt(
        "system_prompts/REVIEWER_AGENT_SYSTEM_PROMPT.md",
        {"PATH_TO_PLAN": full_plan_path, "REVIEW_DIRECTORY": full_review_directory},
    )

    user_prompt_text = load_prompt(
        "user_prompts/REVIEWER_AGENT_USER_PROMPT.md",
        {
            "PATH_TO_PLAN": full_plan_path,
            "REVIEW_OUTPUT_DIRECTORY": full_review_directory,
        },
    )

    # Configure hooks for Write tool restrictions (works for subagents too!)
    async def reviewer_write_hook(
        input_data: Dict[str, Any], tool_use_id: str | None, context: HookContext
    ) -> Dict[str, Any]:
        """Hook to control Write tool access for reviewer and its subagents"""
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})

        if tool_name == "Write":
            file_path = tool_input.get("file_path", "")
            console.print(
                Panel(
                    f"Attempting to write to: {file_path}",
                    title="📝 Reviewer Write Request",
                    border_style="dim",
                )
            )

            # Check if file is in the full review directory
            if not is_inside_directory(file_path, full_review_directory, working_dir):
                console.print(
                    Panel(
                        f"Write blocked: Reviewer can only write to {full_review_directory}\nAttempted path: {file_path}",
                        title="❌ Permission Denied",
                        border_style="red",
                    )
                )
                return {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": f"Reviewer can only write to {full_review_directory}",
                    }
                }

            console.print(
                Panel(
                    f"Write allowed to review directory: {file_path}",
                    title="✅ Write Allowed",
                    border_style="green",
                    style="dim",
                )
            )

        return {}  # Empty dict = allow

    # Configure hooks
    hooks = {
        "PreToolUse": [HookMatcher(hooks=[reviewer_write_hook])]  # Applies to all tools
    }

    # Configure system prompt to use Claude Code's default + append custom instructions
    reviewer_system_prompt = {
        "type": "preset",
        "preset": "claude_code",
        "append": reviewer_custom_instructions,
    }

    options = ClaudeAgentOptions(
        system_prompt=reviewer_system_prompt,
        model=model,
        cwd=working_dir,  # Use ticket's codebase path
        hooks=hooks,  # Use hooks instead of can_use_tool
        permission_mode="acceptEdits",  # Auto-accept all edits
        resume=resume_session_id,  # Reuse session if provided
    )

    if resume_session_id:
        console.print(
            Panel(
                f"Session ID: {resume_session_id}",
                title="♻️ Resuming Session",
                border_style="dim",
            )
        )

    messages = []
    session_id = None
    review_output = ""

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query(user_prompt_text)

            async for message in client.receive_response():
                # Format and store message with logging
                formatted = format_agent_message(message, "review", "REVIEWER")
                if formatted["content"]:
                    messages.append(formatted)
                    # Capture the review output
                    if formatted["type"] == "text":
                        review_output += formatted["content"] + "\n"
                    # Call callback for real-time processing
                    if message_callback:
                        await message_callback(formatted, "review")

                # Get session ID
                if isinstance(message, ResultMessage):
                    session_id = message.session_id

    except Exception as e:
        console.print(
            Panel.fit(
                f"[bold red]❌ Reviewer Error: {e}[/bold red]", border_style="red"
            )
        )
        messages.append(
            {"stage": "review", "type": "error", "emoji": "❌", "content": str(e)}
        )

    return {
        "review_response": review_output.strip(),
        "messages": messages,
        "session_id": session_id,
    }
