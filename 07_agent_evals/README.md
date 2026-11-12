# 07 · Agent Evals — Measure Whether the Agent Did the Job

> **BLUF:** Tests on helpers and hooks prove the plumbing. They say nothing about whether an agent, a prompt or an ADW actually solves the task. An **eval** answers that. Give the agent a small, hermetic golden task. Grade it with a **hidden** deterministic check the agent never sees. Prove the grader can fail (a no-op run) and can pass (a reference solution). Run each config k ≥ 3 times and report pass rate, cost, turns and spread. Change one thing at a time: a model alias or a prompt version, never both.

**Code:** [`eval_harness.py`](eval_harness.py) (stdlib plus PyYAML and pytest, PEP 723 script), four golden tasks in [`tasks/`](tasks/), the running [`scoreboard.md`](scoreboard.md), and tests in [`tests/test_agent_evals.py`](../tests/test_agent_evals.py).

**Core belief:** *An agent you have not measured is an agent you are guessing about.* A review step that says PASS is a claim. A hidden test that passes is evidence.

---

## Eval types

| Type | How it grades | Use it when | Weakness |
|---|---|---|---|
| **Deterministic grader** | Hidden tests or a script, run after the agent finishes | The task has a checkable outcome: code behavior, a file's content, a CLI's output | Only measures what the tests cover |
| **Model-graded rubric** | A second model scores the output against a written rubric | The output is prose or design, and no script can judge it | The grader is itself a model. It drifts, flatters long answers and shares blind spots with the agent |
| **Reviewer calibration** | A deterministic grader checks whether an ADW review verdict agrees with hidden tests | You want to trust a `/review` step to gate a pipeline | One task only catches one kind of miss (see below) |

Prefer deterministic graders. Accept a model-graded rubric only when no script can judge the output, and then pin the grader model and rubric version, score with a fixed scale, and spot-check its scores by hand against a few labeled outputs before you trust a trend.

**Reviewer calibration** is how you earn trust in the review step of an ADW (see [pillar 6](../06_building_agentic_layers/README.md)). The [`review_verdict`](tasks/review_verdict/) task hands the agent a diff and a spec. The agent writes `REVIEW.md` ending in `VERDICT: PASS` or `VERDICT: FAIL`. The hidden grader applies the diff to a pristine copy, runs the spec checks itself, and passes only if the verdict agrees. The shipped diff is known-bad, so this task catches a reviewer that waves bad code through. A reviewer that always says FAIL would also pass it. A full calibration set pairs every known-bad diff with a known-good one.

---

## Golden-task design

A golden task is a folder under `tasks/<id>/`:

| Path | Purpose | Who sees it |
|---|---|---|
| `task.yaml` | `prompt`, `grader` (an argv list), `timeout_s`, `max_turns`, `max_budget_usd` | the harness |
| `repo/` | The fixture workspace, copied fresh and `git init`ed for every run | the agent |
| `grader/` | Hidden tests, copied in **only after** the agent finishes | the grader |
| `solution.patch` or `solution/` | The reference solution | the oracle run |

Rules that keep a task honest:

- **Small.** One behavior per task. A task the agent finishes in a few turns gives a signal you can rerun cheaply.
- **Hermetic.** Stdlib only, no network, no keys. The same input must grade the same way tomorrow.
- **Hidden grader.** The agent never sees the tests, so it cannot overfit to them. `tests/test_agent_evals.py` proves the grader files are absent while the agent runs.
- **Solvable.** A reference solution must pass. If the oracle fails, the task or the grader is broken.
- **Failable.** A no-op run must fail. If doing nothing passes, the grader measures nothing.
- **Tamper-resistant.** Graders run pytest with `--noconftest`, so a `conftest.py` the agent writes cannot rewrite results. The review grader keeps its own pristine copies of the base file and the diff.

`eval_harness.py check` enforces the last two rules for every task in the suite. Run it whenever you add or edit a task.

