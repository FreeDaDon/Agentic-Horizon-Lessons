# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "asyncpg==0.30.0",
#   "python-dotenv==1.2.1",
#   "pydantic==2.12.3",
#   "claude-agent-sdk==0.2.163",
#   "rich==14.2.0",
#   "websockets==15.0.1",
# ]
# ///
"""
ADW Steps - The shared step runner every ADW workflow is built from.

A workflow file is a list of step functions (plan, build, review_must_pass,
review_until_pass) handed to run_cli. This module owns everything they share:

- StepSpec per step: slash command, model, permission mode, tools, caps
  (max_turns, max_budget_usd, wall clock), taken from STEP_PROFILES and input_data.
- The agent row lifecycle, logging hooks, message handlers and bounded AI summaries.
- In-process submit tools: the plan agent reports its plan with submit_plan and
  the review agent reports its verdict and report with submit_review, so Python
  never guesses a path or a verdict from text or from the newest file on disk.
- Per-ADW budget accounting, and the outcome written to ai_developer_workflows.

Usage (a workflow file):
    from adw_modules.adw_steps import build, plan, run_cli

    TOTAL_STEPS = 2
    STEPS = [plan, build]

    if __name__ == "__main__":
        run_cli(STEPS, TOTAL_STEPS)
"""

from __future__ import annotations

import argparse
import asyncio
import shlex
import sys
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable, Literal

from pydantic import BaseModel, Field, ValidationError, model_validator
from rich.console import Console
from rich.panel import Panel

from adw_modules.adw_agent_sdk import (
    HookContext,
    HookInput,
    HookMatcher,
    HookResponse,
    HooksConfig,
    MessageHandlers,
    PermissionMode,
    PostToolUseInput,
    PreToolUseInput,
    QueryInput,
    QueryOptions,
    QueryOutput,
    ResultMessage,
    StopInput,
    TextBlock,
    ThinkingBlock,
    ToolUseBlock,
    query_to_completion,
)
from adw_modules.adw_plan import existing_plan_path
from adw_modules.adw_review import parse_verdict

console = Console()

StepName = Literal["plan", "build", "review", "fix"]
Verdict = Literal["PASS", "FAIL"]


# =============================================================================
# INPUT - parsed once from ai_developer_workflows.input_data
# =============================================================================


class StepCaps(BaseModel):
    max_turns: int = Field(gt=0)
    max_budget_usd: float = Field(gt=0)
    timeout_seconds: float = Field(gt=0)


class StepCapsOverride(BaseModel):
    max_turns: int | None = Field(None, gt=0)
    max_budget_usd: float | None = Field(None, gt=0)
    timeout_seconds: float | None = Field(None, gt=0)


DEFAULT_CAPS: dict[StepName, StepCaps] = {
    "plan": StepCaps(max_turns=40, max_budget_usd=3.0, timeout_seconds=30 * 60),
    "build": StepCaps(max_turns=80, max_budget_usd=8.0, timeout_seconds=60 * 60),
    "review": StepCaps(max_turns=40, max_budget_usd=3.0, timeout_seconds=30 * 60),
    "fix": StepCaps(max_turns=60, max_budget_usd=5.0, timeout_seconds=45 * 60),
}


class AdwInput(BaseModel):
    """ai_developer_workflows.input_data. Everything but prompt and working_dir has a default."""

    prompt: str = Field(min_length=1)
    working_dir: str = Field(min_length=1)
    model: str = "opus"
    review_model: str = "opus"
    fix_model: str = "opus"
    max_budget_usd: float = Field(20.0, gt=0)
    max_fix_rounds: int = Field(2, ge=0)
    step_caps: dict[StepName, StepCapsOverride] = Field(default_factory=dict)

    def caps(self, step: StepName) -> StepCaps:
        override = self.step_caps.get(step)
        updates = override.model_dump(exclude_none=True) if override else {}
        return DEFAULT_CAPS[step].model_copy(update=updates)


# =============================================================================
# STEP PROFILES - what each kind of step may do
# =============================================================================

SUBMIT_SERVER = "adw"
SUBMIT_PLAN_TOOL = f"mcp__{SUBMIT_SERVER}__submit_plan"
SUBMIT_REVIEW_TOOL = f"mcp__{SUBMIT_SERVER}__submit_review"

