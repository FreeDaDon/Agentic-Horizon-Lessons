"""
ADW Bridge - The backend's one entry point to the lesson's ADW runner.

The runner (adws/adw_triggers/adw_scripts.py) resolves the adws directory from its own
location, so the workflow types the orchestrator offers, validates and starts are
always the ones the runner can run, whatever directory the orchestrator works in.
"""

import sys
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

ADWS_DIR = Path(__file__).resolve().parents[4] / "adws"
if str(ADWS_DIR) not in sys.path:
    sys.path.insert(0, str(ADWS_DIR))

from adw_triggers import adw_scripts  # noqa: E402
from adw_triggers.adw_scripts import (  # noqa: E402,F401
    CancelResult,
    RunHandle,
    UnknownWorkflowError,
    WorkflowInfo,
    discover_workflows,
    require_workflow,
    start_workflow,
)

from . import database  # noqa: E402


class _Rows:
    """adw_scripts.AdwRows over the backend database module."""

    async def get(self, adw_id: str) -> Optional[Dict[str, Any]]:
        return await database.get_adw(uuid.UUID(adw_id))

    async def mark_cancelled(self, adw_id: str, message: str) -> None:
        await database.update_adw_status(uuid.UUID(adw_id), "cancelled", error_message=message)


async def record_run(adw_id: str, handle: RunHandle) -> None:
    """Store the runner's pid and log path in the ADW row, where cancel_adw reads them."""
    await database.merge_adw_metadata(uuid.UUID(adw_id), handle.metadata())


async def cancel_adw(adw_id: str) -> CancelResult:
    """Stop a running ADW and mark it cancelled. Raises ValueError for a malformed id."""
    return await adw_scripts.cancel_adw(str(uuid.UUID(adw_id)), _Rows())
