"""Pydantic models for Pomodoro session data."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    """Status of a Pomodoro session."""

    NOT_STARTED = "NOT_STARTED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class PomodoroSession(BaseModel):
    """Model representing a single Pomodoro session."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    duration_minutes: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    paused_at: Optional[datetime] = None
    pause_duration_seconds: int = 0
    status: SessionStatus = SessionStatus.NOT_STARTED
    completed: bool = False

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class SessionStats(BaseModel):
    """Model representing statistics across multiple sessions."""

    total_sessions: int = 0
    completed_sessions: int = 0
    total_focus_time_minutes: int = 0
    average_session_duration_minutes: float = 0.0
    sessions: List[PomodoroSession] = Field(default_factory=list)