EDIT_TOOLS = [
    "Read", "Glob", "Grep", "Bash", "Write", "Edit", "MultiEdit",
    "Task", "TodoWrite", "WebFetch", "WebSearch", "Skill",
]
READ_ONLY_GIT = [
    "Bash(git diff:*)", "Bash(git status:*)", "Bash(git log:*)", "Bash(git show:*)",
]
WRITE_TOOLS = ["Write", "Edit", "MultiEdit", "NotebookEdit"]


class StepProfile(BaseModel):
    permission_mode: PermissionMode
    allowed_tools: list[str]
    disallowed_tools: list[str] = Field(default_factory=list)
    model_field: Literal["model", "review_model", "fix_model"]
    submit: Literal["plan", "review"] | None = None


STEP_PROFILES: dict[StepName, StepProfile] = {
    "plan": StepProfile(
        permission_mode="acceptEdits",
        allowed_tools=EDIT_TOOLS + [SUBMIT_PLAN_TOOL],
        model_field="model",
        submit="plan",
    ),
    "build": StepProfile(
        permission_mode="acceptEdits",
        allowed_tools=EDIT_TOOLS,
        model_field="model",
    ),
    # Read-only: dontAsk denies anything not listed, and the write tools are removed
    # outright. The report comes back through submit_review and Python writes it.
    "review": StepProfile(
        permission_mode="dontAsk",
        allowed_tools=["Read", "Glob", "Grep", *READ_ONLY_GIT, SUBMIT_REVIEW_TOOL],
        disallowed_tools=WRITE_TOOLS,
        model_field="review_model",
        submit="review",
    ),
    "fix": StepProfile(
        permission_mode="acceptEdits",
        allowed_tools=EDIT_TOOLS,
        model_field="fix_model",
    ),
}


def slash_command(name: str, *args: str) -> str:
    """Build `/name arg1 arg2` with POSIX shell quoting, which is how Claude Code
    splits a command's arguments into $1, $2, ... Single quotes keep spaces,
    quotes, `$` and `;` literal."""
    return " ".join([f"/{name}", *(shlex.quote(a) for a in args)])


class StepSpec(BaseModel):
    name: StepName
    label: str = Field(description="Unique within the ADW, e.g. 'review' or 'review-r2'")
    prompt: str
    model: str
    profile: StepProfile
    caps: StepCaps


def step_spec(inp: AdwInput, name: StepName, prompt: str, fix_round: int = 0) -> StepSpec:
    profile = STEP_PROFILES[name]
    return StepSpec(
        name=name,
        label=name if fix_round == 0 else f"{name}-r{fix_round}",
        prompt=prompt,
        model=getattr(inp, profile.model_field),
        profile=profile,
        caps=inp.caps(name),
    )


# =============================================================================
# SUBMIT TOOLS - typed results captured in Python
# =============================================================================


class PlanSubmission(BaseModel):
    plan_path: str = Field(description="Absolute path of an existing plan file")


class ReviewSubmission(BaseModel):
    verdict: Verdict
    report: str = Field(min_length=1)
    blocker_count: int = Field(ge=0)

    @model_validator(mode="after")
    def _pass_has_no_blockers(self) -> "ReviewSubmission":
        if self.verdict == "PASS" and self.blocker_count > 0:
            raise ValueError(f"verdict PASS with {self.blocker_count} blocker(s) is contradictory")
        return self


Submission = PlanSubmission | ReviewSubmission


@dataclass
class SubmitBox:
    """Holds the last valid submission an agent made during one step."""

    value: Submission | None = None


def _tool_text(text: str, is_error: bool = False) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}], "is_error": is_error}


