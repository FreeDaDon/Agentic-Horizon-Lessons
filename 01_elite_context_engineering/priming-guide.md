# Priming Guide — Replace Memory Bloat with Task Primes

> **BLUF:** A prime is a small, reusable slash command that loads exactly the context one *type* of task needs. Keep `CLAUDE.md` to universals, write one prime per recurring area of focus, stack primes rather than duplicating them, and always prime a fresh agent after `/clear`.

## The base prime (from the lesson code)

[`9. elite-context-engineering/.claude/commands/prime.md`](../9.%20elite-context-engineering/.claude/commands/prime.md):

```md
---
description: Gain a general understanding of the codebase
---

# Prime

Execute the `Run`, `Read` and `Report` sections to understand the codebase then summarize your understanding.

## Run

git ls-files

## Read

README.md

## Report

Summarize your understanding of the codebase.
```

## Stacked prime (prime a sub-area on top of the base)

[`prime_cc.md`](../9.%20elite-context-engineering/.claude/commands/prime_cc.md) runs the base prime first, then reads the agentic-layer files:

```md
## Run
Read and execute the .claude/commands/prime.md file top to bottom.

## Read
.claude/commands/**
.claude/output-styles/**
.claude/hooks/context_bundle_builder.py
.claude/settings.json
```

## Template for a domain prime

Save as `.claude/commands/prime_<area>.md`:

```md
---
description: Prime the agent for <area> work
allowed-tools: Read, Glob, Grep, Bash(git ls-files*)
---

# Prime <Area>

Execute the `Run`, `Read`, and `Report` sections to understand <area> then summarize your understanding.

## Run
Read and execute .claude/commands/prime.md top to bottom.

## Codebase Structure
- <dir>/<file> — <one-line role>
- <dir>/<file> — <one-line role>

## Read
IMPORTANT: Read these files exclusively.
- <path 1>
- <path 2>

## Report
Summarize your understanding of <area> in at most 10 bullets: key files, data flow, invariants, and the commands to test it.
```

The `Codebase Structure` section is a **context map**. It tells the agent *where* things are without reading them, which saves search tool calls. `Read` is the short list the agent actually loads.

## Rules

| Rule | Why |
|---|---|
| `CLAUDE.md` holds only what 100% of agents need 100% of the time | Everything else becomes stale or contradictory over time |
| One prime per recurring focus area (`prime_bug`, `prime_feature`, `prime_cc`, `prime_<module>`) | You control the starting state per task type |
| Stack by calling the base prime; don't copy its contents | One place to update |
| End with a short `Report` | Proves the agent loaded the right context, and keeps output small |
| `/clear` then prime again rather than `/compact` | Known state instead of an unknown summary |
| A prime you keep adding to is becoming an **expert** | Promote it to plan/build/improve with an `## Expertise` section ([pillar 5](../05_agent_experts/README.md)) |

## Domain primes

| Domain | Prime | Reads |
|---|---|---|
| Quant trading | `/prime_strategy` | strategy module, signal interface, risk limits config, backtest runner entrypoint |
| Cybersecurity | `/prime_ir` | incident runbook, asset inventory for affected hosts, detection rule being tuned |
| Systems automation | `/prime_infra` | module map, the environment's `tfvars`, the CI deploy workflow |
| Software | `/prime_feature` | README, the feature's directory map, related tests |

← [Pillar 1 overview](README.md)
