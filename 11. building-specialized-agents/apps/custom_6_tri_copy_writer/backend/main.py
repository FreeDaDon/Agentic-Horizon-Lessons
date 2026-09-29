#!/usr/bin/env python3
"""
Tri-Copy-Writer Backend API

FastAPI backend that serves a copywriting interface with multiple copy variations.
Uses Claude Agent SDK to generate professional copywriting with multiple versions.
"""

import json
import asyncio
import traceback
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a rich console for beautiful terminal output
console = Console()

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    ResultMessage,
)

# ============================================================================
# CLI Configuration
# ============================================================================

# Parse command line arguments
parser = argparse.ArgumentParser(description="Tri-Copy-Writer Backend API")
parser.add_argument(
    "-v",
    "--versions",
    type=int,
    default=3,
    help="Number of copy variations to generate (default: 3)",
)

# Parse known args to allow uvicorn args to pass through
args, unknown = parser.parse_known_args()
NUMBER_OF_VERSIONS = max(1, min(args.versions, 10))  # Clamp between 1-10

# ============================================================================
# Configuration and Setup
# ============================================================================

# Track which context files have been sent per session to avoid duplicates
SESSION_CONTEXT_TRACKER = {}

app = FastAPI(
    title="Tri-Copy-Writer Backend",
    description="Backend API for copywriting interface with multiple variations using Claude Agent SDK",
    version="1.0.0",
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception handler caught: {exc}")
    logger.error(f"Exception type: {type(exc).__name__}")
    logger.error(f"Traceback: {traceback.format_exc()}")

    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Internal server error: {str(exc)}",
            "type": type(exc).__name__,
            "traceback": traceback.format_exc().split("\n")[-10:],  # Last 10 lines
        },
    )


# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load system prompt
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
SYSTEM_PROMPT_PATH = PROMPTS_DIR / "TRI_COPY_WRITER_SYSTEM_PROMPT.md"

try:
    with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
        SYSTEM_PROMPT_TEMPLATE = f.read()

    # Replace NUMBER_OF_VERSIONS placeholder
    SYSTEM_PROMPT = SYSTEM_PROMPT_TEMPLATE.replace(
        "{NUMBER_OF_VERSIONS}", str(NUMBER_OF_VERSIONS)
    )
except FileNotFoundError:
    raise FileNotFoundError(f"System prompt file not found at {SYSTEM_PROMPT_PATH}")

# ============================================================================
# Data Models
# ============================================================================


class CopyRequest(BaseModel):
    """Incoming copywriting request from frontend"""

    message: str = Field(
        ..., min_length=1, max_length=5000, description="Copywriting request"
    )
    context_files: Optional[List[Dict[str, str]]] = Field(
        default=None, description="Optional file context"
    )
    session_id: Optional[str] = Field(
        default=None, description="Session ID for conversation continuity"
    )


class CopyResponse(BaseModel):
    """Multiple copy variations from the AI"""

    primary_response: str = Field(..., description="Primary helpful explanation")
    multi_version_copy_responses: List[str] = Field(..., description="Copy variations")


class CopyWriterResponse(BaseModel):
    """Complete copywriting response with metadata"""

    copy_response: CopyResponse
    session_id: str
    duration_ms: int
    cost_usd: float | None = None
    versions_generated: int


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    message: str
    versions_configured: int


# ============================================================================
# Core Copy Generation Logic
# ============================================================================