def submit_server(kind: Literal["plan", "review"], working_dir: str) -> tuple[Any, SubmitBox]:
    """An in-process MCP server exposing one submit tool, and the box it fills.

    Invalid submissions are answered with a tool error so the agent can correct
    them in the same session; nothing is captured for them.
    """
    from claude_agent_sdk import create_sdk_mcp_server, tool

    box = SubmitBox()

    @tool(
        "submit_plan",
        "Report the plan file you wrote. Call this as your LAST action, with the plan's path.",
        {"plan_path": str},
    )
    async def submit_plan(args: dict[str, Any]) -> dict[str, Any]:
        path = existing_plan_path(args["plan_path"], working_dir)
        if path is None:
            return _tool_text(
                f"No file at {args['plan_path']!r} (relative paths resolve from {working_dir}). "
                "Write the plan first, then submit its path.",
                is_error=True,
            )
        box.value = PlanSubmission(plan_path=path)
        return _tool_text(f"Plan recorded: {path}. End your turn now.")

    @tool(
        "submit_review",
        "Report your review. Call this as your LAST action. `report` is the full markdown "
        "report; the workflow writes it to disk. verdict is FAIL if any blocker exists.",
        {
            "type": "object",
            "properties": {
                "verdict": {"type": "string", "enum": ["PASS", "FAIL"]},
                "report": {"type": "string"},
                "blocker_count": {"type": "integer", "minimum": 0},
            },
            "required": ["verdict", "report", "blocker_count"],
        },
    )
    async def submit_review(args: dict[str, Any]) -> dict[str, Any]:
        try:
            box.value = ReviewSubmission.model_validate(args)
        except ValidationError as e:
            return _tool_text(f"Review not recorded: {e.errors()[0]['msg']}", is_error=True)
        return _tool_text(f"Review recorded: {box.value.verdict}. End your turn now.")

    tools = {"plan": [submit_plan], "review": [submit_review]}[kind]
    return create_sdk_mcp_server(name=SUBMIT_SERVER, version="1.0.0", tools=tools), box


# =============================================================================
# RUN STATE AND OUTCOME
# =============================================================================


class StepRecord(BaseModel):
    step: StepName
    label: str
    ok: bool
    error: str | None = None
    cost_usd: float = 0.0
    num_turns: int | None = None
    session_id: str | None = None
    agent_id: str | None = None


class ReviewOutcome(BaseModel):
    fix_round: int
    verdict: Verdict | None
    verdict_source: Literal["submit_review", "final_message"]
    report_path: str
    blocker_count: int | None = None

    @property
    def passed(self) -> bool:
        """Only a verdict reported through submit_review can pass. A verdict read from
        free text, or none at all, fails closed."""
        return self.verdict_source == "submit_review" and self.verdict == "PASS"


class AdwOutput(BaseModel):
    """ai_developer_workflows.output_data."""

    plan_path: str | None = None
    reviews: list[ReviewOutcome] = Field(default_factory=list)
    steps: list[StepRecord] = Field(default_factory=list)
    total_cost_usd: float = 0.0


class StepResult(BaseModel):
    ok: bool
    error: str | None = None
    cost_usd: float = 0.0
    num_turns: int | None = None
    session_id: str | None = None
    agent_id: str | None = None
    result_text: str | None = None
    submission: Submission | None = None


class AdwOutcome(BaseModel):
    status: Literal["completed", "failed"]
    error_step: str | None = None
    error_message: str | None = None
    output: AdwOutput = Field(default_factory=AdwOutput)


class StepFailed(Exception):
    def __init__(self, step: str, message: str):
        super().__init__(f"{step}: {message}")
        self.step = step
        self.message = message


Executor = Callable[["AdwRun", StepSpec], Awaitable[StepResult]]


