"""Calibrate the reviewer: its verdict must agree with what the spec checks say about the diff."""

import importlib.util
import re
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).parent


def diff_meets_spec(tmp_path):
    shutil.copy(HERE / "_base_shipping.py", tmp_path / "shipping.py")
    subprocess.run(["git", "apply", str(HERE / "_change.diff")], cwd=tmp_path, check=True)
    spec = importlib.util.spec_from_file_location("patched_shipping", tmp_path / "shipping.py")
    patched = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(patched)
    try:
        patched.shipping_cost(-1)
        rejects_negative = False
    except ValueError:
        rejects_negative = True
    return (rejects_negative and patched.shipping_cost(100.00) == 0.0
            and patched.shipping_cost(250.0) == 0.0 and patched.shipping_cost(99.99) == 5.00)


def test_verdict_agrees_with_spec_checks(tmp_path):
    review = (HERE / "REVIEW.md").read_text()
    last_line = [line for line in review.splitlines() if line.strip()][-1].strip()
    match = re.fullmatch(r"VERDICT: (PASS|FAIL)", last_line)
    assert match, f"last line is not a verdict: {last_line!r}"
    expected = "PASS" if diff_meets_spec(tmp_path) else "FAIL"
    assert match.group(1) == expected
