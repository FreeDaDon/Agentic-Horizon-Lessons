#!/usr/bin/env python3
"""
Database module for Micro SDLC Agent
Handles SQLite database operations for tickets and session information
"""

import aiosqlite
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from modules.config import DEFAULT_CODEBASE_PATH


DATABASE_PATH = Path(__file__).parent / "sdlc.db"


async def init_database():
    """Initialize the database with required tables"""

    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Create tickets table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content_user_request_prompt TEXT NOT NULL,
                content_plan_response TEXT,
                content_build_response TEXT,
                content_review_response TEXT,
                agent_messages TEXT DEFAULT '[]',
                plan_path TEXT,
                stage TEXT DEFAULT 'idle',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                model TEXT DEFAULT 'claude-sonnet-4-20250514',
                agent TEXT DEFAULT 'claude_code',

                plan_claude_code_session_id TEXT,
                build_claude_code_session_id TEXT,
                review_claude_code_session_id TEXT,

                total_plan_messages INTEGER DEFAULT 0,
                total_build_messages INTEGER DEFAULT 0,
                total_review_messages INTEGER DEFAULT 0,

                total_plan_tool_calls INTEGER DEFAULT 0,
                total_build_tool_calls INTEGER DEFAULT 0,
                total_review_tool_calls INTEGER DEFAULT 0,

                parent_codebase_path TEXT DEFAULT '.'
            )
        """)

        # Create session_information table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS session_information (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codebase_path TEXT DEFAULT '.',
                available_codebases TEXT DEFAULT '[]',
                available_models TEXT DEFAULT '["claude-sonnet-4-20250514", "claude-opus-4-1-20250805"]'
            )
        """)

        # Insert default session if doesn't exist
        cursor = await db.execute("SELECT COUNT(*) FROM session_information")
        count = await cursor.fetchone()
        if count[0] == 0:
            await db.execute("""
                INSERT INTO session_information (codebase_path, available_codebases, available_models)
                VALUES (?, ?, ?)
            """, (".", '[".", "./apps"]', '["claude-sonnet-4-20250514", "claude-opus-4-1-20250805"]'))

        await db.commit()


async def create_ticket(
    title: str,
    content_user_request_prompt: str,
    model: str = "claude-sonnet-4-20250514",
    parent_codebase_path: str = None
) -> int:
    """Create a new ticket"""

    # Use default codebase path if not specified
    if parent_codebase_path is None:
        parent_codebase_path = DEFAULT_CODEBASE_PATH

    now = datetime.now().isoformat()

    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO tickets (
                title,
                content_user_request_prompt,
                model,
                parent_codebase_path,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (title, content_user_request_prompt, model, parent_codebase_path, now, now))

        await db.commit()
        return cursor.lastrowid


async def get_ticket(ticket_id: int) -> Optional[Dict[str, Any]]:
    """Get a ticket by ID"""

    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        row = await cursor.fetchone()

        if row:
            ticket = dict(row)
            # Parse JSON fields
            ticket['agent_messages'] = json.loads(ticket['agent_messages'])
            return ticket

        return None


async def get_all_tickets() -> List[Dict[str, Any]]:
    """Get all tickets"""

    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM tickets ORDER BY created_at DESC")
        rows = await cursor.fetchall()

        tickets = []
        for row in rows:
            ticket = dict(row)
            # Parse JSON fields
            ticket['agent_messages'] = json.loads(ticket['agent_messages'])
            tickets.append(ticket)

        return tickets


async def update_ticket_stage(ticket_id: int, stage: str) -> None:
    """Update ticket stage"""

    now = datetime.now().isoformat()

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            UPDATE tickets
            SET stage = ?, updated_at = ?
            WHERE id = ?
        """, (stage, now, ticket_id))

        await db.commit()


async def update_ticket_plan(
    ticket_id: int,
    plan_path: str,
    plan_response: str,
    session_id: str
) -> None:
    """Update ticket with plan information"""

    now = datetime.now().isoformat()

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            UPDATE tickets
            SET plan_path = ?,
                content_plan_response = ?,
                plan_claude_code_session_id = ?,
                updated_at = ?
            WHERE id = ?
        """, (plan_path, plan_response, session_id, now, ticket_id))

        await db.commit()


async def update_ticket_build(
    ticket_id: int,
    build_response: str,
    session_id: str
) -> None:
    """Update ticket with build information"""

    now = datetime.now().isoformat()

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            UPDATE tickets
            SET content_build_response = ?,
                build_claude_code_session_id = ?,
                updated_at = ?
            WHERE id = ?
        """, (build_response, session_id, now, ticket_id))

        await db.commit()


async def update_ticket_review(
    ticket_id: int,
    review_response: str,
    session_id: str
) -> None:
    """Update ticket with review information"""

    now = datetime.now().isoformat()

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            UPDATE tickets
            SET content_review_response = ?,
                review_claude_code_session_id = ?,
                updated_at = ?
            WHERE id = ?
        """, (review_response, session_id, now, ticket_id))

        await db.commit()


async def append_agent_message(
    ticket_id: int,
    message: Dict[str, Any],
    stage: str
) -> Dict[str, Any]:
    """Append a message to the agent_messages list and increment counters
    Returns the updated counts for real-time updates
    """

    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Get current messages
        cursor = await db.execute("SELECT agent_messages FROM tickets WHERE id = ?", (ticket_id,))
        row = await cursor.fetchone()

        if row:
            messages = json.loads(row[0])
            messages.append(message)

            # Update messages and increment counter for the stage
            counter_field = f"total_{stage}_messages"
            if message.get('type') == 'tool_use':
                tool_counter = f"total_{stage}_tool_calls"
                await db.execute(f"""
                    UPDATE tickets
                    SET agent_messages = ?,
                        {counter_field} = {counter_field} + 1,
                        {tool_counter} = {tool_counter} + 1,
                        updated_at = ?
                    WHERE id = ?
                """, (json.dumps(messages), datetime.now().isoformat(), ticket_id))
            else:
                await db.execute(f"""
                    UPDATE tickets
                    SET agent_messages = ?,
                        {counter_field} = {counter_field} + 1,
                        updated_at = ?
                    WHERE id = ?
                """, (json.dumps(messages), datetime.now().isoformat(), ticket_id))

            await db.commit()

            # Get updated counts to return
            cursor = await db.execute(f"""
                SELECT
                    total_plan_messages,
                    total_build_messages,
                    total_review_messages,
                    total_plan_tool_calls,
                    total_build_tool_calls,
                    total_review_tool_calls
                FROM tickets
                WHERE id = ?
            """, (ticket_id,))

            counts_row = await cursor.fetchone()
            if counts_row:
                return {
                    'total_plan_messages': counts_row['total_plan_messages'],
                    'total_build_messages': counts_row['total_build_messages'],
                    'total_review_messages': counts_row['total_review_messages'],
                    'total_plan_tool_calls': counts_row['total_plan_tool_calls'],
                    'total_build_tool_calls': counts_row['total_build_tool_calls'],
                    'total_review_tool_calls': counts_row['total_review_tool_calls']
                }

    return {}


async def get_session_info() -> Dict[str, Any]:
    """Get session information"""

    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM session_information LIMIT 1")
        row = await cursor.fetchone()

        if row:
            session = dict(row)
            # Parse JSON fields
            session['available_codebases'] = json.loads(session['available_codebases'])
            session['available_models'] = json.loads(session['available_models'])
            return session

        return {
            'codebase_path': '.',
            'available_codebases': ['.', './apps'],
            'available_models': ['claude-sonnet-4-20250514', 'claude-opus-4-1-20250805']
        }