@dataclass
class AdwRun:
    """One ADW execution: its input, its sinks, and what it has done so far.

    `sink` is DbSink in production; any object with the same async methods works.
    `execute` runs one agent step; tests swap it for a scripted fake.
    """

    adw_id: str
    orchestrator_agent_id: str
    input: AdwInput
    sink: Any
    total_steps: int
    execute: Executor
    summaries: "SummaryPool | None" = None
    client_factory: Callable[[Any], Any] | None = None
    output: AdwOutput = field(default_factory=AdwOutput)
    done: set[str] = field(default_factory=set)
    current_step: str | None = None

    async def safe(self, what: str, call: Awaitable[Any]) -> Any:
        """Await a logging or DB call; report and swallow its failure so it cannot fail a step."""
        try:
            return await call
        except Exception as e:
            console.print(f"[yellow]{what} failed (continuing): {type(e).__name__}: {e}[/yellow]")
            return None

    async def save_output(self) -> None:
        await self.safe("save output_data", self.sink.merge_output(self.adw_id, self.output.model_dump(mode="json")))

    async def step(self, spec: StepSpec, counts_as_done: bool = True) -> StepResult:
        """Run one agent step under the per-ADW budget. Raises StepFailed on any failure.

        counts_as_done=False leaves completed_steps to the caller (a review counts once it passes).
        """
        spent = self.output.total_cost_usd
        if spent + spec.caps.max_budget_usd > self.input.max_budget_usd:
            raise StepFailed(
                spec.name,
                f"budget: spent ${spent:.2f}; {spec.label} may spend up to ${spec.caps.max_budget_usd:.2f}, "
                f"which would exceed max_budget_usd ${self.input.max_budget_usd:.2f}",
            )

        self.current_step = spec.name
        await self.safe("status update", self.sink.update_status(
            adw_id=self.adw_id, status="in_progress", current_step=spec.name,
            completed_steps=len(self.done),
        ))
        console.print(Panel(
            f"[bold cyan]{spec.label}[/bold cyan]  model={spec.model}  mode={spec.profile.permission_mode}\n"
            f"caps: {spec.caps.max_turns} turns, ${spec.caps.max_budget_usd:.2f}, {spec.caps.timeout_seconds:.0f}s\n\n"
            f"{spec.prompt[:300]}",
            title=f"ADW {self.adw_id[:8]}",
            width=console.width,
        ))

        result = await self.execute(self, spec)

        self.output.total_cost_usd += result.cost_usd
        self.output.steps.append(StepRecord(
            step=spec.name, label=spec.label, ok=result.ok, error=result.error,
            cost_usd=result.cost_usd, num_turns=result.num_turns,
            session_id=result.session_id, agent_id=result.agent_id,
        ))
        await self.save_output()
        if not result.ok:
            raise StepFailed(spec.name, result.error or "failed")
        if counts_as_done:
            self.done.add(spec.name)
        return result


# =============================================================================
# WORKFLOW STEPS - the building blocks workflow files list
# =============================================================================


async def plan(run: AdwRun) -> None:
    inp = run.input
    result = await run.step(step_spec(inp, "plan", slash_command("plan", inp.prompt)))
    if not isinstance(result.submission, PlanSubmission):
        raise StepFailed("plan", f"plan agent finished without calling {SUBMIT_PLAN_TOOL} with an existing file")
    run.output.plan_path = result.submission.plan_path
    await run.save_output()


async def build(run: AdwRun) -> None:
    await run.step(step_spec(run.input, "build", slash_command("build", _plan_path(run))))


async def review_must_pass(run: AdwRun) -> None:
    outcome = await _review(run, fix_round=0)
    if not outcome.passed:
        raise StepFailed("review", _not_passed(outcome))


async def review_until_pass(run: AdwRun) -> None:
    """Review; while it has not passed, fix and review again, up to max_fix_rounds fixes."""
    outcome = await _review(run, fix_round=0)
    for fix_round in range(1, run.input.max_fix_rounds + 1):
        if outcome.passed:
            return
        inp = run.input
        prompt = slash_command("fix", inp.prompt, _plan_path(run), outcome.report_path)
        await run.step(step_spec(inp, "fix", prompt, fix_round))
        outcome = await _review(run, fix_round)
    if not outcome.passed:
        raise StepFailed(
            "review",
            f"escalate: review still failing after {run.input.max_fix_rounds} fix rounds ({_not_passed(outcome)})",
        )


def _plan_path(run: AdwRun) -> str:
    if run.output.plan_path is None:
        raise StepFailed(run.current_step or "build", "no plan path; the plan step must run first")
    return run.output.plan_path


def _not_passed(outcome: ReviewOutcome) -> str:
    if outcome.verdict_source == "final_message":
        return (f"review did not call {SUBMIT_REVIEW_TOOL} (verdict read from text: "
                f"{outcome.verdict or 'none'}); failing closed. Report: {outcome.report_path}")
    return f"review verdict {outcome.verdict} with {outcome.blocker_count} blocker(s). Report: {outcome.report_path}"


