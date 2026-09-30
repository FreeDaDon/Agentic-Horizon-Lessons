"""
Tests for adw_modules.adw_plan.existing_plan_path, against real files in a temp directory.

Run: uv run --no-project --with pytest pytest adws/adw_tests/test_adw_plan.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from adw_modules.adw_plan import existing_plan_path  # noqa: E402


def make_plan(tmp_path):
    plan = tmp_path / "specs" / "login-form.md"
    plan.parent.mkdir()
    plan.write_text("# Plan")
    return plan


def test_absolute_path_to_an_existing_plan(tmp_path):
    plan = make_plan(tmp_path)
    assert existing_plan_path(str(plan), str(tmp_path)) == str(plan.resolve())


def test_relative_path_resolves_from_the_working_dir(tmp_path):
    plan = make_plan(tmp_path)
    assert existing_plan_path("specs/login-form.md", str(tmp_path)) == str(plan.resolve())
    assert existing_plan_path("./specs/login-form.md", str(tmp_path)) == str(plan.resolve())


def test_a_path_that_was_never_written_is_rejected(tmp_path):
    make_plan(tmp_path)
    # The example path from the extraction prompt, echoed back by the agent
    assert existing_plan_path("/Users/user/project/specs/feature-plan.md", str(tmp_path)) is None
    assert existing_plan_path("specs/other-plan.md", str(tmp_path)) is None


def test_a_directory_is_not_a_plan(tmp_path):
    make_plan(tmp_path)
    assert existing_plan_path("specs", str(tmp_path)) is None


def test_nothing_extracted(tmp_path):
    assert existing_plan_path(None, str(tmp_path)) is None
    assert existing_plan_path("", str(tmp_path)) is None
