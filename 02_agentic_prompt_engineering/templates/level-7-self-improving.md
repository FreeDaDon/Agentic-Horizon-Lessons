# Level 7 — Self-Improving Prompt (Agent Expert)

> The prompt's `## Expertise` section is **maintained by agents**. A plan prompt and a build prompt each carry expertise; an improve prompt reads recent changes and updates **only** those Expertise sections, leaving workflows stable.

## Plan / Build prompt skeleton

```md
---
description: Plan a <domain> change with expert knowledge
argument-hint: [feature description]
---

# <Domain> Expert Plan

You are a <Domain> Expert specializing in planning <domain> changes.

## Variables
USER_PROMPT: $ARGUMENTS
SPEC_DIR: specs/experts/<domain>/

## Instructions
- Read prerequisite docs to establish expertise
- Analyze existing <domain> files before proposing changes

## Expertise
<!-- Updated by /experts:<domain>:improve — do not hand-edit workflow below -->
### File structure
- <path> — <role>
### Patterns that work
- <pattern + why>
### Pitfalls seen
- <pitfall + fix>

## Workflow
1. Read docs in `ai_docs/` relevant to <domain>
2. Inspect current implementation
3. Write the spec to `SPEC_DIR/<name>.md`

## Report
- Path to the spec and 3–5 key decisions
```

## Improve prompt (condensed from `cc_hook_expert_improve.md`)

```md
---
description: Review recent <domain> changes and update expert knowledge
---

# <Domain> Expert Improve

You are a <Domain> Expert specializing in continuous improvement.

## Instructions
- Update ONLY the ## Expertise sections of the plan and build prompts
- Do NOT modify Workflow sections — they remain stable

## Workflow
1. Establish expertise: read the <domain> docs in ai_docs/
2. Analyze recent changes: `git diff`, `git diff --cached`, `git log --oneline -10`, focused on <domain paths>
3. Determine relevance: new patterns? better error handling? files added/removed?
   IMPORTANT: If no relevant learnings found → STOP and report "No expertise updates needed"
4. Extract and apply learnings:
   - Planning knowledge → <domain>_plan.md ## Expertise
   - Building knowledge → <domain>_build.md ## Expertise
5. Report

## Report
1. Changes analyzed  2. Learnings extracted  3. Expert updates made (or "No expertise updates needed")
```

**Run order:** plan → build → improve, each in a fresh agent. Chained, they form an ADW (pillar 6). Pillar 5 covers the YAML expertise-file evolution from lessons 13–14.
