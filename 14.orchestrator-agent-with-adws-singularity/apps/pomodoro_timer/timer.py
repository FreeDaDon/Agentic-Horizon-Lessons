"""Core timer logic for Pomodoro sessions."""

import time
from datetime import datetime
from threading import Event, Thread

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn

from models import PomodoroSession, SessionStatus
from storage import SessionStorage


class PomodoroTimer:
    """Manages Pomodoro timer countdown with pause/resume functionality."""

    def __init__(
        self, duration_minutes: int, session: PomodoroSession, storage: SessionStorage
    ):
        """Initialize timer with duration and session data.

        Args:
            duration_minutes: Total duration of the Pomodoro session in minutes
            session: PomodoroSession object to track
            storage: SessionStorage instance for persisting data
        """
        self.duration_minutes = duration_minutes
        self.session = session
        self.storage = storage
        self.console = Console()

        # Timer state
        self.total_seconds = duration_minutes * 60
        self.remaining_seconds = self.total_seconds
        self.is_paused = False
        self.is_cancelled = False
        self.pause_event = Event()
        self.pause_event.set()  # Start as not paused

    def start(self) -> None:
        """Start the timer and display countdown."""
        self.session.start_time = datetime.now()
        self.session.status = SessionStatus.RUNNING

        self.console.print(
            Panel(
                f"[bold green]Starting Pomodoro Session[/bold green]\n\n"
                f"Duration: [cyan]{self.duration_minutes} minutes[/cyan]\n"
                f"Press [yellow]Ctrl+C[/yellow] to cancel",
                expand=True,
            )
        )

        try:
            self._run_timer()
        except KeyboardInterrupt:
            self._handle_cancellation()

    def pause(self) -> None:
        """Pause the running timer."""
        if self.session.status == SessionStatus.RUNNING:
            self.is_paused = True
            self.pause_event.clear()
            self.session.paused_at = datetime.now()
            self.session.status = SessionStatus.PAUSED
            self.console.print(
                Panel("[yellow]Session Paused[/yellow]", expand=True)
            )

    def resume(self) -> None:
        """Resume a paused timer."""
        if self.session.status == SessionStatus.PAUSED and self.session.paused_at:
            # Calculate pause duration
            pause_duration = (datetime.now() - self.session.paused_at).total_seconds()
            self.session.pause_duration_seconds += int(pause_duration)

            self.is_paused = False
            self.pause_event.set()
            self.session.status = SessionStatus.RUNNING
            self.session.paused_at = None
            self.console.print(
                Panel("[green]Session Resumed[/green]", expand=True)
            )

    def cancel(self) -> None:
        """Cancel the current session."""
        self.is_cancelled = True
        self.session.status = SessionStatus.CANCELLED
        self.session.end_time = datetime.now()
        self.storage.save_session(self.session)

    def _run_timer(self) -> None:
        """Run the timer countdown loop."""
        progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(complete_style="green", finished_style="bold green"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            expand=True,
        )

        with Live(self._create_timer_panel(self.remaining_seconds, progress), refresh_per_second=1) as live:
            task = progress.add_task("Progress", total=self.total_seconds)

            while self.remaining_seconds > 0 and not self.is_cancelled:
                # Wait for pause event (will block if paused)
                self.pause_event.wait()

                time.sleep(1)
                self.remaining_seconds -= 1
                progress.update(task, completed=self.total_seconds - self.remaining_seconds)

                # Update display
                live.update(self._create_timer_panel(self.remaining_seconds, progress))

            # Timer completed
            if not self.is_cancelled and self.remaining_seconds <= 0:
                self._handle_completion()
                live.update(
                    Panel(
                        "[bold green]Session Complete! \u2713[/bold green]\n\n"
                        "Great work! Time for a break.",
                        expand=True,
                    )
                )

    def _create_timer_panel(self, remaining: int, progress: Progress) -> Panel:
        """Create Rich panel for timer display.

        Args:
            remaining: Remaining seconds
            progress: Progress bar object

        Returns:
            Rich Panel with timer information
        """
        minutes, seconds = divmod(remaining, 60)
        status_text = "[yellow]PAUSED[/yellow]" if self.is_paused else "[green]RUNNING[/green]"

        content = (
            f"[bold]Pomodoro Timer[/bold]\n\n"
            f"Duration: [cyan]{self.duration_minutes} minutes[/cyan]\n"
            f"Time Remaining: [bold yellow]{minutes:02d}:{seconds:02d}[/bold yellow]\n"
            f"Status: {status_text}\n\n"
        )

        return Panel(Group(content, progress), expand=True)

    def _handle_completion(self) -> None:
        """Handle timer completion - save session and send notification."""
        self.session.end_time = datetime.now()
        self.session.status = SessionStatus.COMPLETED
        self.session.completed = True
        self.storage.save_session(self.session)

        # Import and send notification
        try:
            from notifications import send_notification
            send_notification(
                "Pomodoro Complete!",
                "Great work! Time for a break."
            )
        except Exception as e:
            # Don't crash if notification fails
            self.console.print(f"[yellow]Note: Could not send notification: {e}[/yellow]")

    def _handle_cancellation(self) -> None:
        """Handle user cancellation via Ctrl+C."""
        self.console.print("\n")
        self.console.print(
            Panel(
                "[yellow]Session Cancelled[/yellow]\n\n"
                "Session has been cancelled and saved.",
                expand=True,
            )
        )
        self.cancel()
