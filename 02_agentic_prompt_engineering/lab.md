# Lab 2 · Promote a One-Liner to a Control-Flow Prompt

> **Goal:** turn a level-1 prompt ("backtest my strategy and tell me if it's good") into a level-3 prompt with variables, a numbered workflow, early returns and a loop.

**Pillar:** [02 Agentic Prompt Engineering](README.md) · **Time:** 30 minutes · **Cost:** none

## Start
```bash
cp labs/starters/lab2/backtest.md /tmp/backtest.md
```

## Steps
1. Add frontmatter with `description` and `argument-hint` ([Metadata](README.md#section-tier-list-graded-for-user-prompts)).
2. Add `## Variables` with at least one dynamic variable (`STRATEGY: $1`) and one static one (`RESULTS_DIR: research/backtests/`).
3. Write a numbered `## Workflow`. Add at least one `STOP` early return, for example when an argument is missing or the date range is too short.
4. Wrap the repeated part in a `<param-loop>` … `</param-loop>` block ([L3](README.md#l3--control-flow)).
5. End with `## Report` that fixes the output format.

Start from the [level-3 template](templates/level-3-control-flow.md) if you want a skeleton.

## Check
```bash
labs/check_lab.py 2 /tmp/backtest.md
```

Reference solution: [`labs/solutions/lab2/backtest.md`](../labs/solutions/lab2/backtest.md).

## Stretch
Write the level-6 meta prompt that generates prompts in this exact format, then use it to generate `/hypothesis`.
