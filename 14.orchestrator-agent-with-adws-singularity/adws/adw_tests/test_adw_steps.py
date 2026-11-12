"""
The real step executor against recorded SDK streams (fakes.ReplayClient) and an
in-memory record of the ADW tables (fakes.MemorySink): caps, step permissions,
submit tools, fail-closed review verdicts, and quoting of slash-command arguments.
"""

import asyncio
import shlex
from pathlib import Path

from fakes import (  # first: puts adws/ on sys.path
    ADW_ID,
    MemorySink,
    Replays,
    Stall,
    adw_row,
    assistant,
    init_message,
    project,  # noqa: F401  (pytest fixture)
    result,
    tool_call,
)

from claude_agent_sdk import TextBlock

from adw_modules.adw_agent_sdk import HookContext, StopInput
from adw_modules.adw_steps import (
    SUBMIT_PLAN_TOOL,
    SUBMIT_REVIEW_TOOL,
    AdwInput,
    build,
    logging_hooks,
    plan,
    review_must_pass,
    run_workflow,
    slash_command,
    step_spec,
)


def run(project_dir: Path, steps, *scripts, sink=None, **input_overrides):
    sink = sink or MemorySink(adw_row(project_dir, **input_overrides))
    replays = Replays(*scripts)
    outcome = asyncio.run(run_workflow(ADW_ID, steps, len(steps), sink=sink, client_factory=replays))
    return outcome, sink, replays


def plan_script(path: str) -> list:
    return [init_message(), tool_call(SUBMIT_PLAN_TOOL, {"plan_path": path}), result(cost=0.4)]


def review_script(verdict: str, blockers: int, report: str = "# Code Review Report") -> list:
    args = {"verdict": verdict, "report": report, "blocker_count": blockers}
    return [init_message(), tool_call(SUBMIT_REVIEW_TOOL, args), result(cost=0.3)]


# ---------------------------------------------------------------- caps (item 2)


def test_each_step_sends_its_caps_and_permission_mode_to_the_sdk(project):
    outcome, _, replays = run(
        project, [plan, build, review_must_pass],
        plan_script("specs/login form.md"), [init_message(), result()], review_script("PASS", 0),
        step_caps={"build": {"max_turns": 99}},
    )
    assert outcome.status == "completed"
    sent = {c.prompt.split()[0]: c.options for c in replays.clients}
    assert {k: (o.max_turns, o.max_budget_usd, o.permission_mode) for k, o in sent.items()} == {
        "/plan": (40, 3.0, "acceptEdits"),
        "/build": (99, 8.0, "acceptEdits"),
        "/review": (40, 3.0, "dontAsk"),
    }


def test_review_cannot_write_or_run_arbitrary_shell(project):
    _, _, replays = run(project, [plan, build, review_must_pass],
                        plan_script("specs/login form.md"), [init_message(), result()], review_script("PASS", 0))
    review = replays.clients[2].options
    assert {"Write", "Edit", "MultiEdit"} <= set(review.disallowed_tools)
    assert "Bash" not in review.allowed_tools
    assert all(not t.startswith("Bash") or t.startswith("Bash(git ") for t in review.allowed_tools)


def test_max_turns_result_fails_the_step(project):
    outcome, sink, _ = run(project, [plan],
                           [init_message(), result("error_max_turns", is_error=True, text=None, turns=41)])
    assert (outcome.status, outcome.error_step) == ("failed", "plan")
    assert outcome.error_message == "plan hit its max_turns cap (40)"
    assert sink.final_status["status"] == "failed"


def test_budget_result_fails_the_step(project):
    outcome, _, _ = run(project, [plan],
                        [init_message(), result("error_max_budget_usd", is_error=True, text=None, cost=3.2)])
    assert outcome.error_message == "plan hit its max_budget_usd cap ($3.00; spent $3.20)"
    assert outcome.output.total_cost_usd == 3.2


def test_wall_clock_cap_fails_the_step(project):
    outcome, _, _ = run(project, [plan], [init_message(), Stall(5), result()],
                        step_caps={"plan": {"timeout_seconds": 0.05}})
    assert (outcome.status, outcome.error_message) == ("failed", "plan hit its wall clock cap (0s)")


def test_adw_budget_stops_before_a_step_that_could_exceed_it(project):
    # Plan spends $4; build may spend up to $8; $4 + $8 > $10.
    outcome, _, replays = run(
        project, [plan, build],
        [init_message(), tool_call(SUBMIT_PLAN_TOOL, {"plan_path": "specs/login form.md"}), result(cost=4.0)],
        max_budget_usd=10, step_caps={"plan": {"max_budget_usd": 5}},
    )
    assert (outcome.status, outcome.error_step) == ("failed", "build")
    assert outcome.error_message.startswith("budget: spent $4.00; build may spend up to $8.00")
    assert len(replays.clients) == 1


# ---------------------------------------------------------- submit tools (item 4)


