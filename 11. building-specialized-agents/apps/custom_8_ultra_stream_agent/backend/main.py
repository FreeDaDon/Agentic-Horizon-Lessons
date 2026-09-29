"""
Ultra Stream Agent - FastAPI Backend
Dual-agent system for processing and inspecting streaming JSONL logs
"""

import asyncio
import json
import sqlite3
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager
from datetime import datetime
import argparse

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    tool,
    create_sdk_mcp_server,
    AssistantMessage,
    TextBlock,
    ThinkingBlock,
    ToolUseBlock,
    ResultMessage,
)

# Import our data types
import sys

sys.path.append(str(Path(__file__).parent.parent))
from modules.data_types import (
    ProducedLog,
    ChatMessage,
    SessionInformation,
    InspectorQueryRequest,
)

# Rich console for beautiful logging
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live

console = Console()

# Constants
TOOL_EMOJI = "🔧"

# Global variables for agent management
stream_agent_client: Optional[ClaudeSDKClient] = None
inspector_agent_client: Optional[ClaudeSDKClient] = None
active_connections: List[WebSocket] = []
db_path: str = ""  # Will be set based on script location
jsonl_file_path: str = ""
current_line_index: int = 0
lines_processed_in_session: int = 0
raw_log_cache: Dict[int, Dict[str, Any]] = (
    {}
)  # Cache raw logs by line_index to save tokens


# ============= Database Setup =============


def reset_database():
    """Reset the database by dropping all tables and recreating them"""

    console.print(Panel("⚠️  Resetting database...", style="yellow"))

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Drop all tables
    cursor.execute("DROP TABLE IF EXISTS produced_logs")
    cursor.execute("DROP TABLE IF EXISTS chat_messages")
    cursor.execute("DROP TABLE IF EXISTS session_information")

    conn.commit()
    conn.close()

    console.print(Panel("🗑️  All tables dropped", style="yellow"))

    # Now reinitialize
    init_database()

    console.print(Panel("✅ Database reset complete", style="green"))


def init_database():
    """Initialize SQLite database with required tables"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS produced_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_index INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            log_id TEXT NOT NULL,
            log_summary TEXT NOT NULL,
            log_severity TEXT NOT NULL,
            raw_data TEXT NOT NULL,
            user_id TEXT
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            message TEXT,
            produced_log TEXT,
            user_id TEXT,
            message_type TEXT NOT NULL
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS session_information (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            current_line_index INTEGER NOT NULL,
            stream_agent_session_id TEXT,
            inspector_agent_session_id TEXT
        )
    """
    )

    # Initialize session_information if not exists
    cursor.execute(
        """
        INSERT OR IGNORE INTO session_information (id, current_line_index, stream_agent_session_id, inspector_agent_session_id)
        VALUES (1, 0, '', '')
    """
    )

    conn.commit()
    conn.close()

    console.print(Panel("✅ Database initialized", style="green"))


