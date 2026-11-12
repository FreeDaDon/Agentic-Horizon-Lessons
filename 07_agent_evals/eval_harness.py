#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6", "pytest>=8"]
# ///
"""
Minimal agent eval harness: golden tasks, hidden graders, k runs, a scoreboard.

  eval_harness.py run --suite 07_agent_evals/tasks --agent claude --model sonnet -k 3
  eval_harness.py report 07_agent_evals/results/*.jsonl
  eval_harness.py check --suite 07_agent_evals/tasks

A task is a folder with task.yaml, repo/ (the workspace fixture), grader/ (hidden tests,
copied in only after the agent finishes) and solution.patch or solution/ (the reference).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import subprocess
import sys
import tempfile
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from functools import partial
from pathlib import Path
from statistics import mean
from typing import Callable

import yaml

HERE = Path(__file__).resolve().parent
TASK_KEYS = {"prompt", "grader", "timeout_s", "max_turns", "max_budget_usd"}
GIT = ["git", "-c", "user.name=eval", "-c", "user.email=eval@localhost", "-c", "commit.gpgsign=false"]


@dataclass(frozen=True)
class Task:
    id: str
    dir: Path
    prompt: str
    grader: list[str]
    timeout_s: int
    max_turns: int
    max_budget_usd: float


@dataclass(frozen=True)
class AgentResult:
    is_error: bool
    cost_usd: float | None
    turns: int | None


@dataclass(frozen=True)
class Agent:
    name: str
    model: str | None
    run: Callable[[Task, Path], AgentResult]


@dataclass(frozen=True)
class RunRecord:
    task: str
    agent: str
    model: str | None
    run: int
    passed: bool
    agent_error: bool
    cost_usd: float | None
    turns: int | None
    wall_s: float
    grader_output: str
    started_at: str


def load_task(task_dir: Path) -> Task:
    spec = yaml.safe_load((task_dir / "task.yaml").read_text())
    unknown = set(spec) - TASK_KEYS
    if unknown:
        raise ValueError(f"{task_dir}: unknown task.yaml keys {sorted(unknown)}")
    if not isinstance(spec.get("grader"), list):
        raise ValueError(f"{task_dir}: grader must be an argv list, not a shell string")
    for required in ("repo", "grader"):
        if not (task_dir / required).is_dir():
            raise ValueError(f"{task_dir}: missing {required}/")
    if not ((task_dir / "solution.patch").is_file() or (task_dir / "solution").is_dir()):
        raise ValueError(f"{task_dir}: missing solution.patch or solution/")
    return Task(
        id=task_dir.name,
        dir=task_dir,
        prompt=spec["prompt"],
        grader=spec["grader"],
        timeout_s=int(spec.get("timeout_s", 600)),
        max_turns=int(spec.get("max_turns", 20)),
        max_budget_usd=float(spec.get("max_budget_usd", 1.0)),
    )


def load_suite(suite_dir: Path) -> list[Task]:
    return [load_task(d) for d in sorted(suite_dir.iterdir()) if (d / "task.yaml").is_file()]


def parse_claude_result(stdout: str) -> AgentResult:
    """Parse `claude -p --output-format json` stdout. Anything unparseable is an agent error."""
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        return AgentResult(is_error=True, cost_usd=None, turns=None)
    if isinstance(data, list):  # --verbose prints the whole message list; the result is last
        data = next((m for m in reversed(data) if m.get("type") == "result"), {})
    return AgentResult(
        is_error=bool(data.get("is_error", True)),
        cost_usd=data.get("total_cost_usd"),
        turns=data.get("num_turns"),
    )


def run_claude(task: Task, workspace: Path, model: str) -> AgentResult:
    argv = ["claude", "-p", task.prompt, "--output-format", "json", "--model", model,
            "--max-turns", str(task.max_turns), "--max-budget-usd", str(task.max_budget_usd),
            "--permission-mode", "acceptEdits"]
    try:
        proc = subprocess.run(argv, cwd=workspace, capture_output=True, text=True, timeout=task.timeout_s)
    except subprocess.TimeoutExpired:
        return AgentResult(is_error=True, cost_usd=None, turns=None)
    return parse_claude_result(proc.stdout)


def run_oracle(task: Task, workspace: Path) -> AgentResult:
    patch = task.dir / "solution.patch"
    if patch.is_file():
        subprocess.run(["git", "apply", str(patch)], cwd=workspace, check=True, capture_output=True)
    else:
        shutil.copytree(task.dir / "solution", workspace, dirs_exist_ok=True)
    return AgentResult(is_error=False, cost_usd=0.0, turns=0)


def run_noop(task: Task, workspace: Path) -> AgentResult:
    return AgentResult(is_error=False, cost_usd=0.0, turns=0)


AGENTS: dict[str, Callable[[str | None], Agent]] = {
    "claude": lambda model: Agent("claude", model, partial(run_claude, model=model)),
    "oracle": lambda model: Agent("oracle", None, run_oracle),
    "noop": lambda model: Agent("noop", None, run_noop),
}


def prepare_workspace(task: Task, workspace: Path) -> None:
    shutil.copytree(task.dir / "repo", workspace)
    for cmd in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "fixture"]):
        subprocess.run(GIT + cmd, cwd=workspace, check=True, capture_output=True)


def grade(task: Task, workspace: Path) -> tuple[bool, str]:
    shutil.copytree(task.dir / "grader", workspace, dirs_exist_ok=True)
    argv = [sys.executable if a == "{python}" else a for a in task.grader]
    try:
        proc = subprocess.run(argv, cwd=workspace, capture_output=True, text=True, timeout=task.timeout_s)
    except subprocess.TimeoutExpired:
        return False, f"grader timed out after {task.timeout_s}s"
    return proc.returncode == 0, (proc.stdout + proc.stderr)[-1500:]


def run_task(task: Task, agent: Agent, run: int) -> RunRecord:
    started_at = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    with tempfile.TemporaryDirectory(prefix=f"eval-{task.id}-") as tmp:
        workspace = Path(tmp) / "workspace"
        prepare_workspace(task, workspace)
        t0 = time.monotonic()
        result = agent.run(task, workspace)
        wall_s = round(time.monotonic() - t0, 2)
        passed, output = grade(task, workspace)
    return RunRecord(task.id, agent.name, agent.model, run, passed, result.is_error,
                     result.cost_usd, result.turns, wall_s, output, started_at)


def run_suite(suite_dir: Path, agent: Agent, k: int, out: Path | None) -> list[RunRecord]:
    tasks = load_suite(suite_dir)
    records = []
    sink = out.open("a") if out else None
    try:
        for task in tasks:
            for run in range(k):
                record = run_task(task, agent, run)
                records.append(record)
                status = "PASS" if record.passed else "FAIL"
                print(f"{status} {task.id} run {run} ({record.wall_s}s)", file=sys.stderr)
                if sink:
                    sink.write(json.dumps(asdict(record)) + "\n")
                    sink.flush()
    finally:
        if sink:
            sink.close()
    return records


def check(suite_dir: Path) -> list[str]:
    """Grader sanity: every task must fail a no-op run and pass the reference solution."""
    problems = []
    for agent_name, must_pass in (("noop", False), ("oracle", True)):
        for record in run_suite(suite_dir, AGENTS[agent_name](None), k=1, out=None):
            if record.passed != must_pass:
                verb = "fails" if must_pass else "passes"
                problems.append(f"{record.task}: grader {verb} the {agent_name} run")
    return problems


def _fmt(values: list[float | None], spec: str) -> str:
    known = [v for v in values if v is not None]
    return format(mean(known), spec) if known else "n/a"


def report(paths: list[Path], scoreboard: Path | None) -> str:
    records = [json.loads(line) for p in paths for line in p.read_text().splitlines() if line.strip()]
    by_config: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for r in records:
        config = r["agent"] + (f"/{r['model']}" if r["model"] else "")
        by_config[config][r["task"]].append(r)

    lines = ["| Config | Task | Passed | pass@k | Mean cost (USD) | Mean turns | Mean wall (s) |",
             "|---|---|---|---|---|---|---|"]
    summaries = []
    for config, tasks in sorted(by_config.items()):
        for task, runs in sorted(tasks.items()):
            passed = sum(r["passed"] for r in runs)
            lines.append(
                f"| {config} | {task} | {passed}/{len(runs)} | {int(passed > 0)} "
                f"| {_fmt([r['cost_usd'] for r in runs], '.4f')} | {_fmt([r['turns'] for r in runs], '.1f')} "
                f"| {_fmt([r['wall_s'] for r in runs], '.1f')} |")
        per_run: dict[int, list[bool]] = defaultdict(list)
        for runs in tasks.values():
            for r in runs:
                per_run[r["run"]].append(r["passed"])
        rates = [sum(v) / len(v) for v in per_run.values()]
        flat = [r for runs in tasks.values() for r in runs]
        total_cost = sum(r["cost_usd"] or 0 for r in flat)
        summaries.append(
            f"- **{config}**: {sum(r['passed'] for r in flat)}/{len(flat)} runs passed. "
            f"Suite pass rate per run ranged {min(rates):.0%} to {max(rates):.0%} over {len(rates)} runs. "
            f"Total cost ${total_cost:.4f}.")

    today = dt.date.today().isoformat()
    sources = ", ".join(p.name for p in paths)
    markdown = "\n".join([f"## {today} ({sources})", "", *lines, "", *summaries, ""])
    if scoreboard:
        with scoreboard.open("a") as f:
            f.write("\n" + markdown)
    return markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="run an agent k times over every task")
    run_p.add_argument("--suite", type=Path, default=HERE / "tasks")
    run_p.add_argument("--agent", choices=sorted(AGENTS), required=True)
    run_p.add_argument("--model", help="model alias for the claude agent: opus, sonnet or haiku")
    run_p.add_argument("-k", type=int, default=3)
    run_p.add_argument("--out", type=Path)

    report_p = sub.add_parser("report", help="print a scoreboard and append it to scoreboard.md")
    report_p.add_argument("results", type=Path, nargs="+")
    report_p.add_argument("--scoreboard", type=Path, default=HERE / "scoreboard.md")
    report_p.add_argument("--no-append", action="store_true")

    check_p = sub.add_parser("check", help="fail if any grader passes a no-op run or fails the reference")
    check_p.add_argument("--suite", type=Path, default=HERE / "tasks")

    args = parser.parse_args(argv)
    if args.command == "run":
        if args.agent == "claude" and not args.model:
            parser.error("--model is required for the claude agent")
        out = args.out or HERE / "results" / f"{dt.date.today().isoformat()}-{args.model or args.agent}.jsonl"
        out.parent.mkdir(parents=True, exist_ok=True)
        records = run_suite(args.suite, AGENTS[args.agent](args.model), args.k, out)
        print(f"{sum(r.passed for r in records)}/{len(records)} runs passed; results in {out}")
        return 0
    if args.command == "report":
        print(report(args.results, None if args.no_append else args.scoreboard))
        return 0
    problems = check(args.suite)
    for p in problems:
        print(p)
    print("grader sanity: " + ("FAILED" if problems else "ok"))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
