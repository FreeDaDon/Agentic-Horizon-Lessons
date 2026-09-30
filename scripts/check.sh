#!/usr/bin/env bash
# Offline checks for the lesson apps: no API keys, no database, no network beyond package installs.
# CI runs exactly this script; run it locally the same way: scripts/check.sh
#
# Not covered here, because they need services or keys:
#   - orchestrator_3_stream tests/test_database.py (PostgreSQL via DATABASE_URL)
#   - nile/server tests (ANTHROPIC_API_KEY)
#   - test_agent_events.py, test_display.py, test_websocket_raw.py, and micro_sdlc test_concurrent.py
#     / test_websocket.py
#     (scripts that drive a running server; pytest collects nothing from most of them)
set -euo pipefail
cd "$(dirname "$0")/.."

# Keys in the calling shell must never reach a test.
unset ANTHROPIC_API_KEY OPENAI_API_KEY TYPESAFE_API_KEY OPENROUTER_API_KEY

step() { printf '\n==> %s\n' "$*"; }

step "Parse every tracked Python file"
git ls-files -z '*.py' | python3 -c '
import ast, sys
files = sys.stdin.read().split("\0")[:-1]
for f in files:
    ast.parse(open(f, encoding="utf-8").read(), f)
print(f"{len(files)} files parsed")
'

# Tests must not modify the working tree (tracked or untracked files).
tree_before=$(git status --porcelain)

pytest_app() {
  local dir=$1; shift
  step "pytest: $dir"
  (cd "$dir" && uv run --frozen --quiet --with pytest --with pytest-asyncio \
    pytest -q -p no:cacheprovider --disable-warnings "$@")
}

for lesson in "13. agent-experts" "14.orchestrator-agent-with-adws-singularity"; do
  pytest_app "$lesson/apps/orchestrator_3_stream/backend" \
    tests/test_slash_command_discovery.py tests/test_autocomplete_agent.py tests/test_autocomplete_endpoints.py
done

pytest_app "11. building-specialized-agents/apps/custom_7_micro_sdlc_agent/backend" tests

step "pytest: tests/ (repo-level guard hook tests)"
uv run --no-project --quiet --with pytest pytest -q -p no:cacheprovider tests

step "Tests left the working tree unchanged"
tree_after=$(git status --porcelain)
if [[ "$tree_before" != "$tree_after" ]]; then
  echo "the tests changed these paths:"
  diff <(echo "$tree_before") <(echo "$tree_after") || true
  exit 1
fi

step "All offline checks passed"
