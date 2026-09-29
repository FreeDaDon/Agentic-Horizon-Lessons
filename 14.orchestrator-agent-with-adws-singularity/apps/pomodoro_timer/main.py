"""Pomodoro Timer CLI application."""

import json
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config import get_state_file, get_storage_file
from models import PomodoroSession, SessionStatus
from storage import SessionStorage
from timer import PomodoroTimer

app = typer.Typer(help="Pomodoro Timer - Focus session management CLI")
console = Console()

VERSION = "0.1.0"


def save_current_session(session: PomodoroSession) -> None:
    """Save current session state to file.

    Args:
        session: PomodoroSession to save
    """
    state_file = get_state_file()
    state_file.parent.mkdir(parents=True, exist_ok=True)

    with open(state_file, "w") as f:
        json.dump(session.model_dump(mode="json"), f, indent=2, default=str)


def load_current_session() -> PomodoroSession | None:
    """Load current session state from file.

    Returns:
        PomodoroSession if found, None otherwise
    """
    state_file = get_state_file()

    if not state_file.exists():
        return None

    try:
        with open(state_file, "r") as f:
            data = json.load(f)
            return PomodoroSession.model_validate(data)
    except (json.JSONDecodeError, FileNotFoundError, ValueError):
        # Corrupted or invalid state file
        return None


def clear_current_session() -> None:
    """Clear the current session state file."""
    state_file = get_state_file()
    if state_file.exists():
        state_file.unlink()


@app.command()
def start(
    duration: int = typer.Argument(25, help="Session duration in minutes"),
) -> None:
    """Start a new Pomodoro session.

    Args:
        duration: Duration of the session in minutes (default: 25)
    """
    # Check if there's already a running or paused session
    existing_session = load_current_session()
    if existing_session and existing_session.status in (
        SessionStatus.RUNNING,
        SessionStatus.PAUSED,
    ):
        console.print(
            Panel(
                f"[yellow]Warning:[/yellow] There is already a {existing_session.status.value} session.\n"
                "Please complete or cancel it before starting a new one.",
                expand=True,
            )
        )
        raise typer.Exit(1)

    # Create new session
    session = PomodoroSession(duration_minutes=duration)
    storage = SessionStorage(get_storage_file())

    # Save session state
    save_current_session(session)

    # Start timer
    timer = PomodoroTimer(duration, session, storage)
    timer.start()

    # Clear session state after completion
    clear_current_session()


@app.command()
def pause() -> None:
    """Pause the current running session.

    Note: Currently not fully implemented in the timer loop.
    Use Ctrl+C to cancel a session instead.
    """
    session = load_current_session()

    if not session:
        console.print(
            Panel(
                "[red]Error:[/red] No active session found.\n"
                "Start a session first with [cyan]pomodoro start[/cyan]",
                expand=True,
            )
        )
        raise typer.Exit(1)

    if session.status != SessionStatus.RUNNING:
        console.print(
            Panel(
                f"[red]Error:[/red] Session is not running (status: {session.status.value}).\n"
                "Cannot pause a session that is not running.",
                expand=True,
            )
        )
        raise typer.Exit(1)

    console.print(
        Panel(
            "[yellow]Note:[/yellow] Pause/resume functionality requires running the timer in a separate process.\n"
            "For now, use [cyan]Ctrl+C[/cyan] to cancel a session.",
            expand=True,
        )
    )


@app.command()
def resume() -> None:
    """Resume a paused session.

    Note: Currently not fully implemented in the timer loop.
    Start a new session instead with the start command.
    """
    session = load_current_session()

    if not session:
        console.print(
            Panel(
                "[red]Error:[/red] No active session found.\n"
                "Start a session first with [cyan]pomodoro start[/cyan]",
                expand=True,
            )
        )
        raise typer.Exit(1)

    if session.status != SessionStatus.PAUSED:
        console.print(
            Panel(
                f"[red]Error:[/red] Session is not paused (status: {session.status.value}).\n"
                "Cannot resume a session that is not paused.",
                expand=True,
            )
        )
        raise typer.Exit(1)

    console.print(
        Panel(
            "[yellow]Note:[/yellow] Pause/resume functionality requires running the timer in a separate process.\n"
            "For now, start a new session with [cyan]pomodoro start[/cyan]",
            expand=True,
        )
    )


@app.command()
def stats() -> None:
    """Display session statistics."""
    storage = SessionStorage(get_storage_file())
    session_stats = storage.get_stats()

    # Create statistics panel
    stats_text = (
        f"[bold]Session Statistics[/bold]\n\n"
        f"Total Sessions: [cyan]{session_stats.total_sessions}[/cyan]\n"
        f"Completed Sessions: [green]{session_stats.completed_sessions}[/green]\n"
        f"Total Focus Time: [yellow]{session_stats.total_focus_time_minutes // 60}h "
        f"{session_stats.total_focus_time_minutes % 60}m[/yellow]\n"
        f"Average Session: [magenta]{session_stats.average_session_duration_minutes:.1f} minutes[/magenta]"
    )

    console.print(Panel(stats_text, expand=True))

    # Display recent sessions if any exist
    if session_stats.sessions:
        console.print("\n[bold]Recent Sessions (Last 5):[/bold]\n")

        table = Table(expand=True)
        table.add_column("Date", style="cyan")
        table.add_column("Duration", style="yellow")
        table.add_column("Status", style="green")

        # Show last 5 sessions
        for session in reversed(session_stats.sessions[-5:]):
            date_str = (
                session.start_time.strftime("%Y-%m-%d %H:%M")
                if session.start_time
                else "N/A"
            )
            duration_str = f"{session.duration_minutes} min"
            status_str = session.status.value

            # Color code status
            if session.status == SessionStatus.COMPLETED:
                status_str = f"[green]{status_str}[/green]"
            elif session.status == SessionStatus.CANCELLED:
                status_str = f"[red]{status_str}[/red]"
            else:
                status_str = f"[yellow]{status_str}[/yellow]"

            table.add_row(date_str, duration_str, status_str)

        console.print(table)
    else:
        console.print(
            Panel(
                "[yellow]No sessions yet.[/yellow]\n"
                "Start your first session with [cyan]pomodoro start[/cyan]",
                expand=True,
            )
        )


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(None, "--version", "-v", help="Show version"),
) -> None:
    """Pomodoro Timer - Manage focus sessions from your terminal."""
    if version:
        console.print(f"Pomodoro Timer version {VERSION}")
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        console.print(f"Pomodoro Timer version {VERSION}")
        console.print("Run [cyan]pomodoro --help[/cyan] for usage information")


if __name__ == "__main__":
    app()
