"""
Request Guards - checks main.py applies to untrusted request input.
"""

from pathlib import Path
from typing import Iterable, Optional


def origin_allowed(origin: Optional[str], allowed_origins: Iterable[str]) -> bool:
    """
    Whether a WebSocket handshake may proceed.

    Browsers always send Origin on a WebSocket handshake, so a cross-site page
    is caught here. Non-browser clients (ADW workflow processes, test scripts)
    send none and are allowed.
    """
    return origin is None or origin in allowed_origins


def path_inside(path: str, root: str) -> Optional[Path]:
    """Resolve path (relative paths against root) and return it only if it stays inside root."""
    root_path = Path(root).resolve()
    candidate = (root_path / path).resolve()
    return candidate if candidate.is_relative_to(root_path) else None
