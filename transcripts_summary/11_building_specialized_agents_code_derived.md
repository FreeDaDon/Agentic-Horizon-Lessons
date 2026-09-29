# Lesson 11 — Building Specialized Agents (code-derived summary)

> **No transcript available.** Derived from [`11. building-specialized-agents/`](../11.%20building-specialized-agents/README.md): README, 8 apps, `.claude/`. Pillar: [03](../03_claude_agent_sdk_mastery/README.md).

## BLUF
*"Better agents, More agents, then… Custom Agents."* After context and prompt engineering, you build **domain-specific agents** with the Claude Agent SDK. You control the system prompt (full override or preset + append), the tools (custom `@tool` servers with built-ins denied), sessions (`resume`) and guardrails (inline hooks). Eight apps take this from a pong bot to multi-agent web products.

## The 8 agents

| # | App | Teaches |
|---|---|---|
| 1 | `custom_1_pong_agent` | System prompt override; cost and session stats from `ResultMessage` |
| 2 | `custom_2_echo_agent` | First `@tool` + `create_sdk_mcp_server`; `allowed_tools` naming `mcp__<key>__<tool>` |
| 3 | `custom_3_calc_agent` | Multi-tool REPL; `resume`; built-in denylist; `is_error` tool results |
| 4 | `custom_4_social_hype_agent` | Firehose → queue → agent; tool call as structured output; `max_turns` |
| 5 | `custom_5_qa_agent` | Parallel `Task` sub-agents; inline `PreToolUse` hooks (block `.env`) that also cover sub-agents |
| 6 | `custom_6_tri_copy_writer` | FastAPI + Vue; strict JSON output contract; file-context injection |
| 7 | `custom_7_micro_sdlc_agent` | Planner/builder/reviewer kanban; state machine; write-scope hooks; per-stage sessions |
| 8 | `custom_8_ultra_stream_agent` | Two cooperating long-running agents; SQLite-persisted sessions; context rotation |

## Reusable assets
Hooks: `dangerous_command_blocker.py`, `universal_hook_logger.py`, `context_bundle_builder.py`. Commands: `/scout_plan_build`, `/background`, `/load_bundle`, `/parallel_subagents`, `/t_metaprompt_workflow`, `cc_hook_expert` set. Output styles: `concise-*`, `verbose-*`, `observable-tools-diffs-tts`.

## Caveats found in the code
- The ultra-stream "context clear" resumes the **same** session, so context isn't actually cleared.
- The TS pong agent uses the legacy `@anthropic-ai/claude-code` package (`customSystemPrompt`).
- "query() doesn't support custom tools" (echo agent comment) is a simplification: SDK MCP tools need the streaming-input mode.
