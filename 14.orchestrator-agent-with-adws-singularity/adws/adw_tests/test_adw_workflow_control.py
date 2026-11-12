"""
Workflow control flow with a scripted step runner in place of agents: the review/fix
loop, review gating, budget accounting, crash handling, and background summaries.
See fakes.py for why these offline tests use fakes at the SDK and DB boundaries.
"""

import asyncio
from pathlib import Path

import pytest

from fakes import ADW_ID, MemorySink, adw_row, project  # noqa: F401  (first: puts adws/ on sys.path)

from adw_modules.adw_steps import (
    PlanSubmission,
    ReviewSubmission,
    StepResult,
    SummaryPool,
    build,
    plan,
    review_must_pass,
    review_until_pass,
    run_workflow,
)


class ScriptedSteps:
    """Stands in for execute_step: each review returns the next scripted verdict."""

    def __init__(self, plan_path: str, verdicts: list[str], cost: float = 1.0):
        self.plan_path = plan_path
        self.verdicts = list(verdicts)
        self.cost = cost
        self.labels: list[str] = []
        self.prompts: list[str] = []

    async def __call__(self, run, spec) -> StepResult:
        self.labels.append(spec.label)
        self.prompts.append(spec.prompt)
        submission = None
        if spec.name == "plan":
            submission = PlanSubmission(plan_path=self.plan_path)
        elif spec.name == "review":
            verdict = self.verdicts.pop(0)
            submission = ReviewSubmission(verdict=verdict, report=f"# {verdict}",
                                          blocker_count=0 if verdict == "PASS" else 1)
        return StepResult(ok=True, cost_usd=self.cost, submission=submission)


def run(project_dir: Path, steps, verdicts, total_steps=4, sink=None, **input_overrides):
    plan_path = str(project_dir / "specs" / "login form.md")
    scripted = ScriptedSteps(plan_path, verdicts)
    sink = sink or MemorySink(adw_row(project_dir, **input_overrides))
    outcome = asyncio.run(run_workflow(ADW_ID, steps, total_steps, sink=sink, execute=scripted))
    return outcome, scripted, sink


FIX_WORKFLOW = [plan, build, review_until_pass]


def test_passing_review_skips_fix(project):
    outcome, steps, sink = run(project, FIX_WORKFLOW, ["PASS"])
    assert outcome.status == "completed"
    assert steps.labels == ["plan", "build", "review"]
    assert sink.final_status == {"adw_id": ADW_ID, "status": "completed", "completed_steps": 4,
                                 "error_message": None, "error_step": None}


def test_fix_then_rereview_until_pass(project):
    outcome, steps, _ = run(project, FIX_WORKFLOW, ["FAIL", "FAIL", "PASS"])
    assert outcome.status == "completed"
    assert steps.labels == ["plan", "build", "review", "fix-r1", "review-r1", "fix-r2", "review-r2"]
    assert [r.verdict for r in outcome.output.reviews] == ["FAIL", "FAIL", "PASS"]


def test_each_fix_reads_the_report_of_the_review_before_it(project):
    _, steps, _ = run(project, FIX_WORKFLOW, ["FAIL", "FAIL", "PASS"])
    fix_prompts = [p for label, p in zip(steps.labels, steps.prompts) if label.startswith("fix")]
    assert fix_prompts[0].endswith(f"review_{ADW_ID[:8]}_r0.md")
    assert fix_prompts[1].endswith(f"review_{ADW_ID[:8]}_r1.md")


def test_still_failing_after_max_fix_rounds_escalates(project):
    outcome, steps, sink = run(project, FIX_WORKFLOW, ["FAIL", "FAIL", "FAIL"])
    assert (outcome.status, outcome.error_step) == ("failed", "review")
    assert outcome.error_message.startswith("escalate: review still failing after 2 fix rounds")
    assert steps.labels.count("plan") == 1 and len([x for x in steps.labels if x.startswith("fix")]) == 2
    assert sink.final_status["status"] == "failed"


def test_max_fix_rounds_is_read_from_input_data(project):
    outcome, steps, _ = run(project, FIX_WORKFLOW, ["FAIL"], max_fix_rounds=0)
    assert outcome.error_message.startswith("escalate: review still failing after 0 fix rounds")
    assert steps.labels == ["plan", "build", "review"]


