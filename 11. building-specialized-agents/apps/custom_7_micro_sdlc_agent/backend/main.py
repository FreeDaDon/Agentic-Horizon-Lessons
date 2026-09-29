#!/usr/bin/env python3
"""
Micro SDLC Agent Backend
FastAPI server for managing plan, build, and review workflow
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from pathlib import Path
import json
import time

from rich.console import Console

# Import configuration
from modules.config import DEFAULT_CODEBASE_PATH, PLAN_DIRECTORY, REVIEW_DIRECTORY
from rich.panel import Panel
from rich.table import Table

# Import database functions
from db.database import (
    init_database,
    create_ticket,
    get_ticket,
    get_all_tickets,
    update_ticket_stage,
    update_ticket_plan,
    update_ticket_build,
    update_ticket_review,
    append_agent_message,
    get_session_info,
)

# Import agent orchestrator
from modules.agent_orchestrator import (
    run_planner_agent,
    run_builder_agent,
    run_reviewer_agent,
)

console = Console()


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    console.print(
        Panel.fit(
            "[bold cyan]🚀 Micro SDLC Agent Backend Starting[/bold cyan]\n"
            + "[dim]Rich logging enabled for tool calls and thinking blocks[/dim]",
            border_style="cyan",
        )
    )

    await init_database()

    # Create plan and review directories if they don't exist
    Path(PLAN_DIRECTORY).mkdir(exist_ok=True)
    Path(REVIEW_DIRECTORY).mkdir(exist_ok=True)

    console.print("[green]✅ Database initialized[/green]")
    console.print("[green]✅ Directories created[/green]")
    console.print("[green]✅ Rich console logging active[/green]")

    yield  # Server runs

    # Shutdown
    console.print("[yellow]👋 Shutting down gracefully[/yellow]")


# Create FastAPI app with lifespan
app = FastAPI(title="Micro SDLC Agent API", version="1.0.0", lifespan=lifespan)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# WebSocket connections for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        console.print(
            f"[green]✅ WebSocket client connected. Total connections: {len(self.active_connections)}[/green]"
        )

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        console.print(
            f"[yellow]👋 WebSocket client disconnected. Total connections: {len(self.active_connections)}[/yellow]"
        )

    async def send_json(self, data: dict):
        """Send JSON data to all connected clients"""
        console.print(
            f"[cyan]📤 Sending WebSocket message to {len(self.active_connections)} clients: {data.get('type', 'unknown')}[/cyan]"
        )
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception as e:
                # Connection might be closed
                console.print(f"[red]❌ Failed to send to client: {e}[/red]")
                pass


manager = ConnectionManager()


# Workflow progress tracking
class WorkflowTracker:
    def __init__(self):
        self.active_workflows: Dict[int, Dict[str, Any]] = {}

    def start_workflow(self, ticket_id: int, initial_stage: str):
        """Track a new workflow"""
        self.active_workflows[ticket_id] = {
            "current_stage": initial_stage,
            "start_time": time.time(),
            "stages_completed": []
        }

    def update_stage(self, ticket_id: int, old_stage: str, new_stage: str):
        """Update workflow stage tracking"""
        if ticket_id in self.active_workflows:
            self.active_workflows[ticket_id]["current_stage"] = new_stage
            self.active_workflows[ticket_id]["stages_completed"].append({
                "stage": old_stage,
                "completed_at": time.time()
            })

    def complete_workflow(self, ticket_id: int):
        """Mark workflow as completed"""
        if ticket_id in self.active_workflows:
            del self.active_workflows[ticket_id]

    def get_previous_stage(self, ticket_id: int) -> str:
        """Get the previous stage for accurate transition tracking"""
        if ticket_id not in self.active_workflows:
            return "unknown"

        completed = self.active_workflows[ticket_id]["stages_completed"]
        return completed[-1]["stage"] if completed else "idle"


# Initialize tracker
workflow_tracker = WorkflowTracker()


# Pydantic models
class CreateTicketRequest(BaseModel):
    title: str
    content_user_request_prompt: str
    model: str = "sonnet"
    parent_codebase_path: str = DEFAULT_CODEBASE_PATH


class UpdateTicketStageRequest(BaseModel):
    stage: str


# API Routes
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "micro-sdlc-agent"}


@app.get("/session")
async def get_session():
    """Get session information"""
    return await get_session_info()


@app.get("/workflows/status")
async def get_workflow_status():
    """Get status of all running workflows"""

    running_tasks = [
        {
            "ticket_id": int(t.get_name().split("_")[1]),
            "name": t.get_name(),
            "done": t.done(),
        }
        for t in asyncio.all_tasks()
        if t.get_name().startswith("workflow_")
    ]

    return {"running_count": len(running_tasks), "workflows": running_tasks}


@app.post("/tickets")
async def create_new_ticket(request: CreateTicketRequest):
    """Create a new ticket"""

    console.print(f"[blue]📝 Creating new ticket: {request.title}[/blue]")

    ticket_id = await create_ticket(
        title=request.title,
        content_user_request_prompt=request.content_user_request_prompt,
        model=request.model,
        parent_codebase_path=request.parent_codebase_path,
    )

    ticket = await get_ticket(ticket_id)
    console.print(f"[green]✅ Ticket created with ID: {ticket_id}[/green]")

    # Send update to all connected clients
    await manager.send_json({"type": "ticket_created", "ticket": ticket})

    return ticket


@app.get("/tickets")
async def list_tickets():
    """Get all tickets"""
    return await get_all_tickets()


@app.get("/tickets/{ticket_id}")
async def get_ticket_by_id(ticket_id: int):
    """Get a specific ticket"""

    ticket = await get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return ticket


@app.put("/tickets/{ticket_id}/stage")
async def update_stage(ticket_id: int, request: UpdateTicketStageRequest):
    """Update ticket stage and trigger appropriate agent"""

    ticket = await get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    old_stage = ticket["stage"]
    new_stage = request.stage

    # Validate stage transition
    valid_transitions = {
        "idle": ["plan", "archived"],
        "plan": [],  # Can't be moved manually
        "build": [],  # Can't be moved manually
        "review": [],  # Can't be moved manually
        "shipped": ["errored", "archived"],  # Allow shipped to errored
        "errored": ["idle", "archived"],
        "archived": ["idle"],
    }

    if old_stage not in valid_transitions:
        raise HTTPException(
            status_code=400, detail=f"Invalid current stage: {old_stage}"
        )

    if new_stage not in valid_transitions[old_stage]:
        raise HTTPException(
            status_code=400, detail=f"Cannot transition from {old_stage} to {new_stage}"
        )

    # Update stage
    await update_ticket_stage(ticket_id, new_stage)

    # If moving to plan, start the workflow
    if new_stage == "plan":
        # Create task with a name for tracking concurrent executions
        task = asyncio.create_task(run_workflow(ticket_id))
        task.set_name(f"workflow_{ticket_id}")

        console.print(f"[cyan]🚀 Started workflow task for ticket #{ticket_id}[/cyan]")

        # Log all currently running workflows
        all_tasks = [
            t for t in asyncio.all_tasks() if t.get_name().startswith("workflow_")
        ]
        console.print(f"[dim]📊 Currently running workflows: {len(all_tasks)}[/dim]")

    # Send update to all connected clients
    await manager.send_json(
        {
            "type": "stage_updated",
            "ticket_id": ticket_id,
            "old_stage": old_stage,
            "new_stage": new_stage,
        }
    )

    return {"status": "success", "new_stage": new_stage}


async def run_workflow(ticket_id: int):
    """Run the complete plan -> build -> review workflow"""

    # Callback for real-time message processing
    async def process_message_realtime(formatted_message: dict, stage: str):
        """Process messages in real-time as they stream in"""
        updated_counts = await append_agent_message(ticket_id, formatted_message, stage)
        await manager.send_json(
            {
                "type": "agent_message",
                "ticket_id": ticket_id,
                "message": formatted_message,
                "counts": updated_counts,
            }
        )

    try:
        # Get ticket
        ticket = await get_ticket(ticket_id)
        if not ticket:
            return

        # Initialize workflow tracking
        workflow_tracker.start_workflow(ticket_id, "idle")

        # Send workflow start notification
        await manager.send_json({"type": "workflow_started", "ticket_id": ticket_id})

        # ======= PLAN PHASE =======
        console.print(
            Panel.fit(
                f"[bold blue]📋 Planning: {ticket['title']}[/bold blue]",
                border_style="blue",
            )
        )

        # Update to plan stage WITH WebSocket notification
        old_stage = workflow_tracker.get_previous_stage(ticket_id)
        await update_ticket_stage(ticket_id, "plan")
        workflow_tracker.update_stage(ticket_id, old_stage, "plan")
        await manager.send_json({
            "type": "stage_updated",
            "ticket_id": ticket_id,
            "old_stage": old_stage,
            "new_stage": "plan"
        })

        # Run planner agent with session resumption if available
        plan_session_id = ticket.get("plan_claude_code_session_id")
        plan_result = await run_planner_agent(
            user_prompt=ticket["content_user_request_prompt"],
            model=ticket["model"],
            codebase_path=DEFAULT_CODEBASE_PATH,
            resume_session_id=(
                plan_session_id if plan_session_id and plan_session_id.strip() else None
            ),
            message_callback=process_message_realtime,
        )

        if not plan_result["plan_path"]:
            raise Exception("Planner failed to create a plan")

        # Update ticket with plan info
        await update_ticket_plan(
            ticket_id,
            plan_result["plan_path"],
            plan_result["plan_path"],  # For now, just store the path
            plan_result["session_id"] or "",
        )

        console.print(f"[green]✅ Plan created: {plan_result['plan_path']}[/green]")

        # ======= BUILD PHASE =======
        console.print(
            Panel.fit(
                f"[bold green]🔨 Building: {ticket['title']}[/bold green]",
                border_style="green",
            )
        )

        # Update to build stage WITH WebSocket notification
        old_stage = workflow_tracker.get_previous_stage(ticket_id)
        await update_ticket_stage(ticket_id, "build")
        workflow_tracker.update_stage(ticket_id, old_stage, "build")
        await manager.send_json({
            "type": "stage_updated",
            "ticket_id": ticket_id,
            "old_stage": old_stage,
            "new_stage": "build"
        })

        # Run builder agent with session resumption if available
        build_session_id = ticket.get("build_claude_code_session_id")
        build_result = await run_builder_agent(
            plan_path=plan_result["plan_path"],
            model=ticket["model"],
            codebase_path=DEFAULT_CODEBASE_PATH,
            resume_session_id=(
                build_session_id
                if build_session_id and build_session_id.strip()
                else None
            ),
            message_callback=process_message_realtime,
        )

        # Update ticket with build info
        await update_ticket_build(
            ticket_id, build_result["build_response"], build_result["session_id"] or ""
        )

        console.print("[green]✅ Build completed[/green]")

        # ======= REVIEW PHASE =======
        console.print(
            Panel.fit(
                f"[bold yellow]📋 Reviewing: {ticket['title']}[/bold yellow]",
                border_style="yellow",
            )
        )

        # Update to review stage WITH WebSocket notification
        old_stage = workflow_tracker.get_previous_stage(ticket_id)
        await update_ticket_stage(ticket_id, "review")
        workflow_tracker.update_stage(ticket_id, old_stage, "review")
        await manager.send_json({
            "type": "stage_updated",
            "ticket_id": ticket_id,
            "old_stage": old_stage,
            "new_stage": "review"
        })

        # Run reviewer agent with session resumption if available
        review_session_id = ticket.get("review_claude_code_session_id")
        review_result = await run_reviewer_agent(
            plan_path=plan_result["plan_path"],
            ticket_title=ticket["title"],
            model=ticket["model"],
            codebase_path=DEFAULT_CODEBASE_PATH,
            resume_session_id=(
                review_session_id
                if review_session_id and review_session_id.strip()
                else None
            ),
            message_callback=process_message_realtime,
        )

        # Update ticket with review info
        await update_ticket_review(
            ticket_id,
            review_result["review_response"],
            review_result["session_id"] or "",
        )

        console.print("[green]✅ Review completed[/green]")

        # ======= SHIPPED =======
        # Update to shipped stage WITH WebSocket notification
        old_stage = workflow_tracker.get_previous_stage(ticket_id)
        await update_ticket_stage(ticket_id, "shipped")
        workflow_tracker.update_stage(ticket_id, old_stage, "shipped")
        await manager.send_json({
            "type": "stage_updated",
            "ticket_id": ticket_id,
            "old_stage": old_stage,
            "new_stage": "shipped"
        })

        console.print(
            Panel.fit(
                f"[bold purple]🚀 Shipped: {ticket['title']}[/bold purple]",
                border_style="purple",
            )
        )

        # Complete workflow tracking
        workflow_tracker.complete_workflow(ticket_id)

        # Send workflow complete notification
        await manager.send_json(
            {"type": "workflow_completed", "ticket_id": ticket_id, "status": "shipped"}
        )

    except Exception as e:
        console.print(
            Panel.fit(
                f"[bold red]❌ Workflow Error: {e}[/bold red]", border_style="red"
            )
        )

        # Update to errored stage WITH WebSocket notification
        old_stage = workflow_tracker.get_previous_stage(ticket_id)
        await update_ticket_stage(ticket_id, "errored")
        workflow_tracker.update_stage(ticket_id, old_stage, "errored")
        await manager.send_json({
            "type": "stage_updated",
            "ticket_id": ticket_id,
            "old_stage": old_stage,
            "new_stage": "errored"
        })

        # Complete workflow tracking
        workflow_tracker.complete_workflow(ticket_id)

        # Send error notification
        await manager.send_json(
            {"type": "workflow_error", "ticket_id": ticket_id, "error": str(e)}
        )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""

    await manager.connect(websocket)

    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn

    # Display startup banner
    table = Table(
        title="Micro SDLC Agent Configuration",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    table.add_row("Backend URL", "http://127.0.0.1:8001")
    table.add_row("WebSocket URL", "ws://127.0.0.1:8001/ws")
    table.add_row("Specs Directory", f"{PLAN_DIRECTORY}/")
    table.add_row("Review Directory", f"{REVIEW_DIRECTORY}/")
    table.add_row("Database", "backend/db/sdlc.db")

    console.print(table)

    # Run the server
    uvicorn.run(app, host="127.0.0.1", port=8001)
