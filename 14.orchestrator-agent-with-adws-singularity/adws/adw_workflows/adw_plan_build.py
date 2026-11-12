# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "asyncpg==0.30.0",
#   "python-dotenv==1.2.1",
#   "pydantic==2.12.3",
#   "claude-agent-sdk==0.2.163",
#   "rich==14.2.0",
#   "websockets==15.0.1",
# ]
# ///
"""ADW Plan-Build Workflow - Two steps: /plan, then /build from the plan the planner submitted.

Usage:
    uv run adws/adw_workflows/adw_plan_build.py --adw-id <uuid>
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from adw_modules.adw_steps import build, plan, run_cli  # noqa: E402

TOTAL_STEPS = 2
STEPS = [plan, build]

if __name__ == "__main__":
    run_cli(STEPS, TOTAL_STEPS)