def get_session_info() -> SessionInformation:
    """Retrieve session information from database"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM session_information WHERE id = 1")
    row = cursor.fetchone()
    conn.close()

    if row:
        return SessionInformation(
            current_line_index=row[1],
            stream_agent_session_id=row[2] or "",
            inspector_agent_session_id=row[3] or "",
        )
    return SessionInformation()


def update_session_info(session: SessionInformation):
    """Update session information in database"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE session_information
        SET current_line_index = ?, stream_agent_session_id = ?, inspector_agent_session_id = ?
        WHERE id = 1
    """,
        (
            session.current_line_index,
            session.stream_agent_session_id,
            session.inspector_agent_session_id,
        ),
    )
    conn.commit()
    conn.close()


# ============= Stream Agent Tools =============


@tool(
    "read_stream_file",
    "Read a batch of lines from JSONL file",
    {"start_line_index": int, "end_line_index": int},
)
async def read_stream_file(args: Dict[str, Any]) -> Dict[str, Any]:
    """Read lines from JSONL file efficiently"""

    global jsonl_file_path, raw_log_cache

    start = args["start_line_index"]
    end = args["end_line_index"]

    # Check if file still exists
    if not Path(jsonl_file_path).exists():
        console.print(
            Panel(
                f"Error: JSONL file no longer exists: {jsonl_file_path}",
                title=f"{TOOL_EMOJI} stream_agent: read_stream_file {TOOL_EMOJI}",
                style="red",
            )
        )
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "error": f"File not found: {jsonl_file_path}",
                            "data": [],
                            "next_index": start,
                        }
                    ),
                }
            ],
            "is_error": True,
        }

    try:
        # Use subprocess for fast line extraction
        cmd = f"sed -n '{start + 1},{end}p' {jsonl_file_path}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        lines = result.stdout.strip().split("\n") if result.stdout else []
        data = []

        for i, line in enumerate(lines):
            if line:
                try:
                    parsed = json.loads(line)
                    # Cache by line_index for token efficiency
                    raw_log_cache[start + i] = parsed
                    data.append(parsed)
                except json.JSONDecodeError:
                    # Include malformed lines as raw strings
                    error_data = {"raw": line, "error": "JSON decode failed"}
                    raw_log_cache[start + i] = error_data
                    data.append(error_data)

        # Clean up old cache entries - ONLY those already processed
        # Never delete entries >= current_line_index to prevent sync issues
        if len(raw_log_cache) > 100:
            safe_to_delete = [
                k for k in raw_log_cache.keys() if k < current_line_index - 10
            ]
            # Keep a buffer of 10 to be extra safe
            for old_key in sorted(safe_to_delete)[:-90]:  # Keep at least 90 entries
                del raw_log_cache[old_key]

        console.print(
            Panel(
                f"📖 Read lines {start}-{end}: {len(data)} logs",
                title=f"{TOOL_EMOJI} stream_agent: read_stream_file {TOOL_EMOJI}",
                style="cyan",
            )
        )

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "data": data,
                            "next_index": start + len(data),
                            "total_lines_read": len(data),
                        }
                    ),
                }
            ]
        }

    except Exception as e:
        console.print(
            Panel(
                f"Error reading stream file: {e}",
                title=f"{TOOL_EMOJI} stream_agent: read_stream_file {TOOL_EMOJI}",
                style="red",
            )
        )
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {"error": str(e), "data": [], "next_index": start}
                    ),
                }
            ],
            "is_error": True,
        }


@tool(
    "produce_summarized_log",
    "Submit a single processed log summary to the database",
    {
        "line_index": int,
        "log_id": str,
        "log_summary": str,
        "log_severity": str,  # Must be "low", "medium", or "high"
        "user_id": str,  # Optional - can be null/empty string
    },
)
async def produce_summarized_log(args: Dict[str, Any]) -> Dict[str, Any]:
    """Store a single summarized log in database and notify clients"""

    global current_line_index, raw_log_cache

    try:
        # Validate severity
        severity = args.get("log_severity", "low").lower()
        if severity not in ["low", "medium", "high"]:
            severity = "low"

        # Fetch raw data from cache using line_index
        line_index = args["line_index"]
        raw_data = raw_log_cache.get(line_index)

        if raw_data is None:
            # Critical error - this should never happen if indices are in sync
            error_msg = f"SYNC ERROR: No cached data for line_index {line_index}. Cache keys: {sorted(raw_log_cache.keys())[-10:]}"
            console.print(
                Panel(
                    error_msg,
                    title=f"{TOOL_EMOJI} stream_agent: produce_summarized_log {TOOL_EMOJI}",
                    style="red",
                )
            )
            # Store error in raw_data so we can track it
            raw_data = {"error": "cache_miss", "line_index": line_index}

        # Create ProducedLog object with clear field mapping
        produced_log = ProducedLog(
            log_index=line_index,
            log_id=args["log_id"],
            log_summary=args["log_summary"],
            log_severity=severity,
            raw_data=raw_data,
            user_id=args.get("user_id") if args.get("user_id") else None,
        )

        # Insert into database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO produced_logs (log_index, timestamp, log_id, log_summary, log_severity, raw_data, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                produced_log.log_index,
                produced_log.timestamp,
                produced_log.log_id,
                produced_log.log_summary,
                produced_log.log_severity,
                json.dumps(produced_log.raw_data),
                produced_log.user_id,
            ),
        )

        produced_log.id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Update current index
        current_line_index = max(current_line_index, produced_log.log_index + 1)

        # Update session info
        session = get_session_info()
        session.current_line_index = current_line_index
        update_session_info(session)

        # Broadcast to WebSocket clients
        await broadcast_message(
            {"type": "stream_update", "data": produced_log.model_dump()}
        )

        # Display in console with color based on severity
        color = {"high": "red", "medium": "yellow", "low": "green"}.get(
            produced_log.log_severity, "white"
        )
        console.print(
            Panel(
                f"📝 Log #{produced_log.log_index} [{produced_log.log_severity.upper()}]: {produced_log.log_summary}",
                title=f"{TOOL_EMOJI} stream_agent: produce_summarized_log {TOOL_EMOJI}",
                style=color,
            )
        )

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Successfully processed log #{produced_log.log_index}",
                }
            ]
        }

    except Exception as e:
        console.print(
            Panel(
                f"Error producing log: {e}",
                title=f"{TOOL_EMOJI} stream_agent: produce_summarized_log {TOOL_EMOJI}",
                style="red",
            )
        )
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "is_error": True,
        }


@tool(
    "create_alert_message",
    "Create an alert for high severity issues",
    {
        "alert_message": str,
        "relevant_start_index": int,
        "relevant_end_index": int,
        "user_id": str,
    },
)
async def create_alert_message(args: Dict[str, Any]) -> Dict[str, Any]:
    """Create and broadcast alert notifications"""

    try:
        alert_data = {
            "message": args["alert_message"],
            "start_index": args["relevant_start_index"],
            "end_index": args["relevant_end_index"],
            "user_id": args.get("user_id"),
            "timestamp": datetime.now().isoformat(),
        }

        # Store in chat messages as alert
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO chat_messages (timestamp, message, produced_log, user_id, message_type)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                alert_data["timestamp"],
                alert_data["message"],
                json.dumps(alert_data),
                alert_data.get("user_id"),
                "alert",
            ),
        )
        conn.commit()
        conn.close()

        # Broadcast alert as inspector_chat message so it shows in the chat
        await broadcast_message(
            {
                "type": "inspector_chat",
                "data": {
                    "id": None,
                    "timestamp": alert_data["timestamp"],
                    "message": f"🚨 ALERT: {alert_data['message']}",
                    "produced_log": alert_data,
                    "user_id": alert_data.get("user_id"),
                    "message_type": "alert",
                },
            }
        )

        console.print(
            Panel(
                f"🚨 ALERT: {args['alert_message']}",
                style="bold red",
                title=f"{TOOL_EMOJI} stream_agent: create_alert_message {TOOL_EMOJI}",
            )
        )

        return {"content": [{"type": "text", "text": "Alert created and broadcast"}]}

    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error creating alert: {str(e)}"}],
            "is_error": True,
        }


@tool("clear_context", "Clear agent context to continue processing", {})
async def clear_context(args: Dict[str, Any]) -> Dict[str, Any]:
    """Signal to clear context and reset session"""

    global lines_processed_in_session, stream_agent_client

    lines_processed_in_session = 0

    # Broadcast context clear event
    await broadcast_message(
        {
            "type": "system_status",
            "data": {
                "message": "Stream agent context cleared",
                "timestamp": datetime.now().isoformat(),
            },
        }
    )

    console.print(
        Panel(
            "🔄 Context cleared - ready for continued processing",
            title=f"{TOOL_EMOJI} stream_agent: clear_context {TOOL_EMOJI}",
            style="blue",
        )
    )

    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(
                    {
                        "end_line_index": current_line_index,
                        "message": "Context cleared successfully",
                    }
                ),
            }
        ]
    }


# ============= Inspector Agent Tools =============


@tool(
    "read_produced_log_entries",
    "Read processed logs from database",
    {"start_index": int, "end_index": int},
)
async def read_produced_log_entries(args: Dict[str, Any]) -> Dict[str, Any]:
    """Read produced logs for inspection"""

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get total count
        cursor.execute("SELECT COUNT(*) FROM produced_logs")
        total_count = cursor.fetchone()[0]

        # Get logs in range by log_index
        cursor.execute(
            """
            SELECT * FROM produced_logs
            WHERE log_index >= ? AND log_index <= ?
            ORDER BY log_index ASC
        """,
            (args["start_index"], args["end_index"]),
        )

        rows = cursor.fetchall()
        conn.close()

        logs = []
        for row in rows:
            logs.append(
                {
                    "id": row[0],
                    "log_index": row[1],
                    "timestamp": row[2],
                    "log_id": row[3],
                    "log_summary": row[4],
                    "log_severity": row[5],
                    "raw_data": json.loads(row[6]),
                    "user_id": row[7],
                }
            )

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        {
                            "logs": logs,
                            "next_index": args["end_index"],
                            "total_count": total_count,
                        }
                    ),
                }
            ]
        }

    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error reading logs: {str(e)}"}],
            "is_error": True,
        }


@tool(
    "find_logs_for_user",
    "Find all logs for a specific user",
    {"user_id": str, "limit": int, "order_by_newest_to_oldest": bool},
)
async def find_logs_for_user(args: Dict[str, Any]) -> Dict[str, Any]:
    """Search for user-specific logs"""

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        order = "DESC" if args.get("order_by_newest_to_oldest", True) else "ASC"

        cursor.execute(
            f"""
            SELECT * FROM produced_logs
            WHERE user_id = ?
            ORDER BY id {order}
            LIMIT ?
        """,
            (args["user_id"], args.get("limit", 15)),
        )

        rows = cursor.fetchall()

        # Get total count for user
        cursor.execute(
            "SELECT COUNT(*) FROM produced_logs WHERE user_id = ?", (args["user_id"],)
        )
        total_found = cursor.fetchone()[0]

        conn.close()

        logs = []
        for row in rows:
            logs.append(
                {
                    "id": row[0],
                    "log_index": row[1],
                    "timestamp": row[2],
                    "log_id": row[3],
                    "log_summary": row[4],
                    "log_severity": row[5],
                    "raw_data": json.loads(row[6]),
                    "user_id": row[7],
                }
            )

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({"logs": logs, "total_found": total_found}),
                }
            ]
        }

    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error finding user logs: {str(e)}"}],
            "is_error": True,
        }


@tool(
    "notify_engineering_team",
    "Notify engineering team of technical issues",
    {
        "alert_message": str,
        "relevant_start_index": int,
        "relevant_end_index": int,
        "user_id": str,
    },
)
async def notify_engineering_team(args: Dict[str, Any]) -> Dict[str, Any]:
    """Mock notification to engineering team"""

    notification = {
        "team": "engineering",
        "message": args["alert_message"],
        "indices": f"{args.get('relevant_start_index', 'N/A')} - {args.get('relevant_end_index', 'N/A')}",
        "user_id": args.get("user_id"),
        "timestamp": datetime.now().isoformat(),
    }

    # Broadcast notification
    await broadcast_message(
        {
            "type": "inspector_chat",
            "data": {
                "message": f"🔧 Engineering team notified: {args['alert_message']}",
                "message_type": "system",
                "timestamp": notification["timestamp"],
            },
        }
    )

    console.print(
        Panel(
            f"🔧 Engineering Team Notified\n{args['alert_message']}",
            title=f"{TOOL_EMOJI} inspector_agent: notify_engineering_team {TOOL_EMOJI}",
            style="green",
        )
    )

    return {"content": [{"type": "text", "text": "Engineering team has been notified"}]}


@tool(
    "notify_support_team",
    "Notify support team of user issues",
    {"alert_message": str, "user_id": str},
)
async def notify_support_team(args: Dict[str, Any]) -> Dict[str, Any]:
    """Mock notification to support team"""

    notification = {
        "team": "support",
        "message": args["alert_message"],
        "user_id": args.get("user_id", "Unknown"),
        "timestamp": datetime.now().isoformat(),
    }

    # Broadcast notification
    await broadcast_message(
        {
            "type": "inspector_chat",
            "data": {
                "message": f"💬 Support team notified: {args['alert_message']}",
                "message_type": "system",
                "timestamp": notification["timestamp"],
            },
        }
    )

    console.print(
        Panel(
            f"💬 Support Team Notified\nUser: {args.get('user_id', 'N/A')}\n{args['alert_message']}",
            title=f"{TOOL_EMOJI} inspector_agent: notify_support_team {TOOL_EMOJI}",
            style="blue",
        )
    )

    return {"content": [{"type": "text", "text": "Support team has been notified"}]}


# ============= WebSocket Management =============


async def broadcast_message(message: Dict[str, Any]):
    """Broadcast message to all connected WebSocket clients"""

    disconnected = []
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except:
            disconnected.append(connection)

    # Clean up disconnected clients
    for conn in disconnected:
        if conn in active_connections:
            active_connections.remove(conn)


# ============= Agent Management =============


async def initialize_stream_agent(resume_session=True):
    """Initialize the Stream Agent with tools and options"""

    global stream_agent_client

    # Get session info from database
    session_info = get_session_info()

    # Create MCP server with stream tools
    stream_server = create_sdk_mcp_server(
        name="stream_tools",
        version="1.0.0",
        tools=[
            read_stream_file,
            produce_summarized_log,  # Changed to singular
            create_alert_message,
            clear_context,
        ],
    )

    # Load system prompt
    prompt_path = (
        Path(__file__).parent.parent
        / "system_prompts"
        / "stream_agent_system_prompt.md"
    )
    with open(prompt_path, "r") as f:
        system_prompt = f.read()

    # Get session ID for resume
    session_id = (
        session_info.stream_agent_session_id
        if resume_session and session_info.stream_agent_session_id
        else None
    )

    console.print(
        Panel(
            f"🚀 Stream Agent: {('resuming session ' + session_id) if session_id else 'starting new session'}",
            title="initialize_stream_agent",
            style="cyan",
        )
    )

    # Configure options with resume if we have a session ID
    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        mcp_servers={"stream": stream_server},
        allowed_tools=[
            "mcp__stream__read_stream_file",
            "mcp__stream__produce_summarized_log",  # Changed to singular
            "mcp__stream__create_alert_message",
            "mcp__stream__clear_context",
        ],
        disallowed_tools=[
            # Disable all built-in tools - stream agent only needs custom tools
            "Read",
            "Write",
            "Edit",
            "MultiEdit",
            "NotebookEdit",
            "Glob",
            "Grep",
            "WebFetch",
            "WebSearch",
            "TodoWrite",
            "Task",
            "ExitPlanMode",
            "Bash",
            "BashOutput",
            "KillShell",
        ],
        model="claude-sonnet-4-20250514",
        resume=session_id,  # Resume existing session for continuity
    )

    stream_agent_client = ClaudeSDKClient(options=options)

    # Create streaming input format required for initial connection
    async def create_initial_message():
        # If resuming, start with the current index
        initial_prompt = str(session_info.current_line_index) if resume_session else "0"
        yield {
            "type": "user",
            "message": {"role": "user", "content": initial_prompt},
        }

    # Connect with initial message
    await stream_agent_client.connect(
        create_initial_message() if not resume_session else None
    )

    console.print(
        Panel(
            f"✅ Stream Agent initialized {'(resumed)' if session_id else '(new)'}",
            title="initialize_stream_agent",
            style="green",
        )
    )


async def initialize_inspector_agent(resume_session=True):
    """Initialize the Inspector Agent with tools and options"""

    global inspector_agent_client

    # Get session info from database
    session_info = get_session_info()

    # Create MCP server with inspector tools
    inspector_server = create_sdk_mcp_server(
        name="inspector_tools",
        version="1.0.0",
        tools=[
            read_produced_log_entries,
            find_logs_for_user,
            notify_engineering_team,
            notify_support_team,
        ],
    )

    # Load system prompt
    prompt_path = (
        Path(__file__).parent.parent
        / "system_prompts"
        / "inspector_agent_system_prompt.md"
    )
    with open(prompt_path, "r") as f:
        system_prompt = f.read()

    # Get session ID for resume
    session_id = (
        session_info.inspector_agent_session_id
        if resume_session and session_info.inspector_agent_session_id
        else None
    )

    console.print(
        Panel(
            f"🔍 Inspector Agent: {('resuming session ' + session_id) if session_id else 'starting new session'}",
            title="initialize_inspector_agent",
            style="cyan",
        )
    )

    # Configure options with resume if we have a session ID
    options = ClaudeAgentOptions(
        mcp_servers={"inspector": inspector_server},
        allowed_tools=[
            "mcp__inspector__read_produced_log_entries",
            "mcp__inspector__find_logs_for_user",
            "mcp__inspector__notify_engineering_team",
            "mcp__inspector__notify_support_team",
        ],
        disallowed_tools=[
            # Disable all built-in tools - inspector agent only needs custom tools
            "Read",
            "Write",
            "Edit",
            "MultiEdit",
            "NotebookEdit",
            "Glob",
            "Grep",
            "WebFetch",
            "WebSearch",
            "TodoWrite",
            "Task",
            "ExitPlanMode",
            "Bash",
            "BashOutput",
            "KillShell",
        ],
        system_prompt=system_prompt,
        model="claude-sonnet-4-20250514",
        resume=session_id,  # Resume existing session for continuity
    )

    inspector_agent_client = ClaudeSDKClient(options=options)
    # Don't connect immediately - connect on first query

    console.print(
        Panel(
            f"✅ Inspector Agent initialized {'(resumed)' if session_id else '(new)'}",
            style="green",
        )
    )


async def run_stream_agent():
    """Run the Stream Agent processing loop"""

    global stream_agent_client, current_line_index, lines_processed_in_session

    while stream_agent_client:
        try:
            # Send current line index to agent
            await stream_agent_client.query(str(current_line_index))

            # Process agent response
            async for message in stream_agent_client.receive_response():
                if isinstance(message, AssistantMessage):
                    # Agent will use tools automatically
                    pass
                elif isinstance(message, ResultMessage):
                    # CRITICAL: Capture session_id from ResultMessage for continuity
                    if message.session_id:
                        session_info = get_session_info()
                        if session_info.stream_agent_session_id != message.session_id:
                            session_info.stream_agent_session_id = message.session_id
                            update_session_info(session_info)
                            console.print(
                                Panel(
                                    f"✓ Stream Agent session ID updated: {message.session_id}",
                                    title="run_stream_agent",
                                    style="green",
                                )
                            )

                    # Update processed count
                    lines_processed_in_session += 5  # Approximate

                    # Check if we need to clear context
                    if lines_processed_in_session >= 50:
                        console.print(
                            Panel(
                                "Approaching context limit, clearing...",
                                title="run_stream_agent",
                                style="yellow",
                            )
                        )
                        await stream_agent_client.disconnect()
                        await initialize_stream_agent(
                            resume_session=True
                        )  # Resume after clear
                        lines_processed_in_session = 0

            # Small delay before next iteration
            await asyncio.sleep(0.5)

        except Exception as e:
            console.print(
                Panel(f"Stream agent error: {e}", title="run_stream_agent", style="red")
            )
            await asyncio.sleep(5)  # Wait before retry


async def handle_inspector_query(query: str) -> str:
    """Handle a query to the Inspector Agent"""

    global inspector_agent_client

    try:
        # Always reinitialize the inspector agent to ensure proper connection
        await initialize_inspector_agent(resume_session=True)

        if not inspector_agent_client:
            return "Inspector Agent not initialized"

        # Create streaming input format required for query
        async def create_message_generator():
            yield {
                "type": "user",
                "message": {"role": "user", "content": query},
            }

        # Use the query method with streaming format
        response = ""
        captured_session_id = None

        async with inspector_agent_client as client:
            # Send the query
            await client.query(create_message_generator())

            # Receive and collect the response
            async for msg in client.receive_response():
                # Handle assistant responses
                if isinstance(msg, AssistantMessage):
                    for content_block in msg.content:
                        if isinstance(content_block, TextBlock):
                            response += content_block.text + " "
                        elif isinstance(content_block, ThinkingBlock):
                            # Broadcast agent thinking to frontend
                            thinking_message = {
                                "id": f"thinking_{datetime.now().timestamp()}",
                                "message": content_block.thinking,
                                "message_type": "thinking",
                                "timestamp": datetime.now().isoformat(),
                            }
                            await broadcast_message(
                                {"type": "inspector_thinking", "data": thinking_message}
                            )
                        elif isinstance(content_block, ToolUseBlock):
                            # Broadcast tool use to frontend
                            tool_message = {
                                "id": f"tool_{content_block.id}",
                                "message": f"🔧 Using tool: {content_block.name}",
                                "message_type": "tool_use",
                                "timestamp": datetime.now().isoformat(),
                            }
                            await broadcast_message(
                                {"type": "inspector_tool_use", "data": tool_message}
                            )

                # CRITICAL: Capture session_id from ResultMessage for next query continuity
                elif isinstance(msg, ResultMessage):
                    if msg.session_id:
                        captured_session_id = msg.session_id
                        console.print(
                            Panel(
                                f"✓ Captured session ID: {captured_session_id}",
                                title="handle_inspector_query",
                                style="dim cyan",
                            )
                        )

            # Update session ID in database for future queries
            if captured_session_id:
                session_info = get_session_info()
                if session_info.inspector_agent_session_id != captured_session_id:
                    session_info.inspector_agent_session_id = captured_session_id
                    update_session_info(session_info)
                    console.print(
                        Panel(
                            f"✓ Inspector Agent session ID updated: {captured_session_id}",
                            title="handle_inspector_query",
                            style="green",
                        )
                    )

        return response.strip() if response else "No response from inspector agent"

    except Exception as e:
        console.print(
            Panel(
                f"Error in inspector query: {str(e)}",
                title="handle_inspector_query",
                style="red",
            )
        )
        return f"Error processing query: {str(e)}"


# ============= FastAPI Application =============


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""

    # Startup
    console.print(Panel("🚀 Starting Ultra Stream Agent", style="bold blue"))
    init_database()
    await initialize_stream_agent()
    await initialize_inspector_agent()

    # Start stream processing
    asyncio.create_task(run_stream_agent())

    yield

    # Shutdown
    if stream_agent_client:
        await stream_agent_client.disconnect()
    if inspector_agent_client:
        await inspector_agent_client.disconnect()

    console.print(Panel("👋 Ultra Stream Agent shutdown", style="bold red"))


app = FastAPI(title="Ultra Stream Agent", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============= API Endpoints =============


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "running", "agents": ["stream", "inspector"]}


@app.get("/status")
async def get_status():
    """Get current system status"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM produced_logs")
    total_logs = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM chat_messages")
    total_messages = cursor.fetchone()[0]

    conn.close()

    session = get_session_info()

    return {
        "stream_agent_active": stream_agent_client is not None,
        "inspector_agent_active": inspector_agent_client is not None,
        "current_line_index": current_line_index,
        "total_logs_processed": total_logs,
        "total_messages": total_messages,
        "session": session.model_dump(),
    }


