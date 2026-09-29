# Level 4 — Delegate Prompt Template

> The primary agent writes prompts for other agents and launches them. Variables carry the **agent config** (count, model, tools). Every delegated prompt must be self-contained, because sub-agents are stateless.

## A. Parallel sub-agents (from `parallel_subagents.md`)

```md
---
description: Launch parallel agents to accomplish a task.
argument-hint: [prompt request] [count]
---

# Parallel Subagents

Follow the `Workflow` below to launch `COUNT` agents in parallel to accomplish a task detailed in the `PROMPT_REQUEST`.

## Variables

PROMPT_REQUEST: $1
COUNT: $2

## Workflow

1. Parse Input Parameters
   - Extract PROMPT_REQUEST to understand the task
   - Determine COUNT (use provided value or infer from task complexity)
2. Design Agent Prompts
   - Create detailed, self-contained prompts for each agent
   - Include specific instructions on what to accomplish
   - Define clear output expectations
   - Remember agents are stateless and need complete context
3. Launch Parallel Agents
   - Use the Task tool to spawn N agents simultaneously in a single parallel batch
4. Collect & Summarize Results
   - Gather outputs from all completed agents
   - Synthesize findings into a cohesive response
```

## B. Background primary agent (condensed from `background.md`)

```md
---
description: Run a Claude Code instance in the background, reporting to a file
argument-hint: [prompt] [model] [report-file]
---

# Background

Run a Claude Code instance in the background to perform `USER_PROMPT` autonomously while you continue working.

## Variables

USER_PROMPT: $1
MODEL: $2 or sonnet if not provided
REPORT_FILE: $3 or agents/background/background-report-<date_time>.md

## Workflow

1. Create `agents/background/`; write a `REPORT_FILE` skeleton with `## Progress` and `## Results`.
2. Run in the background:
   claude --model "MODEL" --output-format text --dangerously-skip-permissions \
     --append-system-prompt "You are a background agent. Continuously update REPORT_FILE ## Progress every few tool calls. On finish, fill ## Results and rename the file with a -complete suffix." \
     --print "USER_PROMPT"
3. Tell the user the report path and how to follow it (`tail -f`).
```

**Safety:** background agents skip permission prompts and spend real money. Run them in a sandbox or container, set a budget, and never point them at production credentials.
