"""Desktop notification support for Pomodoro timer.

This module provides cross-platform notification support using platform-specific
implementations to avoid complex native dependencies:

- macOS: Uses osascript command-line utility (built-in)
- Linux: Uses notify-send command (commonly available)
- Windows: Uses plyer library (works reliably without additional dependencies)
"""

import platform
import subprocess
import shutil
from typing import Optional


def _send_notification_macos(title: str, message: str, timeout: int = 10) -> None:
    """Send notification on macOS using osascript.

    Args:
        title: Notification title
        message: Notification message body
        timeout: Timeout in seconds (not used on macOS, included for API consistency)

    Raises:
        RuntimeError: If osascript command fails
    """
    # Escape double quotes in title and message for AppleScript
    title_escaped = title.replace('"', '\\"')
    message_escaped = message.replace('"', '\\"')

    # Build AppleScript command
    script = f'display notification "{message_escaped}" with title "{title_escaped}"'

    try:
        # Run osascript with timeout to avoid hanging
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5,
            check=True
        )
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"osascript command timed out: {e}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"osascript command failed: {e.stderr}")
    except FileNotFoundError:
        raise RuntimeError("osascript command not found (required for macOS notifications)")


def _send_notification_linux(title: str, message: str, timeout: int = 10) -> None:
    """Send notification on Linux using notify-send.

    Args:
        title: Notification title
        message: Notification message body
        timeout: Timeout in seconds (converted to milliseconds for notify-send)

    Raises:
        RuntimeError: If notify-send command fails or is not installed
    """
    # Check if notify-send is available
    if not shutil.which('notify-send'):
        raise RuntimeError(
            "notify-send command not found. Please install libnotify-bin or notification-daemon "
            "(e.g., 'sudo apt-get install libnotify-bin' on Debian/Ubuntu)"
        )

    # Convert timeout to milliseconds for notify-send
    timeout_ms = timeout * 1000

    try:
        # Run notify-send with timeout
        result = subprocess.run(
            ['notify-send', '-t', str(timeout_ms), title, message],
            capture_output=True,
            text=True,
            timeout=5,
            check=True
        )
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"notify-send command timed out: {e}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"notify-send command failed: {e.stderr}")


def _send_notification_windows(title: str, message: str, timeout: int = 10) -> None:
    """Send notification on Windows using plyer.

    Args:
        title: Notification title
        message: Notification message body
        timeout: Timeout in seconds

    Raises:
        RuntimeError: If plyer notification fails
    """
    try:
        from plyer import notification

        notification.notify(
            title=title,
            message=message,
            app_name="Pomodoro Timer",
            timeout=timeout,
        )
    except ImportError as e:
        raise RuntimeError(f"plyer library not available for Windows notifications: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to send notification via plyer: {e}")


def send_notification(title: str, message: str, timeout: int = 10) -> None:
    """Send a desktop notification using platform-appropriate method.

    This function automatically detects the operating system and uses the most
    reliable notification method for that platform:
    - macOS: osascript (built-in, no dependencies)
    - Linux: notify-send (usually available)
    - Windows: plyer library (fallback)

    Args:
        title: Notification title
        message: Notification message body
        timeout: Notification timeout in seconds (default: 10)

    Raises:
        RuntimeError: If notification fails to send with platform-specific error details
        ValueError: If title or message is empty
    """
    # Validate inputs
    if not title or not message:
        raise ValueError("Title and message cannot be empty")

    # Detect platform and use appropriate notification method
    system = platform.system()

    if system == "Darwin":  # macOS
        _send_notification_macos(title, message, timeout)
    elif system == "Linux":
        _send_notification_linux(title, message, timeout)
    elif system == "Windows":
        _send_notification_windows(title, message, timeout)
    else:
        raise RuntimeError(f"Unsupported platform: {system}")
