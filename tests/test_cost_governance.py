"""Budget ledger, circuit breaker, per-call caps, and the dashboard SQL checked against the orchestrator migrations."""

import importlib.util
import re
import sys
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).parent.parent
MIGRATIONS = ROOT / "14.orchestrator-agent-with-adws-singularity/apps/orchestrator_db/migrations"


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"11_cost_governance/{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


budget = load("budget")
cost_report = load("cost_report")

PATH = ("org", "adw:123", "step:build")


def test_charge_counts_against_every_ancestor():
    ledger = budget.BudgetLedger({"org": 100, "adw": 10, "step": 4})
    ledger.charge(PATH, 1.5)
    ledger.charge(("org", "adw:123", "step:review"), 2)
    ledger.charge(("org", "adw:456"), 3)
    assert ledger.spent(("org",)) == 6.5
    assert ledger.spent(("org", "adw:123")) == 3.5
    assert ledger.spent(PATH) == 1.5
    assert ledger.remaining(PATH) == 2.5


def test_limit_is_inclusive_and_a_refused_charge_records_nothing():
    ledger = budget.BudgetLedger({"step": 0.3})
    ledger.charge(PATH, 0.1)
    ledger.charge(PATH, 0.2)
    assert ledger.spent(PATH) == 0.3
    assert ledger.remaining(PATH) == 0
    with pytest.raises(budget.BudgetExceeded) as exc:
        ledger.charge(PATH, 0.0001)
    assert (exc.value.scope, exc.value.spent, exc.value.limit) == (PATH, 0.3001, 0.3)
    assert ledger.spent(PATH) == 0.3
    assert ledger.spent(("org",)) == 0.3


def test_exact_segment_limit_overrides_its_kind():
    ledger = budget.BudgetLedger({"adw": 1, "adw:big": 50})
    ledger.charge(("org", "adw:big"), 20)
    with pytest.raises(budget.BudgetExceeded) as exc:
        ledger.charge(("org", "adw:small"), 2)
    assert exc.value.scope == ("org", "adw:small")


def test_already_spent_is_recorded_then_closes_the_scope():
    ledger = budget.BudgetLedger({"org": 5})
    with pytest.raises(budget.BudgetExceeded):
        ledger.charge(PATH, 6, already_spent=True)
    assert ledger.spent(("org",)) == 6
    assert ledger.remaining(PATH) == 0
    assert ledger.would_exceed(PATH, 0.01)


def test_would_exceed_is_a_dry_run():
    ledger = budget.BudgetLedger({"adw": 2})
    ledger.charge(PATH, 1.5)
    assert not ledger.would_exceed(PATH, 0.5)
    assert ledger.would_exceed(PATH, 0.51)
    assert ledger.spent(PATH) == 1.5
    assert budget.BudgetLedger({}).remaining(PATH) == float("inf")


