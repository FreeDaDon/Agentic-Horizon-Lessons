# The Self-Improve Loop — ACT → LEARN → REUSE

> **BLUF:** After every change in an expert's domain, a fresh agent compares the expertise file against the real code, fixes what's wrong, trims it to the size cap, parse-checks it, and reports. If nothing changed, it says so and stops. Run it until stable to bootstrap, then after every build.

## The loop

```
          ┌──────────── REUSE ────────────┐
          │ /experts:<d>:plan  (expertise │
          │  → mental model → /plan)      │
          └──────────────┬────────────────┘
                         ▼
          ┌──────────── ACT ──────────────┐
          │ /build <plan_path>            │
          │  (fresh agent, spec only)     │
          └──────────────┬────────────────┘
                         ▼
          ┌──────────── LEARN ────────────┐
          │ /experts:<d>:self-improve true│
          │  (git diff → validate → trim) │
          └──────────────┬────────────────┘
                         └──► expertise.yaml ──► next REUSE
```

Each box is a **separate agent** (a fresh context window). That's pillar 1's "one agent, one purpose" applied to learning.

## `self-improve.md` template (derived from lessons 13 and 14)

Save as `.claude/commands/experts/<domain>/self-improve.md`:

```md
---
allowed-tools: Read, Grep, Glob, Bash, Edit, Write, TodoWrite
description: Self-improve <Domain> expertise by validating against the source of truth
argument-hint: [check_git_diff (true/false)] [focus_area (optional)]
---

# Purpose

You maintain the <Domain> expert's accuracy by comparing the expertise file against the
source of truth (the code/system). Follow the `Workflow` to detect and fix differences,
missing pieces, or outdated information so the file stays an accurate **mental model**.

## Variables

CHECK_GIT_DIFF: $1 default to false
FOCUS_AREA: $2 default to empty string
EXPERTISE_FILE: .claude/commands/experts/<domain>/expertise.yaml
MAX_LINES: 1000

## Instructions

- Always validate expertise against the real implementation, not assumptions
- Focus exclusively on <Domain>; prioritize FOCUS_AREA if given
- Maintain the YAML structure; enforce MAX_LINES strictly
- Prefer actionable, high-value expertise over verbose documentation
- Do NOT write summaries of work done; record only durable facts about the domain
- Write as a principal engineer: clear and concise, for future engineers
- If nothing needs changing after a thorough search, report that and stop

## Workflow

1. If CHECK_GIT_DIFF is "true", run `git diff` and `git log --oneline -10`; note <Domain>-related changes
2. Read the entire EXPERTISE_FILE; note sections that look stale
3. Read every key file the expertise references (plus files from step 1) and compare:
   <domain checklist — entities, signatures, paths, line numbers, flows, configs>
4. List discrepancies: missing / outdated / changed / removed-but-documented / incorrect
5. Update EXPERTISE_FILE: add, update, remove; keep paths and line numbers accurate
6. Run `wc -l EXPERTISE_FILE`. While it exceeds MAX_LINES, trim verbose descriptions,
   redundant examples, and low-priority edge cases; re-count; record what was trimmed
7. Validate: `python3 -c "import yaml; yaml.safe_load(open('EXPERTISE_FILE'))"`; fix and repeat on error

## Report

- Summary: git diff checked (y/n), focus area, discrepancies found/fixed, final lines / MAX_LINES
- Discrepancies Found: what, where in the source, how fixed
- Updates Made
- Line Limit Enforcement
- Validation Results
- Codebase References: files + line ranges
```

## `plan_build_improve.md` template

```md
---
allowed-tools: Task, TaskOutput, TodoWrite
description: Plan, build, and self-improve with the <Domain> expert
argument-hint: [user request]
---

# <Domain> Plan-Build-Improve

Run the full expert loop for `USER_PROMPT`. Each step runs in a fresh sub-agent with complete instructions.

## Variables

USER_PROMPT: $ARGUMENTS

## Workflow

1. Task(general-purpose): "Run /experts:<domain>:plan '<USER_PROMPT>'. Return ONLY the path to the generated plan file."
2. Task(general-purpose): "Run /build <plan_path>. Implement the entire plan. Return a summary of files changed."
3. Task(general-purpose): "Run /experts:<domain>:self-improve true. Return the self-improvement report."
4. Report
- Each sub-agent starts fresh with no prior context. Provide complete instructions.
- DO NOT STOP between steps.

## Report

- Plan path · files changed · expertise updates (or "none needed")
```

## Operating rules

| Rule | Reason |
|---|---|
| The code is the source of truth; expertise is validated before it's used | Stale memory is worse than no memory |
| Only self-improve writes the expertise file | One writer means no drift and an auditable diff |
| Cap size (1000 lines) and trim by priority | Expertise is context; it follows pillar 1's budget |
| Parse-check after every write | A broken YAML file silently kills the expert |
| "Nothing to update" is a valid, expected outcome | It stops the agent from inventing churn |
| Review expertise diffs in PRs | Agent-owned, human-audited |
| Bootstrap: loop self-improve until it reports no discrepancies | Builds the full model from a seed |

## Failure modes seen in the lesson code

| Failure | Mitigation |
|---|---|
| Unbounded runtime memory (autocomplete history) | Apply the same `MAX_*` cap and trim policy to runtime stores |
| In-memory session maps lost on restart (Nile) | Persist session IDs alongside the expertise record |
| Declared but unused variables (`HUMAN_IN_THE_LOOP`) | Remove them, or implement a real approval step between plan and build |
| No automatic trigger for self-improve | Run it from the ADW after the build (pillar 6) or from a post-merge CI job |

← [Pillar 5 overview](README.md)
