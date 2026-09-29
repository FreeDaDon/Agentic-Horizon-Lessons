# BLUF Reference — One Page per Pillar

| Pillar | Bottom line | First move |
|---|---|---|
| [01 Context](../01_elite_context_engineering/README.md) | Only two levers: **Reduce** and **Delegate**. A focused agent is a performant agent. | Fresh agent → `/context`. Kill the default MCP config; shrink `CLAUDE.md`; write `/prime` |
| [02 Prompts](../02_agentic_prompt_engineering/README.md) | The prompt is the unit of engineering. Consistent, composable sections for you, your team and your agents. | Turn your most repeated request into an L2 workflow prompt with Variables + Workflow + Report |
| [03 SDK](../03_claude_agent_sdk_mastery/README.md) | Custom agents = your system prompt + your tools + session state + hook guardrails. | Build a haiku agent with one `@tool`, built-ins denied |
| [04 Orchestration](../04_multi_agent_orchestration/README.md) | One conductor, many performers, eight CRUD tools, and summaries (not transcripts) flowing back. | `/orch_scout_and_build` on a real task |
| [05 Experts](../05_agent_experts/README.md) | ACT → LEARN → REUSE. Expertise YAML is agent-owned and validated against the code. | Seed `experts/<riskiest-module>/expertise.yaml`, loop self-improve until stable |
| [06 Agentic layers](../06_building_agentic_layers/README.md) | Deterministic code orchestrates non-deterministic agents. ADWs are the top of the stack. | `adw_plan_build.py` with marker-based hand-offs |

## The 12 context techniques

**Beginner:** measure · no default MCP · prime > CLAUDE.md
**Intermediate:** output styles · sub-agents properly · planner/builder
**Advanced:** reset + prime > compact · context bundles · one agent one purpose
**Agentic:** append system prompt · primary (background) delegation · agent experts

## The 7 prompt levels

1 High-level → 2 **Workflow** → 3 Control flow → 4 **Delegate** → 5 Higher-order → 6 **Template meta** → 7 Self-improving

## Section tier list (usefulness / skill)

Workflow **S/C** · Variables A/B · Examples A/low · Purpose B/D · Report, Instructions mid · Metadata C/C · Codebase Structure C/low · Relevant Files C/C · Title C/D

## Rules that keep paying off

- Measure before you optimize: `/context` at boot and at 80%.
- One agent, one prompt, one purpose.
- Fixed output locations for every reusable prompt (`specs/`, `app_review/`, `app_fix_reports/`).
- Machine-readable final lines for anything a script parses (`VERDICT: PASS`).
- Deny by default in SDK agents; guardrails in hooks.
- Expertise is memory, code is truth. Validate before you trust it.
- Model aliases (`opus`/`sonnet`/`haiku`), never pinned versions ([model_aliases.md](model_aliases.md)).
- High blast radius → a deterministic gate plus a human. Low blast radius → ship.