async def _review(run: AdwRun, fix_round: int) -> ReviewOutcome:
    inp = run.input
    prompt = slash_command("review", inp.prompt, _plan_path(run))
    result = await run.step(step_spec(inp, "review", prompt, fix_round), counts_as_done=False)

    report_path = Path(inp.working_dir) / "app_review" / f"review_{run.adw_id[:8]}_r{fix_round}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    sub = result.submission
    if isinstance(sub, ReviewSubmission):
        report_path.write_text(sub.report, encoding="utf-8")
        outcome = ReviewOutcome(
            fix_round=fix_round, verdict=sub.verdict, verdict_source="submit_review",
            report_path=str(report_path), blocker_count=sub.blocker_count,
        )
    else:
        # The agent skipped the tool. Keep its final message as the report so /fix has
        # something to read, but never let a text verdict pass.
        report_path.write_text(result.result_text or "(the review agent returned no text)", encoding="utf-8")
        outcome = ReviewOutcome(
            fix_round=fix_round, verdict=parse_verdict(result.result_text),
            verdict_source="final_message", report_path=str(report_path),
        )
    if outcome.passed:
        run.done.add("review")
    run.output.reviews.append(outcome)
    await run.save_output()
    await run.safe("log verdict", run.sink.log_system(
        adw_id=run.adw_id, adw_step="review", level="INFO" if outcome.passed else "WARNING",
        message=f"Review {fix_round}: {outcome.verdict or 'no verdict'} via {outcome.verdict_source}",
        metadata=outcome.model_dump(mode="json"),
    ))
    return outcome


# =============================================================================
# STEP EXECUTION - one agent run against the real SDK
# =============================================================================


def cap_error(spec: StepSpec, out: QueryOutput) -> str | None:
    """Why a finished query must fail its step, or None if it succeeded within caps."""
    caps = spec.caps
    cost = out.total_cost_usd or 0.0
    if out.result_subtype == "error_max_turns" or (out.num_turns or 0) > caps.max_turns:
        return f"{spec.label} hit its max_turns cap ({caps.max_turns})"
    if out.result_subtype == "error_max_budget_usd" or cost > caps.max_budget_usd:
        return f"{spec.label} hit its max_budget_usd cap (${caps.max_budget_usd:.2f}; spent ${cost:.2f})"
    if not out.success:
        return f"{spec.label} failed: {out.error or 'no result'}"
    return None


async def execute_step(run: AdwRun, spec: StepSpec) -> StepResult:
    """Run one step's agent: agent row, hooks, caps, submit tool, usage."""
    started = time.monotonic()
    agent_id = await run.safe("create agent", run.sink.create_agent(
        orchestrator_agent_id=run.orchestrator_agent_id,
        name=f"{spec.label}-{run.adw_id[:8]}",
        model=spec.model,
        working_dir=run.input.working_dir,
        adw_id=run.adw_id,
        adw_step=spec.name,
    ))
    if agent_id:
        await run.safe("agent status", run.sink.update_agent(agent_id=agent_id, status="executing", old_status="idle"))
    await run.safe("log step start", run.sink.log_step_start(
        adw_id=run.adw_id, adw_step=spec.name, agent_id=agent_id,
        payload={"prompt": spec.prompt, "model": spec.model, "caps": spec.caps.model_dump()},
        summary=f"Starting {spec.label}",
    ))

    mcp_servers: dict[str, Any] = {}
    box = SubmitBox()
    if spec.profile.submit:
        server, box = submit_server(spec.profile.submit, run.input.working_dir)
        mcp_servers[SUBMIT_SERVER] = server

    query = QueryInput(
        prompt=spec.prompt,
        options=QueryOptions(
            model=spec.model,
            cwd=run.input.working_dir,
            permission_mode=spec.profile.permission_mode,
            allowed_tools=spec.profile.allowed_tools,
            disallowed_tools=spec.profile.disallowed_tools,
            mcp_servers=mcp_servers,
            hooks=logging_hooks(run, spec.name, agent_id),
            max_turns=spec.caps.max_turns,
            max_budget_usd=spec.caps.max_budget_usd,
        ),
        handlers=message_handlers(run, spec.name, agent_id),
    )

    out: QueryOutput | None = None
    try:
        async with asyncio.timeout(spec.caps.timeout_seconds):
            out = await query_to_completion(query, client_factory=run.client_factory)
        error = cap_error(spec, out)
    except TimeoutError:
        error = f"{spec.label} hit its wall clock cap ({spec.caps.timeout_seconds:.0f}s)"

    usage = out.usage if out else None
    result = StepResult(
        ok=error is None,
        error=error,
        cost_usd=(out.total_cost_usd or 0.0) if out else 0.0,
        num_turns=out.num_turns if out else None,
        session_id=out.session_id if out else None,
        agent_id=agent_id,
        result_text=out.result if out else None,
        submission=box.value,
    )

    if agent_id:
        await run.safe("agent update", run.sink.update_agent(
            agent_id=agent_id,
            session_id=result.session_id,
            status="complete" if result.ok else "blocked",
            input_tokens=usage.input_tokens if usage else None,
            output_tokens=usage.output_tokens if usage else None,
            total_cost=result.cost_usd,
            old_status="executing",
        ))
    await run.safe("log step end", run.sink.log_step_end(
        adw_id=run.adw_id, adw_step=spec.name, agent_id=agent_id,
        status="success" if result.ok else "failed",
        duration_ms=int((time.monotonic() - started) * 1000),
        payload={"session_id": result.session_id, "cost_usd": result.cost_usd,
                 "num_turns": result.num_turns, "error": error},
        summary=f"{spec.label} {'completed' if result.ok else 'failed: ' + (error or '')}",
    ))
    console.print(f"[{'green' if result.ok else 'red'}]{spec.label}: {error or 'ok'} "
                  f"(${result.cost_usd:.2f}, {result.num_turns} turns)[/]")
    return result


