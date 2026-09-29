"""Configuration management for Pomodoro timer."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()


def get_data_dir() -> Path:
    """Get the data directory for Pomodoro timer storage.

    Returns:
        Path to the data directory
    """
    # Check for custom data directory in environment variable
    custom_dir = os.getenv("POMODORO_DATA_DIR")

    if custom_dir:
        return Path(custom_dir).expanduser()

    # Default to ~/.pomodoro_timer
    return Path.home() / ".pomodoro_timer"


def get_storage_file() -> Path:
    """Get the path to the sessions storage file.

    Returns:
        Path to sessions.json
    """
    return get_data_dir() / "sessions.json"


def get_state_file() -> Path:
    """Get the path to the current session state file.

    Returns:
        Path to current_session.json
    """
    return get_data_dir() / "current_session.json"
