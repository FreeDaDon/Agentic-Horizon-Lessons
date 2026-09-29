# 03 · Claude Agent SDK Mastery — Building Custom Domain Agents

> **BLUF:** *"Better agents, more agents, then… custom agents."* The Agent SDK turns Claude Code's loop into a library. You pick the **system prompt** (replace or append), the **tools** (custom in-process tools, with built-ins denied), the **state** (`resume` a session), and the **guardrails** (inline hooks that also cover sub-agents). Lesson 11 builds this up over 8 agents, from a one-line "pong" bot to two cooperating streaming agents behind a web UI.

**Source:** code in [`11. building-specialized-agents/`](../11.%20building-specialized-agents/README.md). There is no transcript; this pillar is derived from the code ([summary](../transcripts_summary/11_building_specialized_agents_code_derived.md)). Package: `claude-agent-sdk` (Python). The TypeScript pong agent uses the older `@anthropic-ai/claude-code` package; its successor is `@anthropic-ai/claude-agent-sdk`.

---

## The core-four control surface

| Lever | `ClaudeAgentOptions` field | Choice |
|---|---|---|
| **Prompt** | `system_prompt` | `str` = **full replacement** (a new identity) · `{"type":"preset","preset":"claude_code","append":"…"}` = keep Claude Code, add a role |
| **Model** | `model` | `"opus"` / `"sonnet"` / `"haiku"` alias. Match the model to the job, e.g. haiku for summarizers and pong-class agents |
| **Tools** | `mcp_servers`, `allowed_tools`, `disallowed_tools` | Custom tools via `@tool` + `create_sdk_mcp_server`. **Deny built-ins you don't want**, and allow exactly `mcp__<server_key>__<tool>` |
| **Context** | `resume`, `cwd`, `setting_sources`, `max_turns` | Session continuity, working directory, whether project `.claude/` loads, and a turn cap |
| Guardrails | `hooks`, `permission_mode` | Inline `PreToolUse`/`PostToolUse` Python hooks; `acceptEdits` vs `bypassPermissions` |

## The 8-agent progression (lesson 11)

| # | Agent | New capability | SDK surface introduced |
|---|---|---|---|
| 1 | [`pong_agent`](../11.%20building-specialized-agents/apps/custom_1_pong_agent/pong_agent.py) | Full system-prompt override; cost and session stats | `query()`, `ClaudeAgentOptions(system_prompt=str, model)`, `ResultMessage.total_cost_usd / session_id` |
| 2 | [`echo_agent`](../11.%20building-specialized-agents/apps/custom_2_echo_agent/echo_agent.py) | First custom tool, tool allowlist, multi-turn client | `@tool`, `create_sdk_mcp_server`, `ClaudeSDKClient`, `ToolUseBlock` |
| 3 | [`calc_agent`](../11.%20building-specialized-agents/apps/custom_3_calc_agent/calc_agent.py) | Multi-tool REPL, session memory, built-in denylist, `is_error` results, running cost | `resume`, `disallowed_tools`, async-generator input |
| 4 | [`social_hype_agent`](../11.%20building-specialized-agents/apps/custom_4_social_hype_agent/modules/agent.py) | Live event source → queue → agent; **tool as structured output** | `max_turns=3`, reading `ToolUseBlock.input` |
| 5 | [`qa_agent`](../11.%20building-specialized-agents/apps/custom_5_qa_agent/qa_agent.py) | Read-only codebase Q&A; parallel `Task` sub-agents; inline security hooks (they apply to sub-agents too); external MCP config | `hooks={"PreToolUse":[HookMatcher(...)]}`, `connect()/disconnect()` |
| 6 | `tri_copy_writer` | FastAPI + Vue UI; strict JSON output; file-context injection | all tools denied; JSON output contract |
| 7 | `micro_sdlc_agent` | Planner, builder and reviewer agents; stage state machine; WebSocket streaming; per-stage sessions; write-scope hooks | `preset + append`, `cwd`, `permission_mode` |
| 8 | `ultra_stream_agent` | Two cooperating agents (stream producer + inspector); runs indefinitely; sessions persisted in SQLite | two MCP servers, long-lived client, `resume` |