def _tool_summary(tool_name: str, tool_input: dict[str, Any]) -> str:
    if tool_name in ("Read", "Write", "Edit", "MultiEdit") and "file_path" in tool_input:
        return f"{tool_name}: {Path(tool_input['file_path']).name}"
    if tool_name == "Bash" and "command" in tool_input:
        return f"Bash: {tool_input['command'][:40]}..."
    if tool_name in ("Glob", "Grep") and "pattern" in tool_input:
        return f"{tool_name}: {tool_input['pattern']}"
    if tool_name == "Skill" and "skill" in tool_input:
        return f"Skill: /{tool_input['skill']}"
    if tool_name == "Task":
        return f"Task: {tool_input.get('description', '')[:30]}..."
    return f"Tool: {tool_name}"


def logging_hooks(run: AdwRun, adw_step: str, agent_id: str | None) -> HooksConfig:
    """PreToolUse, PostToolUse and Stop hooks that log to agent_logs. They always allow:
    a logging failure is reported and the agent carries on."""

    async def log(event_type: str, content: str, payload: dict[str, Any], summary: str) -> None:
        await run.safe(f"{event_type} hook log", run.sink.log_event(
            adw_id=run.adw_id, adw_step=adw_step, event_category="hook", event_type=event_type,
            content=content, agent_id=agent_id, payload=payload, summary=summary,
        ))

    async def pre_tool_use(hook_input: HookInput, tool_use_id: str | None, context: HookContext) -> HookResponse:
        if isinstance(hook_input, PreToolUseInput):
            await log(
                "PreToolUse", f"Using tool: {hook_input.tool_name}",
                {"tool_name": hook_input.tool_name, "tool_input": hook_input.tool_input, "tool_use_id": tool_use_id},
                _tool_summary(hook_input.tool_name, hook_input.tool_input),
            )
        return HookResponse.allow()

    async def post_tool_use(hook_input: HookInput, tool_use_id: str | None, context: HookContext) -> HookResponse:
        if isinstance(hook_input, PostToolUseInput):
            response = hook_input.tool_response
            await log(
                "PostToolUse", f"PostToolUse: {hook_input.tool_name}",
                {"tool_name": hook_input.tool_name, "tool_input": hook_input.tool_input,
                 "tool_use_id": tool_use_id, "tool_response": str(response) if response else None},
                _tool_summary(hook_input.tool_name, hook_input.tool_input) + " ✓",
            )
        return HookResponse.allow()

    async def stop(hook_input: HookInput, tool_use_id: str | None, context: HookContext) -> HookResponse:
        if isinstance(hook_input, StopInput):
            payload = {
                "session_id": hook_input.session_id,
                "stop_hook_active": hook_input.stop_hook_active,
                "permission_mode": hook_input.permission_mode,
            }
            await log("Stop", f"Agent stopped (stop_hook_active={hook_input.stop_hook_active})",
                      payload, f"Stop: session {hook_input.session_id[:8]}")
        return HookResponse.allow()

    return HooksConfig(
        pre_tool_use=[HookMatcher(matcher=None, hooks=[pre_tool_use], timeout=30)],
        post_tool_use=[HookMatcher(matcher=None, hooks=[post_tool_use], timeout=30)],
        stop=[HookMatcher(matcher=None, hooks=[stop], timeout=30)],
    )