async def generate_copy_variations(
    user_message: str,
    context_files: Optional[List[Dict[str, str]]] = None,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate copy variations from Claude Agent SDK.

    Args:
        user_message: The user's copywriting request
        context_files: Optional list of file contexts

    Returns:
        Dictionary containing the parsed response and metadata

    Raises:
        HTTPException: If Claude fails to respond or response is invalid
    """

    # Build the full prompt with context files (only add new ones)
    full_prompt = user_message

    if context_files:
        console.print(
            Panel.fit(
                Text.assemble(
                    ("📁 Context Files Received\n", "bold blue"),
                    (f"Count: {len(context_files)} file(s)", "cyan"),
                ),
                title="File Context",
                border_style="blue",
            )
        )

        # Initialize session tracking if needed
        if session_id and session_id not in SESSION_CONTEXT_TRACKER:
            SESSION_CONTEXT_TRACKER[session_id] = set()
            console.print(
                Panel.fit(
                    Text.assemble(
                        ("🆕 New Session Initialized\n", "bold green"),
                        (f"Session ID: {session_id[:8]}...", "yellow"),
                    ),
                    title="Session Management",
                    border_style="green",
                )
            )

        context_sections = []
        sent_files = (
            SESSION_CONTEXT_TRACKER.get(session_id, set()) if session_id else set()
        )

        # Track which files are new vs already sent
        new_files = []
        skipped_files = []

        for file_data in context_files:
            name = file_data.get("name", "unknown.txt")

            # Only add files that haven't been sent in this session
            if name not in sent_files:
                content = file_data.get("content", "")
                context_sections.append(f'<content name="{name}">{content}</content>')
                new_files.append(name)

                # Track that we've sent this file
                if session_id:
                    SESSION_CONTEXT_TRACKER[session_id].add(name)
            else:
                skipped_files.append(name)

        # Log summary of context handling
        if new_files or skipped_files:
            file_table = Table(
                show_header=True, title="Context File Processing", border_style="cyan"
            )
            file_table.add_column("Status", style="bold")
            file_table.add_column("Count", justify="center")
            file_table.add_column("Files")

            if new_files:
                file_table.add_row(
                    "✅ NEW", str(len(new_files)), ", ".join(new_files), style="green"
                )
            if skipped_files:
                file_table.add_row(
                    "⏭️  DUPLICATE",
                    str(len(skipped_files)),
                    ", ".join(skipped_files),
                    style="dim yellow",
                )

            console.print(file_table)

        if context_sections:
            full_prompt = "\n\n".join(context_sections) + "\n\n" + user_message
            console.print(
                Panel(
                    f"📝 Prompt includes {len(new_files)} new context section(s)",
                    title="Prompt Building",
                    border_style="cyan",
                )
            )
        else:
            console.print(
                Panel(
                    "ℹ️  No new context to add - all files already in session",
                    title="Context Status",
                    border_style="dim yellow",
                )
            )

    # Configure Claude Code options with session resumption
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        model="sonnet",
        resume=session_id,  # KEY: Resume existing session for continuity!
        disallowed_tools=[
            # Disable all built-in tools - calculator only needs custom tools
            "Read",
            "Write",
            "Edit",
            "MultiEdit",
            "NotebookEdit",  # File management
            "Glob",
            "Grep",  # Search & discovery
            "WebFetch",
            "WebSearch",  # Web tools
            "TodoWrite",
            "Task",
            "ExitPlanMode",  # Task management
            "Bash",
            "BashOutput",
            "KillShell",  # System tools
        ],
    )

    # Track response and metadata
    claude_response_text = ""
    session_metadata = {}

    try:
        # Show Claude SDK interaction starting
        console.print(
            Panel.fit(
                Text.assemble(
                    ("🤖 Invoking Claude Agent SDK\n", "bold magenta"),
                    (f"Model: sonnet\n", "cyan"),
                    (f"Session: {'Resuming' if session_id else 'New'}", "yellow"),
                ),
                title="AI Processing",
                border_style="magenta",
            )
        )

        # Create streaming input format for ClaudeSDKClient
        async def create_message_generator():
            yield {
                "type": "user",
                "message": {"role": "user", "content": full_prompt},
            }

        # Use ClaudeSDKClient with async context manager
        async with ClaudeSDKClient(options=options) as client:
            # Send query
            await client.query(create_message_generator())

            # Process responses
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    # Extract text from Claude's response
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            claude_response_text += block.text

                elif isinstance(message, ResultMessage):
                    # Capture session metadata
                    session_metadata = {
                        "session_id": message.session_id,
                        "duration_ms": message.duration_ms,
                        "cost_usd": message.total_cost_usd,
                        "versions_generated": NUMBER_OF_VERSIONS,
                    }

                    # Initialize tracking for new session if needed
                    if (
                        message.session_id
                        and message.session_id not in SESSION_CONTEXT_TRACKER
                    ):
                        SESSION_CONTEXT_TRACKER[message.session_id] = set()

                    # Clean up old sessions if we have too many (keep last 100)
                    if len(SESSION_CONTEXT_TRACKER) > 100:
                        oldest_sessions = list(SESSION_CONTEXT_TRACKER.keys())[:-100]
                        for old_session in oldest_sessions:
                            del SESSION_CONTEXT_TRACKER[old_session]

                        console.print(
                            Panel(
                                f"🧹 Cleaned up {len(oldest_sessions)} old session(s)",
                                title="Session Cleanup",
                                border_style="dim yellow",
                            )
                        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Claude Agent SDK error: {str(e)}")

    # Parse JSON response from Claude
    try:
        # Extract JSON from the response text
        cleaned_response = claude_response_text.strip()

        # Look for JSON object at the end of the response
        json_start = cleaned_response.rfind('{"primary_response":')
        if json_start == -1:
            # Try to find any JSON-like structure
            json_start = cleaned_response.rfind("{")

        if json_start != -1:
            cleaned_response = cleaned_response[json_start:]

        # Remove markdown formatting if present
        if cleaned_response.startswith("```json"):
            cleaned_response = (
                cleaned_response.replace("```json", "").replace("```", "").strip()
            )
        elif cleaned_response.startswith("```"):
            cleaned_response = cleaned_response.replace("```", "").strip()

        # Parse the JSON
        parsed_response = json.loads(cleaned_response)

        # Validate structure
        if "primary_response" not in parsed_response:
            raise ValueError("Missing 'primary_response' field in Claude response")

        if "multi_version_copy_responses" not in parsed_response:
            raise ValueError(
                "Missing 'multi_version_copy_responses' field in Claude response"
            )

        if not isinstance(parsed_response["multi_version_copy_responses"], list):
            raise ValueError("'multi_version_copy_responses' field must be a list")

        # Ensure we have the expected number of versions (allow some flexibility)
        versions = parsed_response["multi_version_copy_responses"]
        if len(versions) < 1:
            raise ValueError("Must have at least 1 copy variation")

        return {
            "copy_response": CopyResponse(
                primary_response=parsed_response["primary_response"],
                multi_version_copy_responses=versions,
            ),
            **session_metadata,
        }

    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse Claude response as JSON: {str(e)}. Raw response: {claude_response_text}...",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=500, detail=f"Invalid response structure: {str(e)}"
        )


# ============================================================================
# API Endpoints
# ============================================================================


@app.get("/config")
async def get_config():
    """Get backend configuration including number of versions"""
    return {
        "versions_configured": NUMBER_OF_VERSIONS,
        "model": "sonnet",
        "backend_name": "Tri-Copy-Writer Backend",
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="Tri-Copy-Writer Backend is running",
        versions_configured=NUMBER_OF_VERSIONS,
    )


@app.post("/copy", response_model=CopyWriterResponse)
async def copy_endpoint(copy_request: CopyRequest):
    """
    Main copywriting endpoint that returns multiple copy variations.

    Args:
        copy_request: The copywriting request with optional file context

    Returns:
        CopyWriterResponse with primary response and multiple copy variations
    """

    try:
        # Display incoming request with rich formatting
        request_info = []
        request_info.append(("📝 Request: ", "bold blue"))
        request_info.append(
            (
                f"{copy_request.message[:100]}{'...' if len(copy_request.message) > 100 else ''}\n",
                "white",
            )
        )

        if copy_request.session_id:
            request_info.append(("🔗 Session: ", "bold yellow"))
            request_info.append((f"{copy_request.session_id[:8]}...\n", "yellow"))
        else:
            request_info.append(("🔗 Session: ", "bold yellow"))
            request_info.append(("New Conversation\n", "green"))

        if copy_request.context_files:
            file_names = [f.get("name", "unknown") for f in copy_request.context_files]
            request_info.append(("📎 Files: ", "bold cyan"))
            request_info.append(
                (
                    f"{len(copy_request.context_files)} file(s) - {', '.join(file_names[:3])}",
                    "cyan",
                )
            )
            if len(file_names) > 3:
                request_info.append((f" ...+{len(file_names)-3} more", "dim cyan"))

        console.print(
            Panel.fit(
                Text.assemble(*request_info),
                title="Incoming Copy Request",
                border_style="blue",
            )
        )

        # Generate copy variations from Claude with session support
        result = await generate_copy_variations(
            copy_request.message, copy_request.context_files, copy_request.session_id
        )

        # Show success with rich formatting
        console.print(
            Panel.fit(
                Text.assemble(
                    ("✨ Copy Generation Successful\n", "bold green"),
                    (
                        f"Variations: {len(result['copy_response'].multi_version_copy_responses)}\n",
                        "cyan",
                    ),
                    (f"Duration: {result.get('duration_ms', 0)}ms\n", "yellow"),
                    (f"Cost: ${result.get('cost_usd', 0) or 0:.6f}", "magenta"),
                ),
                title="Response Generated",
                border_style="green",
            )
        )
        return CopyWriterResponse(**result)

    except HTTPException as e:
        # Re-raise HTTP exceptions as-is
        console.print(
            Panel.fit(
                Text.assemble(
                    ("❌ HTTP Error\n", "bold red"), (f"Details: {str(e)}", "red")
                ),
                title="Request Failed",
                border_style="red",
            )
        )
        raise
    except Exception as e:
        # Handle unexpected errors
        console.print(
            Panel.fit(
                Text.assemble(
                    ("❌ Unexpected Error\n", "bold red"),
                    (f"Type: {type(e).__name__}\n", "yellow"),
                    (f"Details: {str(e)}", "red"),
                ),
                title="Request Failed",
                border_style="red",
            )
        )
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with basic info"""
    return {
        "name": "Tri-Copy-Writer Backend",
        "version": "1.0.0",
        "description": "FastAPI backend for copywriting with multiple variations",
        "versions_configured": NUMBER_OF_VERSIONS,
        "endpoints": {
            "health": "/health",
            "config": "/config",
            "copy": "/copy",
            "docs": "/docs",
        },
    }


# ============================================================================
# Development Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    # Display startup banner with rich formatting
    startup_banner = Text.assemble(
        ("🚀 Tri-Copy-Writer Backend\n", "bold cyan"),
        ("✅ System Prompt Loaded\n", "green"),
        (f"📊 {NUMBER_OF_VERSIONS} Copy Variations Configured\n", "cyan"),
        (f"📁 Prompt: {SYSTEM_PROMPT_PATH.name}\n", "dim"),
        ("🌐 API: http://127.0.0.1:8000\n", "yellow"),
        ("📚 Docs: http://127.0.0.1:8000/docs", "magenta"),
    )

    console.print(
        Panel.fit(
            startup_banner,
            title="Starting Server",
            border_style="cyan",
            subtitle="Press Ctrl+C to stop",
        )
    )
    console.print()

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True, log_level="info")
