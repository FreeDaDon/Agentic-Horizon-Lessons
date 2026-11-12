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
"""ADW Plan-Build-Gated: /plan, /build, then one /review that must pass or the ADW fails.

Usage:
    uv run adws/adw_workflows/adw_plan_build_gated.py --adw-id <uuid>
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from adw_modules.adw_steps import build, plan, review_must_pass, run_cli  # noqa: E402

TOTAL_STEPS = 3
STEPS = [plan, build, review_must_pass]

if __name__ == "__main__":
    run_cli(STEPS, TOTAL_STEPS)
