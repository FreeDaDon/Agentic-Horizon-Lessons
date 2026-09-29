# Lesson 13 — Agent Experts (code-derived summary)

> **No transcript available.** Derived from [`13. agent-experts/`](../13.%20agent-experts/README.md): README, `.claude/commands/experts/`, `apps/nile`, the orchestrator's autocomplete expert. Pillar: [05](../05_agent_experts/README.md).

## BLUF
*"Your agents forget. And that means your agents don't learn."* An **agent expert** runs **ACT → LEARN → REUSE** with an **expertise file**, a YAML "mental model" of one domain. The code stays the source of truth; the expert validates its expertise against the code before trusting it. *"You don't manually update expertise files. You teach your agents how to learn by writing self-improve prompts."*

## What lesson 13 adds over lesson 12
- `.claude/commands/experts/{database,websocket}/`: `expertise.yaml` (412 and 676 lines), `question.md`, `plan.md`, `self-improve.md`, `plan_build_improve.md`.
- **Nile** product-expert demo: per-user expertise row (views, cart, checkout), learned deterministically and reused in the system prompt of a haiku SDK agent with two custom tools.
- **Autocomplete expert** in the orchestrator: YAML history of accepted and typed completions.
- Nested slash-command discovery (`glob("**/*.md")` → `experts:websocket:question`).
- `meta-agent` (strict 4-section format), `meta-skill`, `meta_prompt.md`.

## Self-improve in one line
Optional `git diff` → read expertise → compare with the code → list discrepancies → update → enforce 1000-line cap → YAML parse check → report (or "nothing to update" and stop).

## Caveats found in the code
- README endpoint/table names differ from the code (`/track` vs `/action`; JSONB vs SQLite JSON).
- Nile SDK sessions are held in memory only; the autocomplete history has no cap.
- `HUMAN_IN_THE_LOOP` is declared in `plan_build_improve.md` but never used.
