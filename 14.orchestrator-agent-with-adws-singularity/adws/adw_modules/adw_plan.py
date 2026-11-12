"""
ADW Plan Module - Check the plan file path an agent reported before building from it.

Usage:
    from adw_modules.adw_plan import existing_plan_path

    plan_path = existing_plan_path(submitted_path, working_dir)  # absolute path, or None
"""

from __future__ import annotations

from pathlib import Path


def existing_plan_path(candidate: str | None, working_dir: str) -> str | None:
    """Return the candidate as an absolute path if it names an existing file, else None.

    Relative paths are resolved from working_dir, where the plan agent ran. An
    agent can submit a path it never wrote; that must not reach /build.
    """
    if not candidate:
        return None
    path = Path(working_dir, candidate)
    return str(path.resolve()) if path.is_file() else None


__all__ = ["existing_plan_path"]