@app.get("/logs/recent")
async def get_recent_logs(limit: int = 50):
    """Get recent processed logs"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM produced_logs
        ORDER BY id DESC
        LIMIT ?
    """,
        (limit,),
    )

    rows = cursor.fetchall()
    conn.close()

    logs = []
    for row in rows:
        logs.append(
            ProducedLog(
                id=row[0],
                log_index=row[1],
                timestamp=row[2],
                log_id=row[3],
                log_summary=row[4],
                log_severity=row[5],
                raw_data=json.loads(row[6]),
                user_id=row[7],
            ).model_dump()
        )

    return logs


@app.get("/messages/recent")
async def get_recent_messages(limit: int = 50):
    """Get recent chat messages"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM chat_messages
        ORDER BY id DESC
        LIMIT ?
    """,
        (limit,),
    )

    rows = cursor.fetchall()
    conn.close()

    messages = []
    for row in rows:
        messages.append(
            ChatMessage(
                id=row[0],
                timestamp=row[1],
                message=row[2],
                produced_log=json.loads(row[3]) if row[3] else None,
                user_id=row[4],
                message_type=row[5],
            ).model_dump()
        )

    return messages


@app.post("/inspector/query")
async def query_inspector(request: InspectorQueryRequest):
    """Send a query to the Inspector Agent"""

    # Store user query
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO chat_messages (timestamp, message, message_type)
        VALUES (?, ?, ?)
    """,
        (datetime.now().isoformat(), request.query, "user"),
    )
    conn.commit()
    conn.close()

    # Get response from Inspector Agent
    response = await handle_inspector_query(request.query)

    # Store assistant response
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO chat_messages (timestamp, message, message_type)
        VALUES (?, ?, ?)
    """,
        (datetime.now().isoformat(), response, "assistant"),
    )
    conn.commit()
    conn.close()

    return {"response": response}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection for real-time updates"""

    await websocket.accept()
    active_connections.append(websocket)

    # Send initial data
    await websocket.send_json(
        {
            "type": "connected",
            "data": {
                "message": "Connected to Ultra Stream Agent",
                "timestamp": datetime.now().isoformat(),
            },
        }
    )

    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()

            # Handle incoming messages if needed
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        active_connections.remove(websocket)


# ============= Main Entry Point =============

if __name__ == "__main__":
    # Determine correct paths based on where script is run from
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    default_data_file = project_root / "data" / "ultra_stream_agent.jsonl"

    # Set database path in backend directory
    db_path = str(script_dir / "ultra_stream.db")

    parser = argparse.ArgumentParser(description="Ultra Stream Agent Backend")
    parser.add_argument(
        "-f",
        "--file",
        default=str(default_data_file),
        help="Path to JSONL file to process",
    )
    parser.add_argument(
        "-p", "--port", type=int, default=8002, help="Port to run the server on"
    )
    parser.add_argument(
        "--reset", action="store_true", help="Reset the database and start fresh"
    )

    args = parser.parse_args()

    # Handle reset flag
    if args.reset:
        reset_database()
        console.print(Panel("🚀 Starting server with fresh database...", style="cyan"))
        # Continue to start the server with clean database

    jsonl_file_path = args.file

    # Check if JSONL file exists
    if not Path(jsonl_file_path).exists():
        console.print(
            Panel(
                f"[red]Error: JSONL file not found: {jsonl_file_path}[/red]\n\n"
                f"Please either:\n"
                f"1. Run: [cyan]uv run python generate_sample_data.py[/cyan] to create sample data\n"
                f"2. Provide a valid JSONL file path with [cyan]-f /path/to/file.jsonl[/cyan]",
                title="File Not Found",
                style="bold red",
            )
        )
        import sys

        sys.exit(1)

    # Verify it's a file and not a directory
    if not Path(jsonl_file_path).is_file():
        console.print(
            Panel(
                f"[red]Error: Path is not a file: {jsonl_file_path}[/red]",
                title="Invalid Path",
                style="bold red",
            )
        )
        import sys

        sys.exit(1)

    console.print(
        Panel(
            f"Starting server on http://127.0.0.1:{args.port}\n"
            f"Processing file: {jsonl_file_path}\n"
            f"File size: {Path(jsonl_file_path).stat().st_size / 1024:.2f} KB",
            title="Ultra Stream Agent",
            style="bold cyan",
        )
    )

    uvicorn.run(app, host="127.0.0.1", port=args.port)
