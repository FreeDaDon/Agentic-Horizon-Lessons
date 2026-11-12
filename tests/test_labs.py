"""Every lab check passes on its reference solution and fails on its starter for the intended reasons."""

import importlib.util
import sys
from pathlib import Path

import pytest

LABS_DIR = Path(__file__).parent.parent / "labs"
SPEC = importlib.util.spec_from_file_location("check_lab", LABS_DIR / "check_lab.py")
check_lab = importlib.util.module_from_spec(SPEC)
sys.modules["check_lab"] = check_lab
SPEC.loader.exec_module(check_lab)

ARTIFACT = {
    1: ".",
    2: "backtest.md",
    3: "signal_analyst.py",
    4: ".claude/agents/data-scout.md",
    5: ".claude/commands/experts/billing/expertise.yaml",
    6: "adw_plan_build_gated.py",
}
STARTER_MUST_FAIL = {
    1: ["CLAUDE.md is about", "no default .mcp.json", "prime*.md"],
    2: ["Workflow", "STOP", "loop"],
    3: ["allowed_tools", "disallowed_tools", "bypassPermissions", "submit_"],
    4: ["read-only", "alias", "Purpose"],
    5: ["drift check is clean"],
    6: ["pinned", "STEPS", "review gate", "subprocess"],
}


@pytest.mark.parametrize("lab", sorted(ARTIFACT))
def test_reference_solution_passes_every_check(lab):
    results = check_lab.grade(lab, LABS_DIR / f"solutions/lab{lab}" / ARTIFACT[lab])
    assert [m for ok, m in results if not ok] == []


@pytest.mark.parametrize("lab", sorted(ARTIFACT))
def test_starter_fails_the_checks_the_lab_teaches(lab):
    failures = [m for ok, m in check_lab.grade(lab, LABS_DIR / f"starters/lab{lab}" / ARTIFACT[lab]) if not ok]
    for expected in STARTER_MUST_FAIL[lab]:
        assert any(expected in m for m in failures), f"starter should fail a check mentioning {expected!r}"


def test_every_lab_has_a_guide_in_its_pillar():
    root = LABS_DIR.parent
    for lab in check_lab.LABS:
        assert list(root.glob(f"0{lab}_*/lab.md")), f"pillar 0{lab} has no lab.md"
