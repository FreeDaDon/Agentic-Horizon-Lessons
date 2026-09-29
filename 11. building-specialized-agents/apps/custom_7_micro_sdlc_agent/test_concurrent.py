#!/usr/bin/env python3
"""
Test concurrent workflow execution
Demonstrates that multiple agents can run simultaneously
"""

import asyncio
import aiohttp
import json
from rich.console import Console
from rich.table import Table
from rich.live import Live
import time

console = Console()
API_URL = "http://127.0.0.1:8001"


async def create_ticket(session, title, prompt):
    """Create a new ticket"""

    data = {
        "title": title,
        "content_user_request_prompt": prompt,
        "model": "claude-sonnet-4-20250514",
        "parent_codebase_path": "."
    }

    async with session.post(f"{API_URL}/tickets", json=data) as resp:
        return await resp.json()


async def move_to_plan(session, ticket_id):
    """Move ticket to plan stage to start workflow"""

    data = {"stage": "plan"}

    async with session.put(f"{API_URL}/tickets/{ticket_id}/stage", json=data) as resp:
        return await resp.json()


async def get_workflow_status(session):
    """Get current workflow status"""

    async with session.get(f"{API_URL}/workflows/status") as resp:
        return await resp.json()


async def get_ticket(session, ticket_id):
    """Get ticket details"""

    async with session.get(f"{API_URL}/tickets/{ticket_id}") as resp:
        return await resp.json()


async def monitor_workflows(tickets):
    """Monitor the progress of workflows"""

    async with aiohttp.ClientSession() as session:
        with Live(console=console, refresh_per_second=2) as live:
            completed = []
            start_time = time.time()

            while len(completed) < len(tickets):
                # Get workflow status
                status = await get_workflow_status(session)

                # Get ticket details
                ticket_details = []
                for ticket_id in tickets:
                    ticket = await get_ticket(session, ticket_id)
                    ticket_details.append(ticket)

                    if ticket['stage'] in ['shipped', 'errored'] and ticket_id not in completed:
                        completed.append(ticket_id)

                # Create status table
                table = Table(title="🚀 Concurrent Workflow Status", show_header=True)
                table.add_column("Ticket ID", style="cyan")
                table.add_column("Title", style="white")
                table.add_column("Stage", style="yellow")
                table.add_column("Messages", style="green")
                table.add_column("Tools", style="blue")

                for ticket in ticket_details:
                    stage_emoji = {
                        'plan': '📋',
                        'build': '🔨',
                        'review': '📝',
                        'shipped': '✅',
                        'errored': '❌',
                        'idle': '⏸️'
                    }.get(ticket['stage'], '❓')

                    total_msgs = (
                        ticket.get('total_plan_messages', 0) +
                        ticket.get('total_build_messages', 0) +
                        ticket.get('total_review_messages', 0)
                    )

                    total_tools = (
                        ticket.get('total_plan_tool_calls', 0) +
                        ticket.get('total_build_tool_calls', 0) +
                        ticket.get('total_review_tool_calls', 0)
                    )

                    table.add_row(
                        f"#{ticket['id']}",
                        ticket['title'][:30],
                        f"{stage_emoji} {ticket['stage']}",
                        str(total_msgs),
                        str(total_tools)
                    )

                table.add_row(
                    "",
                    f"[dim]Running: {status['running_count']} | Completed: {len(completed)}/{len(tickets)}[/dim]",
                    f"[dim]Time: {int(time.time() - start_time)}s[/dim]",
                    "",
                    ""
                )

                live.update(table)

                await asyncio.sleep(1)

        console.print(f"[green]✅ All workflows completed in {int(time.time() - start_time)} seconds![/green]")


async def main():
    """Create multiple tickets and run them concurrently"""

    console.print("[bold cyan]Testing Concurrent Workflow Execution[/bold cyan]\n")

    # Test tickets
    test_tickets = [
        ("Test Task 1", "Write a simple Python function that calculates fibonacci numbers"),
        ("Test Task 2", "Create a basic REST API endpoint for user management"),
        ("Test Task 3", "Implement a binary search algorithm in Python")
    ]

    async with aiohttp.ClientSession() as session:
        # Create tickets
        console.print("[yellow]Creating test tickets...[/yellow]")
        ticket_ids = []

        for title, prompt in test_tickets:
            ticket = await create_ticket(session, title, prompt)
            ticket_ids.append(ticket['id'])
            console.print(f"  ✅ Created ticket #{ticket['id']}: {title}")

        console.print(f"\n[yellow]Starting all {len(ticket_ids)} workflows simultaneously...[/yellow]")

        # Start all workflows at once
        tasks = []
        for ticket_id in ticket_ids:
            task = asyncio.create_task(move_to_plan(session, ticket_id))
            tasks.append(task)

        # Wait for all to start
        await asyncio.gather(*tasks)

        console.print("[green]✅ All workflows started![/green]\n")

    # Monitor progress
    await monitor_workflows(ticket_ids)


if __name__ == "__main__":
    try:
        console.print("\n[dim]Make sure the backend is running at http://127.0.0.1:8001[/dim]\n")
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Test interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[dim]Is the backend running?[/dim]")