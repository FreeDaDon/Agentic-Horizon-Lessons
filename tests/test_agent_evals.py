"""The agent eval harness: grader sanity on the shipped suite, hidden graders, and claude result parsing."""

import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest

MODULE = Path(__file__).parent.parent / "07_agent_evals"
SPEC = importlib.util.spec_from_file_location("eval_harness", MODULE / "eval_harness.py")
h = importlib.util.module_from_spec(SPEC)
sys.modules["eval_harness"] = h
SPEC.loader.exec_module(h)

SUITE = MODULE / "tasks"
SHIPPED = {"off_by_one", "json_flag", "empty_input", "review_verdict"}


def test_shipped_suite_passes_grader_sanity():
    assert {t.id for t in h.load_suite(SUITE)} == SHIPPED
    assert h.check(SUITE) == []


def test_check_catches_a_grader_that_passes_a_noop_run(tmp_path):
    suite = tmp_path / "suite"
    shutil.copytree(SUITE / "off_by_one", suite / "always_green")
    task_yaml = suite / "always_green/task.yaml"
    task_yaml.write_text(task_yaml.read_text().replace(
        'grader: ["{python}", "-m", "pytest"', 'grader: ["{python}", "-c", "pass", "-m", "pytest"'))
    assert h.check(suite) == ["always_green: grader passes the noop run"]


def test_grader_is_absent_while_the_agent_runs():
    seen = {}

    def lister(task, workspace):
        seen[task.id] = sorted(p.name for p in workspace.rglob("*") if ".git" not in p.parts)
        return h.AgentResult(is_error=False, cost_usd=0.0, turns=0)

    records = h.run_suite(SUITE, h.Agent("lister", None, lister), k=1, out=None)
    assert set(seen) == SHIPPED
    for task in h.load_suite(SUITE):
        hidden = {p.name for p in (task.dir / "grader").iterdir()}
        assert hidden.isdisjoint(seen[task.id]), f"{task.id}: agent saw {hidden & set(seen[task.id])}"
    assert not any(r.passed for r in records)


def test_parses_recorded_claude_json_result():
    stdout = (MODULE / "fixtures/claude_result.json").read_text()
    assert h.parse_claude_result(stdout) == h.AgentResult(is_error=False, cost_usd=0.0043392, turns=1)


def test_verbose_message_list_uses_the_result_message():
    result = json.loads((MODULE / "fixtures/claude_result.json").read_text())
    stdout = json.dumps([{"type": "system", "subtype": "init"}, result])
    assert h.parse_claude_result(stdout).turns == 1


@pytest.mark.parametrize("stdout", ["", "Error: not logged in", json.dumps([{"type": "system"}])])
def test_unparseable_output_counts_as_an_agent_error(stdout):
    assert h.parse_claude_result(stdout) == h.AgentResult(is_error=True, cost_usd=None, turns=None)


def test_report_scores_each_task_and_appends_to_the_scoreboard(tmp_path):
    rows = [
        {"task": "a", "agent": "claude", "model": "haiku", "run": 0, "passed": True, "cost_usd": 0.02, "turns": 4, "wall_s": 10},
        {"task": "a", "agent": "claude", "model": "haiku", "run": 1, "passed": False, "cost_usd": 0.04, "turns": 6, "wall_s": 20},
        {"task": "b", "agent": "claude", "model": "haiku", "run": 0, "passed": True, "cost_usd": 0.01, "turns": 2, "wall_s": 5},
        {"task": "b", "agent": "claude", "model": "haiku", "run": 1, "passed": True, "cost_usd": 0.01, "turns": 2, "wall_s": 5},
    ]
    results = tmp_path / "run.jsonl"
    results.write_text("".join(json.dumps(r) + "\n" for r in rows))
    scoreboard = tmp_path / "scoreboard.md"
    scoreboard.write_text("# header\n")

    markdown = h.report([results], scoreboard)

    assert "| claude/haiku | a | 1/2 | 1 | 0.0300 | 5.0 | 15.0 |" in markdown
    assert "| claude/haiku | b | 2/2 | 1 | 0.0100 | 2.0 | 5.0 |" in markdown
    assert "3/4 runs passed. Suite pass rate per run ranged 50% to 100% over 2 runs." in markdown
    assert scoreboard.read_text() == "# header\n\n" + markdown
