# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "asyncpg==0.30.0",
#   "python-dotenv==1.2.1",
#   "rich==14.2.0",
#   "websockets==15.0.1",
# ]
# ///
"""
ADW Manual Trigger - Manually create and trigger an ADW for testing.

This script:
1. Creates an ADW record in the database (like start_adw tool does)
2. Triggers the workflow via adw_scripts.py
3. Allows testing the complete flow without the orchestrator

Usage:
    uv run adws/adw_triggers/adw_manual_trigger.py <adw_name> <workflow_type> <prompt> <working_dir> [model]
        [--review-model M] [--fix-model M] [--max-budget-usd N] [--max-fix-rounds N]

Example:
    uv run adws/adw_triggers/adw_manual_trigger.py "test-feature" "plan_build" "Create a hello world script" "/path/to/project" "sonnet"

Arguments:
    adw_name:      Human-readable name for the ADW (e.g., "test-feature")
    workflow_type: Workflow type (maps to adw_workflows/adw_<type>.py, e.g., "plan_build")
    prompt:        The task prompt to execute
    working_dir:   Working directory for the agents
    model:         Optional model name for plan/build (default: sonnet)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

sys.path.insert(0, str(Path(__file__).parent.parent))

from adw_triggers.adw_scripts import (  # noqa: E402
    RunHandle,
    UnknownWorkflowError,
    require_workflow,
    start_workflow,
)

load_dotenv()

console = Console()


# =============================================================================
# DATABASE OPERATIONS (inline to avoid import complexity)
# =============================================================================


async def create_adw_record(
    adw_name: str,
    workflow_type: str,
    total_steps: int,
    input_data: dict,
    orchestrator_agent_id: str | None = None,
) -> str:
    """Create an ADW record in the database.

    Args:
        adw_name: Human-readable name
        workflow_type: Workflow type (already validated against discovered workflows)
        total_steps: The workflow's TOTAL_STEPS
        input_data: prompt, working_dir, models and caps (see adw_steps.AdwInput)
        orchestrator_agent_id: Optional parent orchestrator ID

    Returns:
        The created ADW ID (UUID string)
    """
    import asyncpg

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is not set")

    adw_id = str(uuid.uuid4())
    model = input_data["model"]
    prompt = input_data["prompt"]

    conn = await asyncpg.connect(database_url)
    try:
        # If no orchestrator_agent_id provided, try to find or create one
        if orchestrator_agent_id is None:
            # Try to find an existing orchestrator agent
            row = await conn.fetchrow("SELECT id FROM orchestrator_agents LIMIT 1")
            if row:
                orchestrator_agent_id = str(row["id"])
            else:
                # Create a new orchestrator agent for manual testing
                orchestrator_agent_id = str(uuid.uuid4())
                await conn.execute(
                    """
                    INSERT INTO orchestrator_agents (
                        id, name, model, status, created_at, updated_at
                    ) VALUES (
                        $1, 'manual-test-orchestrator', $2, 'idle', NOW(), NOW()
                    )
                    """,
                    uuid.UUID(orchestrator_agent_id),
                    model,
                )
                console.print(
                    f"[dim]Created orchestrator agent: {orchestrator_agent_id}[/dim]"
                )

        await conn.execute(
            """
            INSERT INTO ai_developer_workflows (
                id, orchestrator_agent_id, adw_name, workflow_type,
                description, status, total_steps, input_data, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4,
                $5, 'pending', $6, $7, NOW(), NOW()
            )
            """,
            uuid.UUID(adw_id),
            uuid.UUID(orchestrator_agent_id) if orchestrator_agent_id else None,
            adw_name,
            workflow_type,
            f"Manual trigger: {prompt[:100]}...",
            total_steps,
            json.dumps(input_data),
        )

        # Fetch the created ADW to get full record with timestamps
        adw_row = await conn.fetchrow(
            "SELECT * FROM ai_developer_workflows WHERE id = $1",
            uuid.UUID(adw_id)
        )
    finally:
        await conn.close()

    # Broadcast ADW creation via WebSocket for real-time UI updates
    if adw_row:
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from adw_modules.adw_websockets import broadcast_adw_created

            adw_data = {
                "id": str(adw_row["id"]),
                "orchestrator_agent_id": str(adw_row["orchestrator_agent_id"]) if adw_row["orchestrator_agent_id"] else None,
                "adw_name": adw_row["adw_name"],
                "workflow_type": adw_row["workflow_type"],
                "description": adw_row["description"],
                "status": adw_row["status"],
                "current_step": adw_row["current_step"],
                "completed_steps": adw_row["completed_steps"],
                "total_steps": adw_row["total_steps"],
                "input_data": adw_row["input_data"],
                "created_at": adw_row["created_at"].isoformat() if adw_row["created_at"] else None,
                "updated_at": adw_row["updated_at"].isoformat() if adw_row["updated_at"] else None,
            }
            await broadcast_adw_created(adw_data)
            console.print("[dim]Broadcasted ADW creation via WebSocket[/dim]")
        except Exception as e:
            console.print(f"[dim yellow]WebSocket broadcast failed (non-critical): {e}[/dim yellow]")

    return adw_id


# =============================================================================
# WORKFLOW TRIGGER
# =============================================================================


async def record_run(adw_id: str, handle: RunHandle) -> None:
    """Store the runner's pid and log path in the row's metadata, where cancel_adw reads them."""
    import asyncpg

    conn = await asyncpg.connect(os.environ["DATABASE_URL"])
    try:
        await conn.execute(
            """
            UPDATE ai_developer_workflows
            SET metadata = COALESCE(metadata, '{}'::jsonb) || $2::jsonb, updated_at = NOW()
            WHERE id = $1
            """,
            uuid.UUID(adw_id),
            json.dumps(handle.metadata()),
        )
    finally:
        await conn.close()


# =============================================================================
# MAIN
# =============================================================================


async def main_async(args: argparse.Namespace) -> int:
    """Validate, create the ADW row, start the workflow, record its pid. Returns an exit code."""
    try:
        workflow = require_workflow(args.workflow_type)
    except UnknownWorkflowError as e:
        console.print(f"[red]{e}[/red]")
        return 1

    if not Path(args.working_dir).is_dir():
        console.print(f"[red]Working directory does not exist: {args.working_dir}[/red]")
        return 1
    working_dir = str(Path(args.working_dir).resolve())

    input_data = {
        "prompt": args.prompt,
        "working_dir": working_dir,
        "model": args.model,
        "review_model": args.review_model,
        "fix_model": args.fix_model,
        "max_budget_usd": args.max_budget_usd,
        "max_fix_rounds": args.max_fix_rounds,
    }

    console.print(
        Panel(
            f"[bold cyan]ADW Manual Trigger[/bold cyan]\n\n"
            f"[bold]Name:[/bold] {args.adw_name}\n"
            f"[bold]Type:[/bold] {workflow.workflow_type} ({workflow.total_steps} steps)\n"
            f"[bold]Prompt:[/bold] {args.prompt[:100]}\n"
            f"[bold]Working Dir:[/bold] {working_dir}\n"
            f"[bold]Models:[/bold] plan/build={args.model} review={args.review_model} fix={args.fix_model}\n"
            f"[bold]Budget:[/bold] ${args.max_budget_usd:.2f}, up to {args.max_fix_rounds} fix rounds",
            title="Configuration",
            width=console.width,
        )
    )

    console.print("\n[cyan]Creating ADW record...[/cyan]")
    try:
        adw_id = await create_adw_record(
            adw_name=args.adw_name,
            workflow_type=workflow.workflow_type,
            total_steps=workflow.total_steps,
            input_data=input_data,
        )
        console.print(f"[green]Created ADW: {adw_id}[/green]")
    except Exception as e:
        console.print(f"[red]Failed to create ADW record: {e}[/red]")
        return 1

    console.print("\n[cyan]Starting workflow...[/cyan]")
    try:
        handle = start_workflow(adw_id, workflow.workflow_type)
        await record_run(adw_id, handle)
    except Exception as e:
        console.print(f"[red]Failed to start workflow: {e}[/red]")
        return 1

    console.print(
        Panel(
            f"[bold green]Workflow Started[/bold green]\n\n"
            f"[bold]ADW ID:[/bold] {adw_id}\n"
            f"[bold]PID:[/bold] {handle.pid}\n"
            f"[bold]Log:[/bold] {handle.log_path}\n\n"
            f"[dim]Check the database for status updates:\n"
            f"  SELECT * FROM ai_developer_workflows WHERE id = '{adw_id}';\n"
            f"  SELECT * FROM agent_logs WHERE adw_id = '{adw_id}' ORDER BY timestamp;[/dim]",
            title="Success",
            width=console.width,
        )
    )
    return 0


def main():
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="ADW Manual Trigger - Create and trigger an ADW for testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    uv run adws/adw_triggers/adw_manual_trigger.py \\
        "test-hello" "plan_build" "Create a hello world Python script" "."

    uv run adws/adw_triggers/adw_manual_trigger.py \\
        "feature-auth" "plan_build_review_fix" \\
        "Implement user authentication with JWT tokens" \\
        "/path/to/project" "opus" --review-model sonnet --max-budget-usd 30
        """,
    )
    parser.add_argument("adw_name", help="Human-readable name for the ADW (e.g., 'test-feature')")
    parser.add_argument("workflow_type", help="Workflow type (adw_workflows/adw_<type>.py, e.g., 'plan_build')")
    parser.add_argument("prompt", help="The task prompt to execute")
    parser.add_argument("working_dir", help="Working directory for the agents")
    parser.add_argument("model", nargs="?", default="sonnet", help="Model alias for plan/build (default: sonnet)")
    parser.add_argument("--review-model", default="opus", help="Model alias for /review (default: opus)")
    parser.add_argument("--fix-model", default="opus", help="Model alias for /fix (default: opus)")
    parser.add_argument("--max-budget-usd", type=float, default=20.0, help="Total ADW budget in USD (default: 20)")
    parser.add_argument("--max-fix-rounds", type=int, default=2, help="Fix/re-review rounds (default: 2)")

    args = parser.parse_args()
    sys.exit(asyncio.run(main_async(args)))


if __name__ == "__main__":
    main()
