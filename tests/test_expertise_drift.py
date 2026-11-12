"""The expertise drift checker against a small project whose code has moved under its expertise file."""

import importlib.util
import sys
import textwrap
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "check_expertise", Path(__file__).parent.parent / "08_expertise_drift/check_expertise.py")
check_expertise = importlib.util.module_from_spec(SPEC)
sys.modules["check_expertise"] = check_expertise
SPEC.loader.exec_module(check_expertise)

EXPERTISE = textwrap.dedent("""\
    core:
      manager:
        file: "backend/manager.py"
        lines: 4  # total
        connect:
          lines: "1-2"
        vanished:
          lines: "3-4"
      gone:
        file: "backend/deleted.py"
    """)


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "lesson"
    (root / ".git").mkdir(parents=True)
    expertise = root / ".claude/commands/experts/demo/expertise.yaml"
    expertise.parent.mkdir(parents=True)
    expertise.write_text(EXPERTISE)
    source = root / "apps/app/backend/manager.py"
    source.parent.mkdir(parents=True)
    source.write_text("import os\n" * 30 + "def connect():\n    return 1\n")
    return expertise


def kinds(findings):
    return sorted((f.kind, f.where) for f in findings)


def test_reports_each_kind_of_drift(project):
    assert kinds(check_expertise.check_file(project, 15, 0.15)) == [
        ("line-count", "core.manager.lines"),
        ("missing-file", "core.gone"),
        ("missing-symbol", "core.manager.vanished"),
        ("moved-symbol", "core.manager.connect.lines"),
    ]


def test_fix_rewrites_only_line_references_and_keeps_comments(project):
    assert check_expertise.main(["--fix", str(project)]) == 1
    text = project.read_text()
    assert 'lines: 32  # total' in text
    assert 'connect:\n      lines: "31-32"' in text
    remaining = kinds(check_expertise.check_file(project, 15, 0.15))
    assert remaining == [("missing-file", "core.gone"), ("missing-symbol", "core.manager.vanished")]


def test_clean_file_exits_zero(project):
    project.write_text('core:\n  manager:\n    file: "backend/manager.py"\n    connect:\n      lines: "31-32"\n')
    assert check_expertise.main([str(project)]) == 0