def test_review_workflow_fails_on_a_failing_review(project):
    outcome, steps, sink = run(project, [plan, build, review_must_pass], ["FAIL"], total_steps=3)
    assert (outcome.status, outcome.error_step) == ("failed", "review")
    assert sink.final_status["status"] == "failed"
    assert sink.final_status["completed_steps"] == 2


def test_fix_loop_stops_at_the_adw_budget(project):
    # Each scripted step costs $1. After plan, build, review: $3 + fix-r1's $5 cap fits $9.50;
    # at $4, review-r1's $3 cap fits; at $5, fix-r2's $5 cap does not.
    outcome, steps, _ = run(project, FIX_WORKFLOW, ["FAIL", "FAIL"], max_budget_usd=9.5)
    assert (outcome.status, outcome.error_step) == ("failed", "fix")
    assert outcome.error_message == (
        "budget: spent $5.00; fix-r2 may spend up to $5.00, which would exceed max_budget_usd $9.50"
    )
    assert steps.labels[-1] == "review-r1"
    assert outcome.output.total_cost_usd == 5.0


# --------------------------------------------------- errors before step 1 (item 7)


@pytest.mark.parametrize("row,message", [
    (None, f"LookupError: ADW not found: {ADW_ID}"),
    ({"orchestrator_agent_id": None, "input_data": {}}, "ValueError: ADW row has no orchestrator_agent_id"),
    ({"orchestrator_agent_id": "o", "input_data": {"working_dir": "/w"}}, "ValidationError"),
])
def test_errors_before_the_first_step_mark_the_row_failed(row, message):
    sink = MemorySink(row)
    outcome = asyncio.run(run_workflow(ADW_ID, [plan], 2, sink=sink, execute=ScriptedSteps("x", [])))
    assert outcome.status == "failed"
    assert sink.final_status["status"] == "failed"
    assert message in sink.final_status["error_message"]
    assert sink.calls[-1][0] == "close"


def test_an_unexpected_exception_in_a_step_marks_the_row_failed(project):
    async def explode(run, spec):
        raise RuntimeError("boom")

    sink = MemorySink(adw_row(project))
    outcome = asyncio.run(run_workflow(ADW_ID, [plan], 2, sink=sink, execute=explode))
    assert (outcome.status, outcome.error_step, outcome.error_message) == ("failed", "plan", "RuntimeError: boom")
    assert sink.final_status["error_step"] == "plan"


# ------------------------------------------------------- summaries (item 8)


def test_summary_pool_bounds_concurrency_and_finishes_before_close():
    running = 0
    peak = 0
    done = []

    async def summarize(i):
        nonlocal running, peak
        running += 1
        peak = max(peak, running)
        await asyncio.sleep(0.01)
        running -= 1
        done.append(i)

    async def main():
        pool = SummaryPool(summarize, limit=4)
        for i in range(12):
            pool.submit(i)
        await pool.drain(timeout=5)

    asyncio.run(main())
    assert peak == 4
    assert sorted(done) == list(range(12))


def test_summary_pool_drain_cancels_stragglers():
    cancelled = []

    async def summarize():
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            cancelled.append(True)
            raise

    async def main():
        pool = SummaryPool(summarize, limit=4)
        pool.submit()
        await asyncio.sleep(0)
        await pool.drain(timeout=0.01)

    asyncio.run(main())
    assert cancelled == [True]


def test_summaries_run_before_the_sink_closes(project):
    class SlowSummarySink(MemorySink):
        async def summarize(self, adw_id, log_id, event_data, event_type):
            await asyncio.sleep(0.05)
            await super().summarize(adw_id, log_id, event_data, event_type)

    async def logs_a_block(run, spec):
        log_id = await run.sink.log_event(adw_id=run.adw_id)
        run.summaries.submit(run.adw_id, log_id, {"content": "x"}, "TextBlock")
        return StepResult(ok=True, submission=PlanSubmission(plan_path=str(project / "specs" / "login form.md")))

    sink = SlowSummarySink(adw_row(project))
    asyncio.run(run_workflow(ADW_ID, [plan], 2, sink=sink, execute=logs_a_block))
    names = [n for n, _ in sink.calls]
    assert names.index("summarize") < names.index("close")