def message_handlers(run: AdwRun, adw_step: str, agent_id: str | None) -> MessageHandlers:
    """Log each response block, then queue an AI summary for it."""

    async def log_block(event_type: str, content: str, payload: dict[str, Any], summary: str,
                        summary_input: dict[str, Any]) -> None:
        log_id = await run.safe(f"{event_type} log", run.sink.log_event(
            adw_id=run.adw_id, adw_step=adw_step, event_category="response", event_type=event_type,
            content=content, agent_id=agent_id, payload=payload, summary=summary,
        ))
        if log_id and run.summaries:
            run.summaries.submit(run.adw_id, log_id, summary_input, event_type)

    async def on_assistant_block(block: Any) -> None:
        if isinstance(block, TextBlock):
            text = block.text
            await log_block("TextBlock", text, {"text": text}, f"Response: {text[:150]}", {"content": text})
        elif isinstance(block, ThinkingBlock):
            thinking = block.thinking
            await log_block("ThinkingBlock", thinking, {"thinking": thinking},
                            f"Thinking: {thinking[:100]}", {"thinking": thinking})
        elif isinstance(block, ToolUseBlock):
            await log_block(
                "ToolUseBlock", f"[Tool] {block.name}",
                {"tool_name": block.name, "tool_input": block.input, "tool_use_id": block.id},
                f"Using tool: {block.name}", {"tool_name": block.name, "tool_input": block.input},
            )

    async def on_result(msg: ResultMessage) -> None:
        await run.safe("result log", run.sink.log_event(
            adw_id=run.adw_id, adw_step=adw_step, event_category="response", event_type="result",
            content=msg.result or "", agent_id=agent_id,
            payload={"subtype": msg.subtype, "num_turns": msg.num_turns, "total_cost_usd": msg.total_cost_usd,
                     "usage": msg.usage.model_dump() if msg.usage else None, "session_id": msg.session_id},
            summary=f"Step result: {msg.subtype}",
        ))

    return MessageHandlers(on_assistant_block=on_assistant_block, on_result=on_result)


# =============================================================================
# BACKGROUND SUMMARIES
# =============================================================================


class SummaryPool:
    """Background AI summaries, at most `limit` running at once. Every task is kept
    until it finishes, and drain() settles them before the DB pool closes."""

    def __init__(self, summarize: Callable[..., Awaitable[None]], limit: int = 4):
        self._summarize = summarize
        self._slots = asyncio.Semaphore(limit)
        self._tasks: set[asyncio.Task[None]] = set()

    def submit(self, *args: Any) -> None:
        task = asyncio.create_task(self._run(*args))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _run(self, *args: Any) -> None:
        async with self._slots:
            try:
                await self._summarize(*args)
            except Exception as e:
                console.print(f"[dim red]Summary failed: {type(e).__name__}: {e}[/dim red]")

    async def drain(self, timeout: float = 30.0) -> None:
        """Wait up to `timeout` seconds for queued summaries, then cancel the rest."""
        if not self._tasks:
            return
        _, pending = await asyncio.wait(set(self._tasks), timeout=timeout)
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)


# =============================================================================
# WORKFLOW DRIVER
# =============================================================================


class DbSink:
    """Where a run's records go: the ADW tables, plus WebSocket broadcasts."""

    def __init__(self) -> None:
        from adw_modules import adw_database, adw_logging

        self.open = adw_logging.init_logging
        self.close = adw_logging.close_logging
        self.load = adw_database.get_adw
        self.update_status = adw_logging.update_adw_status
        self.merge_output = adw_database.merge_adw_output
        self.create_agent = adw_database.create_agent
        self.update_agent = adw_database.update_agent
        self.log_event = adw_logging.log_adw_event
        self.log_step_start = adw_logging.log_step_start
        self.log_step_end = adw_logging.log_step_end
        self.log_system = adw_logging.log_system_event

    async def summarize(self, adw_id: str, log_id: str, event_data: dict[str, Any], event_type: str) -> None:
        from adw_modules.adw_database import update_log_summary
        from adw_modules.adw_summarizer import summarize_event
        from adw_modules.adw_websockets import broadcast_adw_event_summary_update

        summary = await summarize_event(event_data, event_type)
        if summary.strip():
            await update_log_summary(log_id, summary)
            await broadcast_adw_event_summary_update(adw_id, log_id, summary)


WorkflowStep = Callable[[AdwRun], Awaitable[None]]