| Shipped task | What the agent must do | Hidden grader checks |
|---|---|---|
| [`off_by_one`](tasks/off_by_one/) | Fix a 1-indexed pager that skips the first page | first page, partial last page, page past the end |
| [`json_flag`](tasks/json_flag/) | Add `--json` to an argparse CLI | JSON output and the unchanged plain output |
| [`empty_input`](tasks/empty_input/) | Make `summarize([])` return a null summary | empty list, empty generator, non-empty unchanged |
| [`review_verdict`](tasks/review_verdict/) | Review a diff against a spec and write a verdict | verdict agrees with the spec checks on the patched code |

---

## Running it

```bash
# grader sanity: noop must fail every task, oracle must pass every task
07_agent_evals/eval_harness.py check

# 3 runs per task with the headless CLI; appends JSONL records
07_agent_evals/eval_harness.py run --suite 07_agent_evals/tasks --agent claude --model sonnet -k 3 \
  --out 07_agent_evals/results/2026-11-12-sonnet.jsonl

# markdown scoreboard, printed and appended to scoreboard.md
07_agent_evals/eval_harness.py report 07_agent_evals/results/*.jsonl
```

The `claude` agent runs `claude -p <prompt> --output-format json --model <alias> --max-turns N --max-budget-usd B --permission-mode acceptEdits` inside the workspace and reads `total_cost_usd`, `num_turns` and `is_error` from the JSON. Output it cannot parse counts as an agent error, never as a pass. `acceptEdits` lets the agent edit files but not run unapproved shell commands, which keeps an eval run from touching anything outside its temp workspace.

| Agent | What it does | Why it exists |
|---|---|---|
| `claude` | The real agent under test | the measurement |
| `oracle` | Applies `solution.patch` or copies `solution/` | proves each task is solvable |
| `noop` | Does nothing | proves each grader can fail |

---

## Metrics

| Metric | Source | Read it as |
|---|---|---|
| Pass rate | hidden grader exit code | the headline number, per task and per suite |
| pass@k | any of k runs passed | the ceiling if you retry; the gap to pass rate is flakiness |
| Cost (USD) | `total_cost_usd` | spend per attempt; multiply by retries for spend per success |
| Turns | `num_turns` | how directly the agent worked; rising turns at a flat pass rate is a regression |
| Wall time | measured around the agent call | latency for out-of-loop pipelines |
| Agent error | `is_error`, a timeout or unparseable output | separates "could not finish" from "finished wrong" |

## Comparing model aliases and prompt versions

- **Change one variable per comparison.** Run `--model haiku`, then `--model sonnet`, on the same suite at the same k. For a prompt change, keep the alias fixed and compare prompt versions.
- **Name the result file after the config** (`2026-11-12-sonnet.jsonl`, `2026-11-12-review-prompt-v2.jsonl`) so the scoreboard rows say what changed.
- **Decide on cost per success, not cost per run.** A cheaper alias that passes half as often can cost more per solved task.
- **Freeze the suite while comparing.** A task edit invalidates every earlier row for that task.

## Noise

Agents are nondeterministic. One run is an anecdote.

- Run **k ≥ 3** per task per config. The report prints the per-run suite pass rate range for each config.
- Treat a difference smaller than that range as noise. Rerun with a larger k before acting on it.
- A task that flips between runs of the same config is telling you its prompt is ambiguous or its grader is flaky. Fix the task before using it to rank configs.

---

## Domain adaptation

| Domain | Golden task | Deterministic grader | Must-fail check |
|---|---|---|---|
| Software | fix a bug, add a flag, handle an edge case | hidden pytest suite | the unmodified repo fails it |
| Quant trading | implement a signal or fix a backtest bug on a frozen dataset | backtest metrics within tolerance of the reference, plus **leakage checks**: shuffle future bars and confirm the signal's edge disappears, assert no feature reads a timestamp after the decision bar | the reference signal shifted one bar into the future must fail the leakage check |
| Cybersecurity | write or tune a detection rule | replay labeled logs; grade on **precision and recall** against thresholds | an empty rule set (zero recall) and a match-everything rule (low precision) both fail |
| Systems automation | write an IaC change for a stated goal | **plan-diff grader**: run `plan` in a sandbox and compare the resource diff to the expected one; any destroy not in the expected diff fails | an empty change set fails; a plan with an unexpected destroy fails |

**Next:** [pillar 6](../06_building_agentic_layers/README.md) (the ADW review step this calibrates) · [scoreboard.md](scoreboard.md)
