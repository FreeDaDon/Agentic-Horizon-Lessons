"""
Offline tests for how start_be.sh and start_fe.sh load .env.

Runs each script's real .env-loading block under bash against a scratch .env;
the servers are never started.
"""

import re
import subprocess
from pathlib import Path

import pytest

APP_DIR = Path(__file__).parent.parent.parent


@pytest.mark.parametrize("script", ["start_be.sh", "start_fe.sh"])
def test_env_values_with_quotes_and_spaces_survive(script, tmp_path):
    text = (APP_DIR / script).read_text()
    subprocess.run(["bash", "-n", str(APP_DIR / script)], check=True)
    block = re.search(r"^# Load environment variables.*?^fi$", text, re.S | re.M).group(0)
    (tmp_path / "load.sh").write_text(block)
    (tmp_path / ".env").write_text(
        '# comment\nFAST_MODEL="claude haiku"\nCORS_ORIGINS=http://a:1,http://b:2\n'
    )

    out = subprocess.run(
        # $0 is the script path, so the block reads ./.env from tmp_path
        ["bash", "-c", '. ./load.sh; printf "%s|%s" "$FAST_MODEL" "$CORS_ORIGINS"', f"./{script}"],
        cwd=tmp_path, capture_output=True, text=True, check=True,
    )

    assert out.stdout == "claude haiku|http://a:1,http://b:2"
