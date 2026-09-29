"""Session storage layer for persisting Pomodoro session data."""

import json
from pathlib import Path
from typing import List

from models import PomodoroSession, SessionStats, SessionStatus


class SessionStorage:
    """Handles persistence of Pomodoro session data to JSON."""

    def __init__(self, storage_file: Path):
        """Initialize storage with a file path.

        Args:
            storage_file: Path to the JSON storage file
        """
        self.storage_file = storage_file
        self._ensure_storage_file()

    def _ensure_storage_file(self) -> None:
        """Create storage directory and file if they don't exist."""
        # Create parent directory if it doesn't exist
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)

        # Create empty sessions file if it doesn't exist
        if not self.storage_file.exists():
            self._write_sessions([])

    def _read_sessions(self) -> List[PomodoroSession]:
        """Read all sessions from storage file.

        Returns:
            List of PomodoroSession objects
        """
        try:
            with open(self.storage_file, "r") as f:
                data = json.load(f)
                sessions_data = data.get("sessions", [])
                return [PomodoroSession.model_validate(s) for s in sessions_data]
        except (json.JSONDecodeError, FileNotFoundError):
            # If file is corrupted or missing, return empty list
            return []

    def _write_sessions(self, sessions: List[PomodoroSession]) -> None:
        """Write sessions to storage file.

        Args:
            sessions: List of PomodoroSession objects to write
        """
        data = {
            "sessions": [s.model_dump(mode="json") for s in sessions]
        }
        with open(self.storage_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def load_sessions(self) -> SessionStats:
        """Load session history and calculate statistics.

        Returns:
            SessionStats object with all sessions and computed stats
        """
        sessions = self._read_sessions()
        return self._calculate_stats(sessions)

    def save_session(self, session: PomodoroSession) -> None:
        """Append a session to the history.

        Args:
            session: PomodoroSession to save
        """
        sessions = self._read_sessions()
        sessions.append(session)
        self._write_sessions(sessions)

    def get_stats(self) -> SessionStats:
        """Calculate and return statistics for all sessions.

        Returns:
            SessionStats object with computed statistics
        """
        return self.load_sessions()

    def _calculate_stats(self, sessions: List[PomodoroSession]) -> SessionStats:
        """Calculate statistics from session list.

        Args:
            sessions: List of PomodoroSession objects

        Returns:
            SessionStats object with computed statistics
        """
        total_sessions = len(sessions)
        completed_sessions = sum(1 for s in sessions if s.status == SessionStatus.COMPLETED)

        # Calculate total focus time (only for completed sessions)
        total_focus_minutes = 0
        for session in sessions:
            if session.status == SessionStatus.COMPLETED and session.start_time and session.end_time:
                # Calculate actual time spent minus pause duration
                elapsed_seconds = (session.end_time - session.start_time).total_seconds()
                focus_seconds = elapsed_seconds - session.pause_duration_seconds
                total_focus_minutes += int(focus_seconds / 60)

        # Calculate average session duration
        avg_duration = 0.0
        if completed_sessions > 0:
            avg_duration = total_focus_minutes / completed_sessions

        return SessionStats(
            total_sessions=total_sessions,
            completed_sessions=completed_sessions,
            total_focus_time_minutes=total_focus_minutes,
            average_session_duration_minutes=avg_duration,
            sessions=sessions,
        )
