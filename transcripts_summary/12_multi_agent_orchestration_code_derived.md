# Lesson 12 — Multi-Agent Orchestration (code-derived summary)

> **No transcript available.** Derived from [`12. multi-agent-orchestration/`](../12.%20multi-agent-orchestration/README.md): `apps/orchestrator_3_stream`, `apps/orchestrator_db`, `.claude/`, `specs/`. Pillar: [04](../04_multi_agent_orchestration/README.md).

## BLUF
One orchestrator agent, *"the conductor of this multi-agent orchestra"*, manages command agents through **8 management tools** (create, list, command, check status, delete, interrupt, read logs, report cost) exposed as an in-process MCP server. Workers run fire-and-forget with resumable sessions. Every hook and response block is written to Postgres, streamed over WebSocket, and summarized by haiku, *"comprehensive observability — every event, cost, and interaction tracked."*

## Key artifacts

| Area | Files |
|---|---|
| Orchestrator | `backend/modules/orchestrator_service.py`, `prompts/orchestrator_agent_system_prompt.md` |
| Fleet tools | `backend/modules/agent_manager.py` |
| Hooks → DB/WS | `backend/modules/command_agent_hooks.py`, `orchestrator_hooks.py`, `websocket_manager.py` |
| Summaries | `backend/modules/single_agent_prompt.py` (haiku) |
| File diffs | `backend/modules/file_tracker.py` |
| Schema | `apps/orchestrator_db/migrations/0–8`, `models.py`, `sync_models.py` |
| Templates | `apps/orchestrator_3_stream/.claude/agents/*.md` |
| Patterns | `/orch_one_shot_agent`, `/orch_scout_and_build`, `/orch_plan_w_scouts_build_review`, `/plan_w_scouters`, `/build_in_parallel` |

## Engineering rules from `CLAUDE.md`
No mocks (real DB + real SDK) · never fail silently · keep `models.py` in sync with migrations · validate frontend changes with Playwright MCP.

## Caveats found in the code
- Template tool limits apply only at creation; `command_agent` grants the full default toolset.
- `waiting`/`complete` statuses and agent-side chat rows are defined in the schema but never written.
- `PreCompact` zeroes cost as well as tokens.
- The README says backend port 9403; the app `CLAUDE.md` says 8002.
