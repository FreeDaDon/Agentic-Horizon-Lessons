# Lab 4 · Write a Read-Only Fleet Template

> **Goal:** write a worker template the orchestrator can spawn many times: a sub-agent file whose tools are read-only, whose model fits the job, and whose report is short enough to summarize.

**Pillar:** [04 Multi-Agent Orchestration](README.md) · **Time:** 20 minutes · **Cost:** none

## Start
```bash
mkdir -p /tmp/lab4/.claude/agents && cp labs/starters/lab4/.claude/agents/data-scout.md /tmp/lab4/.claude/agents/
```

## Steps
1. Make `name` match the file name, and write a `description` that says what the agent does and when the orchestrator should use it.
2. Restrict `tools` to `Read, Glob, Grep`. Since the orchestrator fix in this repo, `command_agent` keeps a template's tools on every command, so this restriction now holds for the agent's whole life ([fleet CRUD](fleet-crud.md)).
3. Use a model alias. A scout is a `haiku` job.
4. Write `## Purpose`, `## Workflow` (with a stopping rule) and `## Report` sections.

## Check
```bash
labs/check_lab.py 4 /tmp/lab4/.claude/agents/data-scout.md
```

Reference solution: [`labs/solutions/lab4/.claude/agents/data-scout.md`](../labs/solutions/lab4/.claude/agents/data-scout.md).

## Stretch
Copy the template into lesson 14's `.claude/agents/`, start the orchestrator, and ask it to run three scouts in parallel over different folders. Watch the summarized events in the UI.