def test_plan_path_comes_from_submit_plan(project):
    outcome, sink, replays = run(project, [plan, build],
                                 plan_script("specs/login form.md"), [init_message(), result()])
    plan_file = str((project / "specs" / "login form.md").resolve())
    assert outcome.output.plan_path == plan_file
    assert sink.output["plan_path"] == plan_file
    assert shlex.split(replays.clients[1].prompt) == ["/build", plan_file]


def test_a_submitted_path_that_does_not_exist_is_refused_and_the_plan_fails(project):
    # A newer file in specs/ must not be picked up as the plan.
    (project / "specs" / "someone-elses-plan.md").write_text("# other run")
    outcome, _, replays = run(project, [plan, build], plan_script("specs/never-written.md"))
    assert replays.clients[0].tool_results[0].is_error
    assert (outcome.status, outcome.error_step) == ("failed", "plan")
    assert outcome.output.plan_path is None
    assert len(replays.clients) == 1


def test_submit_review_report_is_written_by_python(project):
    outcome, sink, _ = run(project, [plan, build, review_must_pass],
                           plan_script("specs/login form.md"), [init_message(), result()],
                           review_script("FAIL", 2, report="# Report\n2 blockers"))
    review = outcome.output.reviews[0]
    assert (review.verdict, review.verdict_source, review.blocker_count) == ("FAIL", "submit_review", 2)
    assert Path(review.report_path).read_text() == "# Report\n2 blockers"
    assert Path(review.report_path).parent == project / "app_review"
    assert (outcome.status, outcome.error_step) == ("failed", "review")
    assert sink.output["reviews"][0]["report_path"] == review.report_path


def test_pass_with_blockers_is_refused(project):
    outcome, _, replays = run(project, [plan, build, review_must_pass],
                              plan_script("specs/login form.md"), [init_message(), result()],
                              review_script("PASS", 1))
    assert replays.clients[2].tool_results[0].is_error
    assert outcome.output.reviews[0].verdict_source == "final_message"
    assert outcome.status == "failed"


def test_review_that_skips_the_tool_fails_closed_even_if_its_text_says_pass(project):
    outcome, _, _ = run(project, [plan, build, review_must_pass],
                        plan_script("specs/login form.md"), [init_message(), result()],
                        [init_message(), assistant(TextBlock("Verdict: ✅ PASS")), result(text="Verdict: ✅ PASS")])
    review = outcome.output.reviews[0]
    assert (review.verdict, review.verdict_source, review.passed) == ("PASS", "final_message", False)
    assert Path(review.report_path).read_text() == "Verdict: ✅ PASS"
    assert (outcome.status, outcome.error_step) == ("failed", "review")
    assert "did not call" in outcome.error_message


# ------------------------------------------------------- quoting (item 10)


def test_slash_command_arguments_survive_shell_style_splitting():
    prompt = 'Fix the "login" bug; don\'t touch $HOME or `rm -rf`\nsecond line'
    paths = ["/work/my project/specs/login form.md", "/work/my project/app_review/review 1.md"]
    command = slash_command("fix", prompt, *paths)
    assert shlex.split(command) == ["/fix", prompt, *paths]


def test_build_and_review_quote_paths_with_spaces(project):
    _, _, replays = run(project, [plan, build, review_must_pass],
                        plan_script("specs/login form.md"), [init_message(), result()], review_script("PASS", 0))
    plan_file = str((project / "specs" / "login form.md").resolve())
    assert shlex.split(replays.clients[2].prompt) == ["/review", "Add a login form", plan_file]


def test_step_labels_are_unique_per_fix_round(project):
    inp = AdwInput(prompt="p", working_dir=str(project))
    assert [step_spec(inp, "review", "/review", n).label for n in (0, 1, 2)] == ["review", "review-r1", "review-r2"]


# ------------------------------------------------ logging is best effort (item 7, 12)


def test_database_failures_inside_a_step_do_not_fail_it(project):
    sink = MemorySink(adw_row(project), fail=True)
    outcome, _, _ = run(project, [plan, build], plan_script("specs/login form.md"),
                        [init_message(), result()], sink=sink)
    assert outcome.status == "completed"
    assert sink.named("log_step_start")  # attempted, failed, carried on


def test_stop_hook_logs_the_fields_stop_input_has(project):
    sink = MemorySink()

    class Run:
        adw_id = ADW_ID

        @staticmethod
        async def safe(what, call):
            return await call

    Run.sink = sink
    hooks = logging_hooks(Run(), "build", "agent-1")
    stop_input = StopInput(session_id="sess-9", transcript_path="/t", cwd="/w",
                           permission_mode="acceptEdits", stop_hook_active=True)
    asyncio.run(hooks.stop[0].hooks[0](stop_input, None, HookContext()))
    [logged] = sink.named("log_event")
    assert logged["payload"] == {"session_id": "sess-9", "stop_hook_active": True, "permission_mode": "acceptEdits"}
    assert "unknown" not in logged["content"]