def test_concurrent_charges_never_overspend():
    ledger = budget.BudgetLedger({"org": 10})
    accepted = []
    barrier = threading.Barrier(50)

    def worker():
        barrier.wait()
        for _ in range(10):
            try:
                ledger.charge(("org", "adw:x"), 0.07)
                accepted.append(1)
            except budget.BudgetExceeded:
                pass

    threads = [threading.Thread(target=worker) for _ in range(50)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(accepted) == 142
    assert ledger.spent(("org",)) == pytest.approx(9.94)


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def test_breaker_trips_on_consecutive_failures_and_half_opens_after_cooldown():
    clock = FakeClock()
    breaker = budget.CircuitBreaker(3, max_spend_per_minute=100, clock=clock, cooldown_seconds=30)
    breaker.record(False)
    breaker.record(False)
    breaker.record(True)
    breaker.record(False)
    breaker.record(False)
    assert breaker.allow()
    breaker.record(False)
    assert not breaker.allow()
    assert breaker.reason == "3 consecutive failures"

    clock.now += 29
    assert not breaker.allow()
    clock.now += 1
    assert breaker.state is budget.BreakerState.HALF_OPEN
    assert breaker.allow()
    assert not breaker.allow(), "only one trial call while half-open"
    breaker.record(True)
    assert breaker.state is budget.BreakerState.CLOSED
    assert breaker.allow()


def test_failed_trial_reopens_for_another_cooldown():
    clock = FakeClock()
    breaker = budget.CircuitBreaker(1, max_spend_per_minute=100, clock=clock, cooldown_seconds=10)
    breaker.record(False)
    clock.now += 10
    assert breaker.allow()
    breaker.record(False)
    assert breaker.state is budget.BreakerState.OPEN
    clock.now += 9
    assert not breaker.allow()


def test_breaker_trips_on_spend_rate_within_the_minute_only():
    clock = FakeClock()
    breaker = budget.CircuitBreaker(10, max_spend_per_minute=5, clock=clock, cooldown_seconds=60)
    breaker.record(True, 2)
    clock.now += 59
    breaker.record(True, 3)
    assert breaker.allow(), "exactly at the rate is allowed"
    clock.now += 1
    breaker.record(True, 2)
    assert breaker.allow(), "the first $2 left the window"
    breaker.record(True, 0.01)
    assert not breaker.allow()
    assert breaker.reason == "spent $5.01 in the last minute (limit $5)"


def test_options_with_caps():
    assert budget.options_with_caps(8, 0.5, model="sonnet") == {"model": "sonnet", "max_turns": 8, "max_budget_usd": 0.5}
    with pytest.raises(ValueError):
        budget.options_with_caps(0, 1)
    with pytest.raises(ValueError):
        budget.options_with_caps(5, 0)


def test_options_with_caps_matches_the_sdk():
    sdk = pytest.importorskip("claude_agent_sdk")
    options = sdk.ClaudeAgentOptions(**budget.options_with_caps(3, 0.25, model="haiku"))
    assert (options.max_turns, options.max_budget_usd) == (3, 0.25)


def test_charge_result_reads_total_cost_usd():
    ledger = budget.BudgetLedger({"step": 1})
    assert budget.charge_result(ledger, PATH, SimpleNamespace(total_cost_usd=0.42)) == 0.42
    assert budget.charge_result(ledger, PATH, SimpleNamespace(total_cost_usd=None)) is None
    assert ledger.spent(PATH) == 0.42
    with pytest.raises(budget.BudgetExceeded):
        budget.charge_result(ledger, PATH, SimpleNamespace(total_cost_usd=0.6))
    assert ledger.spent(PATH) == 1.02


def migration_columns() -> dict[str, set[str]]:
    tables = {}
    for sql in MIGRATIONS.glob("*.sql"):
        for name, body in re.findall(r"CREATE TABLE IF NOT EXISTS (\w+) \((.*?)\n\);", sql.read_text(), re.S):
            tables[name] = {m.group(1) for m in re.finditer(r"^\s+(\w+)\s+[A-Z]", body, re.M)} - {"CONSTRAINT"}
    return tables


def test_migration_parser_sees_the_cost_columns():
    tables = migration_columns()
    assert {"total_cost", "adw_id", "adw_step", "git_worktree"} <= tables["agents"]
    assert "total_cost" in tables["orchestrator_agents"]
    assert {"status", "adw_name"} <= tables["ai_developer_workflows"]


def test_dashboard_sections_reference_only_real_columns():
    sections = cost_report.parse_sections((ROOT / "11_cost_governance/dashboard.sql").read_text())
    assert list(sections) == ["spend_by_agent", "spend_by_orchestrator", "spend_by_adw_step",
                              "top_adws", "daily_spend", "cost_by_adw_outcome"]
    tables = migration_columns()
    for name, sql in sections.items():
        aliases = {alias: table for table, alias in re.findall(r"(?:FROM|JOIN) (\w+) (\w+)", sql)}
        derived = set(re.findall(r"\) (\w+)", sql))
        refs = re.findall(r"\b([a-z_]+)\.([a-z_]+)\b", sql)
        outputs = set(re.findall(r"AS (\w+)", sql)) | {column for _, column in refs}
        assert refs, name
        for alias, column in refs:
            if alias in derived:
                assert column in outputs, f"{name}: {alias}.{column} is not an output of the subquery"
            else:
                assert aliases[alias] in tables, f"{name}: unknown table {aliases[alias]}"
                assert column in tables[aliases[alias]], f"{name}: {aliases[alias]}.{column} not in migrations"


def test_to_markdown():
    assert cost_report.to_markdown([["agent", "cost"], ["a|b", "1.5"]]) == "| agent | cost |\n|---|---|\n| a\\|b | 1.5 |"
    assert cost_report.to_markdown([["agent"]]).endswith("_no rows_")
