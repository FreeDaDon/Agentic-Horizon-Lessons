# Lesson 14 — Orchestrator Agent with ADWs, "Singularity" (code-derived summary)

> **No transcript available.** Derived from [`14.orchestrator-agent-with-adws-singularity/`](../14.orchestrator-agent-with-adws-singularity/README.md): `adws/`, `.claude/`, `app_review/`, `app_fix_reports/`, orchestrator changes. Pillar: [06](../06_building_agentic_layers/README.md).

## BLUF
ADWs are *"the highest leverage point of agentic coding: deterministic orchestration meets non-deterministic intelligence."* *"Raw agents are unreliable. Raw code is inflexible. Combined, they're unstoppable."* Lesson 14 wires ADWs (plan → build → review → fix-on-FAIL) under the orchestrator with `start_adw` and `check_adw`. The orchestrator hands off whole cycles and then *"observe[s], not control[s]."* An ADW expert keeps the workflow system's own mental model current.

**On "singularity":** the word appears only in the folder name. This repo reads it as the stage where the agentic layer plans, builds, reviews and fixes product code **and** maintains its own subsystems through experts, while the human operates the agentic layer. That reading is an interpretation, not a quote.

## What lesson 14 adds over lesson 13
- `adws/`: typed SDK wrapper, DB, logging, WebSocket, summarizer modules; 3 workflows; triggers.
- Migration `9_ai_developer_workflows.sql`; `adw_id`/`adw_step` on agents and logs.
- `start_adw` / `check_adw` tools; `{{AVAILABLE_ADW_TYPES}}` discovered by glob; the "Use ADW vs Direct Agents" policy in the orchestrator prompt.
- `/review` (opus, no Edit) → `app_review/`; `/fix` (opus) → `app_fix_reports/`.
- `experts/adw/` (expertise, self-improve, plan_build_improve); `AdwSwimlanes.vue` UI; `scripts/copy_claude.py`.

## Caveats found in the code (all fixed in this repo)
The original lesson code parsed verdicts by substring, picked plan and review paths by newest modification time, never mapped `bypass_permissions` to the SDK, had no turn or budget caps, ran one fix pass with no re-review, sent the runner's output to `/dev/null`, and left `adw_agents.py` empty. A fix report even exists for a review whose verdict was PASS. Each of these is now fixed and tested; the [pillar 6 checklist](../06_building_agentic_layers/README.md#hardening-checklist-gaps-found-in-the-lesson-code-and-their-status) maps each gap to its fix.
