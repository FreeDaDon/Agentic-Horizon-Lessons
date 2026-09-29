# Playbooks — Applying the Six Pillars to a Domain

> **BLUF:** Every playbook uses the same build order: **prime → prompts → SDK agent → fleet → expert → ADW**. Stop at the layer your blast radius justifies. Anything that can move money, touch production, or delete data gets a deterministic gate that no agent can bypass.

| Playbook | Highest-risk action | Hard gate |
|---|---|---|
| [Software](software.md) | Merge or deploy broken code | Tests + review verdict + human merge |
| [Quant trading](trading.md) | Placing live orders | Agents never hold order-placing tools; a separate execution gate needs human confirmation |
| [Cybersecurity](cybersecurity.md) | Containment actions (isolate host, disable account) | Agents recommend; a human or SOAR policy executes |
| [Systems automation](systems_automation.md) | `apply`/`destroy` on production | Plan with no destroys, or explicit human approval, before apply |

## Shared build order

| Layer | Deliverable | Pillar |
|---|---|---|
| 1. Context | `CLAUDE.md` ≤ 50 lines, `/prime_<area>`, cost-named MCP configs | [01](../01_elite_context_engineering/README.md) |
| 2. Prompts | L2–L4 workflow prompts with fixed output locations | [02](../02_agentic_prompt_engineering/README.md) |
| 3. SDK agent | One domain agent: custom tools, built-ins denied, guardrail hooks | [03](../03_claude_agent_sdk_mastery/README.md) |
| 4. Fleet | Orchestrator + templates for scout, worker and reviewer roles | [04](../04_multi_agent_orchestration/README.md) |
| 5. Expert | `experts/<domain>/expertise.yaml` + self-improve | [05](../05_agent_experts/README.md) |
| 6. ADW | Deterministic pipeline with a verdict gate | [06](../06_building_agentic_layers/README.md) |
