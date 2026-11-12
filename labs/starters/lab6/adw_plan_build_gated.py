# /// script
# dependencies = ["claude-agent-sdk"]
# ///
"""Plan then build by shelling out to Claude Code twice."""

import subprocess
import sys

prompt = sys.argv[1]
subprocess.run(["claude", "-p", f"/plan {prompt}", "--dangerously-skip-permissions"], check=True)
subprocess.run(["claude", "-p", "/build specs/latest.md", "--dangerously-skip-permissions"], check=True)