Pattern catalog with code: [patterns.md](patterns.md).

---

## Design rules distilled

1. **Replace the system prompt only for narrow agents.** A string prompt discards Claude Code's engineering prompt. That is right for pong, calc and copywriter; wrong for anything that edits code. Use `preset + append` for engineering roles (planner, reviewer).
2. **Deny by default.** Give an agent a custom toolset and **explicitly** list built-ins in `disallowed_tools`. Lesson 11 denies `Read, Write, Edit, MultiEdit, NotebookEdit, Glob, Grep, WebFetch, WebSearch, TodoWrite, Task, ExitPlanMode, Bash, BashOutput, KillShell` for non-coding agents.
3. **Tools return errors, not exceptions.** Catch inside the tool and return `{"content":[…], "is_error": True}` so the model can recover.
4. **Use a tool call as structured output.** Make the agent call `submit_<thing>(fields…)` and read `ToolUseBlock.input`. That is typed data, not regex over prose.
5. **Put guardrails in hooks.** Inline `PreToolUse` hooks deny with `permissionDecision: "deny"` plus a reason (block `.env` reads; limit writes to `specs/`). They apply to sub-agents too. Prefer them to `can_use_tool` for policy.
6. **Persist the session ID.** Capture `ResultMessage.session_id` and store it (in the DB, per user or per stage). Use `resume=` to continue.
7. **Track cost on every result.** Sum `ResultMessage.total_cost_usd` per session and per agent. Cap with `max_turns`.
8. **Manage context in long-running agents.** Rotate sessions after N units of work, but start a **new** session, because resuming the same session keeps the same context (a bug in the lesson's ultra-stream agent).
9. **Keep prompts in files.** `prompts/*_SYSTEM_PROMPT.md` with `{VARIABLE}` substitution; split `system_prompts/` from `user_prompts/`.

## Error handling and state recovery

| Failure | Pattern |
|---|---|
| Tool raises | Return `is_error: True` with a message; the model retries or explains |
| Agent run fails | `ResultMessage.is_error`; set the stage/agent status to `errored` or `blocked`; allow `errored → idle` to retry (micro-SDLC state machine) |
| Process restart | Reload `session_id` from the DB and `resume=`; long-running agents reconnect with a fresh client |
| Output format drift | Strict JSON contract + defensive parse (find the last `{"primary_response":`, strip fences, `json.loads`) or, better, tool-as-output |
| Context overflow | Budget turns (`max_turns`), rotate sessions, summarize to a DB instead of keeping history in context |
| User interrupt | `client.interrupt()` on a registered active client |

## Domain adaptation

| Domain | Agent | Custom tools | Guardrail hooks |
|---|---|---|---|
| Quant trading | `signal_analyst` (haiku, string system prompt) | `get_bars(symbol, tf, n)`, `compute_indicators`, `submit_signal(symbol, side, confidence, rationale)` | deny every order-placing tool; an execution gate lives outside the agent |
| Cybersecurity | `alert_triager` | `query_siem(q, window)`, `lookup_ioc(value)`, `submit_verdict(alert_id, severity, mitre, evidence)` | allow read-only query tools only; redact secrets in `PostToolUse` |
| Systems automation | `drift_inspector` (preset + append) | `run_plan(env)` (read-only), `submit_drift_report` | block `apply`/`destroy` in Bash with a `PreToolUse` regex |
| Software | `qa_agent`, `micro_sdlc` | as in lesson 11 | `.env` read block; write-scope per role |

**Next:** [patterns.md](patterns.md) · [pillar 4: orchestration](../04_multi_agent_orchestration/README.md)
