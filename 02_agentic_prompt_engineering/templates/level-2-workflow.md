# Level 2 — Workflow Prompt Template

> Input → Workflow → Output. The Workflow section is the S-tier block. Add the other sections only if you need them.

```md
---
description: <one line used to identify this prompt>
argument-hint: [<first dynamic variable>] [<second dynamic variable>]
allowed-tools: <Read, Write, Edit, Bash, Grep, Glob …>
model: sonnet
---

# <Title>

Follow the `Workflow` to <accomplish X> using `<VARIABLE_1>`, then `Report` the result.

## Variables

<VARIABLE_1>: $1
<VARIABLE_2>: $2
<STATIC_VARIABLE>: <fixed value, e.g. specs/>

## Instructions

- <supporting rule that applies across workflow steps>
- <constraint, e.g. "Do not modify files outside <dir>">

## Codebase Structure

- <path> — <one-line role>
- <path> — <one-line role>

## Workflow

1. <Step> — reference variables by NAME, e.g. read `<VARIABLE_1>`
   - <sub-detail>
2. <Step>
3. <Step>

## Report

- <exact output format: bullets / table / JSON schema>
- <required fields, e.g. `git diff --stat`>
```

## Example (from `10. agentic-prompt-engineering/.claude/commands/prime.md`)

```md
---
description: Gain a general understanding of the codebase
---

# Prime

Execute the `Workflow` and `Report` sections to understand the codebase then summarize your understanding.

## Workflow

- Run `git ls-files` to list all files in the repository.
- Read `README.md` for an overview of the project.

## Report

Summarize your understanding of the codebase.
```

**Model field:** use the alias (`opus`, `sonnet`, `haiku`) so the prompt follows the latest model automatically.
