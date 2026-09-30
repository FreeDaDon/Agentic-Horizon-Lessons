"""
Tests for adw_modules.adw_review.parse_verdict.

Run: uv run --no-project --with pytest pytest adws/adw_tests/test_adw_review.py
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from adw_modules.adw_review import parse_verdict  # noqa: E402


@pytest.mark.parametrize("text,verdict", [
    # Clear verdicts, in the shapes the /review command asks for
    ("Review complete. Verdict: ✅ PASS - no blockers.", "PASS"),
    ("**Status**: ✅ PASS", "PASS"),
    ("All checks passed.", "PASS"),
    ("Review complete. Verdict: ⚠️ FAIL - 2 blockers found.", "FAIL"),
    ("**Status**: ⚠️ FAIL", "FAIL"),
    ("Build failed type checks.", "FAIL"),
    # FAIL wins over PASS
    ("Tests PASS but the review verdict is FAIL.", "FAIL"),
    ("PASS / FAIL: FAIL", "FAIL"),
    # PASS inside another word is not a verdict
    ("Blocker: the password is stored in plaintext. See report.", None),
    ("Auth bypass found in login.", None),
    ("Passport number field unvalidated.", None),
    # No verdict word at all
    ("Review complete: 2 blockers found (SQL injection in login). See report.", None),
    ("", None),
    (None, None),
])
def test_parse_verdict(text, verdict):
    assert parse_verdict(text) == verdict
