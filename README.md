# Agentic Horizon — Lessons, Frameworks & Playbooks

> **BLUF:** Six Agentic Horizon lessons (9–14) turned into a reusable system for agentic engineering. It has six pillar guides, copy-paste prompt templates, domain playbooks (software, trading, cybersecurity, systems automation) and one-page cheat sheets. The original lesson code sits unchanged next to them (apart from model aliases), and every guide links into it. Model references are family aliases (`opus`, `sonnet`, `haiku`), so nothing needs editing when new models ship.

## The stack in one picture

```
 06 Agentic layers   ADWs: deterministic code orchestrating agents → the layer maintains itself
 05 Agent experts    ACT → LEARN → REUSE with agent-owned expertise files
 04 Orchestration    one conductor, a fleet of workers, 8 CRUD tools, summarized events
 03 Agent SDK        custom agents: your system prompt, your tools, sessions, hook guardrails
 02 Prompts          7 levels of reusable, composable prompts for you, your team, your agents
 01 Context          R&D: Reduce and Delegate; a focused agent is a performant agent
```

Each layer depends on the ones below it. Start at the bottom.

## Pillars

| # | Pillar | Bottom line | Lesson code | Source |
|---|---|---|---|---|
| 01 | [Elite Context Engineering](01_elite_context_engineering/README.md) | 12 techniques, 4 levels, 2 levers (Reduce, Delegate) | [`9. elite-context-engineering/`](9.%20elite-context-engineering/README.md) | transcript |
| 02 | [Agentic Prompt Engineering](02_agentic_prompt_engineering/README.md) | 7 prompt levels; Workflow is the S-tier section; meta prompts give the biggest speed-up | [`10. agentic-prompt-engineering/`](10.%20agentic-prompt-engineering/README.md) | transcript |
| 03 | [Claude Agent SDK Mastery](03_claude_agent_sdk_mastery/README.md) | 8 agents from pong to multi-agent apps; 12 SDK patterns | [`11. building-specialized-agents/`](11.%20building-specialized-agents/README.md) | code |
| 04 | [Multi-Agent Orchestration](04_multi_agent_orchestration/README.md) | Orchestrator + fleet CRUD + real-time observability | [`12. multi-agent-orchestration/`](12.%20multi-agent-orchestration/README.md) | code |
| 05 | [Agent Experts](05_agent_experts/README.md) | Expertise YAML validated against the code; self-improve loop | [`13. agent-experts/`](13.%20agent-experts/README.md) | code |
| 06 | [Building Agentic Layers](06_building_agentic_layers/README.md) | 9-stage roadmap to a self-maintaining layer; ADW anatomy + hardening | [`14.orchestrator-agent-with-adws-singularity/`](14.orchestrator-agent-with-adws-singularity/README.md) | code |

**Source** says where each pillar's content comes from: *transcript* means the lesson video transcript is in this repo; *code* means no transcript exists and the pillar is derived from the lesson's code and README (labeled in each doc).

## Also in this repo

| Folder | Contents |
|---|---|
| [`transcripts_summary/`](transcripts_summary/) | Timestamped summaries of lessons 9 and 10; code-derived summaries of 11–14 with the gaps found in each |
| [`playbooks/`](playbooks/README.md) | [Software](playbooks/software.md) · [Quant trading](playbooks/trading.md) · [Cybersecurity](playbooks/cybersecurity.md) · [Systems automation](playbooks/systems_automation.md) |
| [`cheat_sheets/`](cheat_sheets/) | [BLUF reference](cheat_sheets/bluf_reference.md) · [Claude Code commands](cheat_sheets/claude_code_commands.md) · [Model aliases](cheat_sheets/model_aliases.md) |
| [`02_agentic_prompt_engineering/templates/`](02_agentic_prompt_engineering/templates/) | Copy-paste templates for prompt levels 1–7 |
| [`05_agent_experts/expertise-file-template.yaml`](05_agent_experts/expertise-file-template.yaml) | Starter expertise file |
| [`06_building_agentic_layers/adw-layers.md`](06_building_agentic_layers/adw-layers.md) | Hardened ADW skeleton |

## Quick start: the first hour

1. **Measure.** Start a fresh Claude Code session in your project and run `/context`. Note boot tokens ([pillar 1, #1](01_elite_context_engineering/README.md#1-measure-to-manage)).
2. **Reduce.** Remove the default `.mcp.json`; cut `CLAUDE.md` to universals; copy [`prime.md`](9.%20elite-context-engineering/.claude/commands/prime.md) into `.claude/commands/`.
3. **Plan and build in separate agents.** Copy [`quick-plan.md`](10.%20agentic-prompt-engineering/.claude/commands/quick-plan.md) and [`build.md`](10.%20agentic-prompt-engineering/.claude/commands/build.md). Run `/quick-plan "<task>"`, then `/build specs/<plan>.md` in a **new** session.
4. **Template your next prompt.** Use the [level-2 template](02_agentic_prompt_engineering/templates/level-2-workflow.md) for whatever you did three times this week.
5. **Pick a playbook** for your domain and follow its layer table until you reach the layer your blast radius justifies.

## Running the lesson apps

Each lesson folder is self-contained, with its own `README.md`, `.env.sample` and `.claude/`. Copy `.env.sample` to `.env`, add `ANTHROPIC_API_KEY`, and follow that lesson's README. Lessons 12–14 need PostgreSQL for the orchestrator (`apps/orchestrator_db/`). Open Claude Code **inside a lesson folder** so its `.claude/commands`, hooks and skills load.

## Conventions

- **Models:** aliases only. Raw-API scripts resolve the newest ID at runtime; pin with `ANTHROPIC_MODEL_<FAMILY>` ([details](cheat_sheets/model_aliases.md)).
- **Transcripts** (`9. …mp4.txt`, `10. …mp4.txt`) are verbatim source material and are never edited.
- **Blast radius decides the gate.** Low-risk work ships on an agent verdict. Anything touching money, production or data gets a deterministic check plus a human.
