"""
Shared test fixtures.

AutocompleteAgent finds its expertise directory from its own module path
(modules/../prompts/experts/orch_autocomplete), not from working_dir, so the
temp_dir the tests pass in never isolated anything: every run rewrote the
committed expertise.yaml. This fixture points the module at a sandbox copy of
the prompts instead, for every test in this directory.
"""

import shutil
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import modules.autocomplete_agent as autocomplete_agent  # noqa: E402


@pytest.fixture(autouse=True)
def isolated_autocomplete_expertise(tmp_path, monkeypatch):
    """Run AutocompleteAgent against a copy of its prompts, without the committed expertise.yaml."""
    sandbox = tmp_path / "orchestrator_3_stream" / "backend"
    shutil.copytree(
        BACKEND_DIR / "prompts" / "experts" / "orch_autocomplete",
        sandbox / "prompts" / "experts" / "orch_autocomplete",
        ignore=shutil.ignore_patterns("expertise.yaml"),
    )
    monkeypatch.setattr(autocomplete_agent, "__file__", str(sandbox / "modules" / "autocomplete_agent.py"))
    return sandbox
