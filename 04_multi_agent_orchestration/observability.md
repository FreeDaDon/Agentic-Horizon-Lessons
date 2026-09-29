# Observability — Seeing a Fleet in Real Time

> **BLUF:** Capture every hook event and response block as a DB row, broadcast it over WebSocket, and summarize it asynchronously with haiku. Humans get a live UI; the orchestrator gets compact summaries. Track tokens and cost on every `ResultMessage`. Git-diff the files each agent touched.

## Event capture pipeline

```python
async def hook(input_data, tool_use_id, context):             # one factory per event type
    idx = counter["n"]; counter["n"] += 1
    log_id = await insert_hook_event(agent_id=agent_id, task_slug=task_slug, entry_index=idx,
                                     event_type="PreToolUse", payload=input_data,
                                     content=f"Using tool: {input_data.get('tool_name')}")
    await ws.broadcast_agent_log({"agent_id": agent_id, "event_category": "hook",
                                  "event_type": "PreToolUse", "entry_index": idx})
    asyncio.create_task(summarize_and_update(log_id, "PreToolUse", input_data))  # haiku, non-blocking
    return {}                                                   # observe only, never block
```

| Captured | Worker agents | Orchestrator |
|---|---|---|
| Hooks | `PreToolUse`, `PostToolUse` (+ file tracking), `UserPromptSubmit`, `Stop`, `SubagentStop`, `PreCompact` | `PreToolUse`, `PostToolUse`, `Stop` |
| Response blocks | `TextBlock`, `ThinkingBlock`, `ToolUseBlock` → `event_category="response"` | chat stream + thinking |

## Data model (`apps/orchestrator_db/migrations/`)

| Table | Key fields |
|---|---|
| `orchestrator_agents` | `session_id`, status, tokens, `total_cost`, metadata (tools, model, cwd, slash commands) |
| `agents` | name, model, system_prompt, working_dir, `session_id`, tokens, cost, `adw_id`/`adw_step` (lesson 14) |
| `prompts` | `author` (`engineer` / `orchestrator_agent`), text, summary |
| `agent_logs` | `event_category` (`hook` / `response` / `adw_step`), `event_type`, `entry_index`, `task_slug`, `payload` JSONB, `summary` |
| `system_logs` | app logs |
| `orchestrator_chat` | user ↔ orchestrator conversation |
| `ai_developer_workflows` | ADW state (lesson 14; see [pillar 6](../06_building_agentic_layers/adw-layers.md)) |

Pydantic `models.py` is the source of truth; `sync_models.py` copies it into each app. Rule from `CLAUDE.md`: **keep models in sync with migrations.**

## WebSocket event types

`agent_created` · `agent_updated` · `agent_deleted` · `agent_status_changed` · `agent_log` · `agent_summary_update` · `orchestrator_updated` · `orchestrator_chat` · `thinking_block` · `system_log` · `chat_stream` · `chat_typing` · `error` · `heartbeat` · plus `adw_*` events in lesson 14.

## Cost and context tracking

- Per result: `total_cost_usd` (falling back to `usage["total_cost_usd"]`), `usage.input_tokens`, `usage.output_tokens`, written incrementally (`total_cost = total_cost + $n`).
- `report_cost()` returns cost, tokens, session and a context % with a warning at 80%.
- Improvement over the lesson: don't zero cost on `PreCompact`; keep spend cumulative and reset only token counters.

## File-change tracking

A `PostToolUse` hook records paths each agent read or modified. On `ResultMessage`, a tracker produces a per-file git diff, added and removed counts, status, and an AI summary, and broadcasts it as a `FileTrackingBlock`. That answers "what did this agent actually change?" without reading its transcript.

## Claude Code session observability (outside the app)

Every hook in `.claude/settings.json` also runs `send_event.py --source-app <name> --event-type <X> --summarize`, which POSTs to a local observability server (`http://localhost:4000/events`). The same pattern works for plain interactive Claude Code sessions.

## Minimum viable observability for your own fleet

| Must have | Why |
|---|---|
| One row per tool call with agent ID and task slug | Traceability and replay |
| Async summaries (haiku) | The orchestrator's and human's context stays small |
| Status transitions as events | UI and alerting |
| Cost per result, cumulative per agent and workflow | Budget enforcement |
| File diff per agent run | Review without reading transcripts |
| Heartbeat | Detect stalled agents |

← [Pillar 4 overview](README.md)