async def run_steps(run: AdwRun, steps: list[WorkflowStep]) -> AdwOutcome:
    try:
        for step in steps:
            await step(run)
    except StepFailed as e:
        return AdwOutcome(status="failed", error_step=e.step, error_message=e.message, output=run.output)
    return AdwOutcome(status="completed", output=run.output)


async def run_workflow(
    adw_id: str,
    steps: list[WorkflowStep],
    total_steps: int,
    sink: Any,
    execute: Executor = execute_step,
    client_factory: Callable[[Any], Any] | None = None,
) -> AdwOutcome:
    """Run a workflow to an outcome and record it on the ADW row. Any exception,
    including one before the first step, ends as status 'failed' with its message."""
    summaries = SummaryPool(sink.summarize)
    run: AdwRun | None = None
    try:
        await sink.open()
        row = await sink.load(adw_id)
        if row is None:
            raise LookupError(f"ADW not found: {adw_id}")
        if not row.get("orchestrator_agent_id"):
            raise ValueError("ADW row has no orchestrator_agent_id")
        run = AdwRun(
            adw_id=adw_id,
            orchestrator_agent_id=str(row["orchestrator_agent_id"]),
            input=AdwInput.model_validate(row.get("input_data") or {}),
            sink=sink,
            total_steps=total_steps,
            execute=execute,
            summaries=summaries,
            client_factory=client_factory,
        )
        outcome = await run_steps(run, steps)
    except Exception as e:
        console.print(Panel(traceback.format_exc(), title="ADW crashed", style="red", width=console.width))
        outcome = AdwOutcome(
            status="failed",
            error_step=run.current_step if run else None,
            error_message=f"{type(e).__name__}: {e}",
            output=run.output if run else AdwOutput(),
        )

    await summaries.drain()
    await _record_outcome(sink, adw_id, outcome, run)
    try:
        await sink.close()
    except Exception:
        console.print(traceback.format_exc())
    return outcome


async def _record_outcome(sink: Any, adw_id: str, outcome: AdwOutcome, run: AdwRun | None) -> None:
    completed = len(run.done) if run else 0
    try:
        await sink.merge_output(adw_id, outcome.output.model_dump(mode="json"))
        await sink.update_status(
            adw_id=adw_id,
            status=outcome.status,
            completed_steps=run.total_steps if outcome.status == "completed" and run else completed,
            error_message=outcome.error_message,
            error_step=outcome.error_step,
        )
        await sink.log_system(
            adw_id=adw_id, adw_step=None, level="INFO" if outcome.status == "completed" else "ERROR",
            message=f"Workflow {outcome.status}" + (f": {outcome.error_message}" if outcome.error_message else ""),
            metadata=outcome.model_dump(mode="json"),
        )
    except Exception:
        # The row cannot be updated; the runner's run.log keeps this trace.
        console.print(Panel(traceback.format_exc(), title="Could not record ADW outcome", style="red",
                            width=console.width))
    console.print(Panel(
        f"status: {outcome.status}\n"
        + (f"error ({outcome.error_step}): {outcome.error_message}\n" if outcome.error_message else "")
        + f"cost: ${outcome.output.total_cost_usd:.2f}\nplan: {outcome.output.plan_path}",
        title=f"ADW {adw_id[:8]} {outcome.status}",
        style="green" if outcome.status == "completed" else "red",
        width=console.width,
    ))


def run_cli(steps: list[WorkflowStep], total_steps: int) -> None:
    parser = argparse.ArgumentParser(description="Run an AI Developer Workflow by ADW ID")
    parser.add_argument("--adw-id", required=True, help="ADW ID (UUID) to execute")
    args = parser.parse_args()
    outcome = asyncio.run(run_workflow(args.adw_id, steps, total_steps, sink=DbSink()))
    sys.exit(0 if outcome.status == "completed" else 1)


__all__ = [
    "AdwInput", "AdwOutcome", "AdwOutput", "AdwRun", "DbSink", "DEFAULT_CAPS", "PlanSubmission",
    "ReviewOutcome", "ReviewSubmission", "STEP_PROFILES", "StepCaps", "StepFailed", "StepResult",
    "StepSpec", "SummaryPool", "build", "cap_error", "execute_step", "plan", "review_must_pass",
    "review_until_pass", "run_cli", "run_steps", "run_workflow", "slash_command", "step_spec",
    "submit_server",
]
