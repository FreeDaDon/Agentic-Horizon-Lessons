# Level 5 — Higher-Order Prompt Template

> A prompt that takes **another prompt or plan file** as input. The outer workflow (read, implement, validate, report) stays fixed; the inner plan changes each run.

```md
---
description: Execute a plan/spec file end to end
argument-hint: [path-to-plan]
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# Build From Plan

Follow the `Workflow` to implement `PATH_TO_PLAN`, then `Report` the completed work.

## Variables

PATH_TO_PLAN: $ARGUMENTS

## Workflow

- If no `PATH_TO_PLAN` is provided, STOP immediately and ask the user to provide it.
- Read the plan at `PATH_TO_PLAN`. Think hard about the plan and implement it into the codebase.
- Execute every command listed under the plan's `Validation Commands`; fix failures before finishing.

## Report

- Summarize the work in a concise bullet list.
- Report files and total lines changed with `git diff --stat`.
```

## Pairings

| Planner (produces the input) | Higher-order executor |
|---|---|
| `/quick-plan "<request>"` → `specs/<name>.md` | `/build specs/<name>.md` |
| Expert plan (`/experts:<x>:plan`) | Expert build (`/experts:<x>:build <path>`) |
| `/plan_w_scouters` (lesson 12) | `/build_in_parallel <path>` (lesson 12) |

Run the executor in a **fresh agent** so its context holds only the plan (pillar 1, technique #6).
