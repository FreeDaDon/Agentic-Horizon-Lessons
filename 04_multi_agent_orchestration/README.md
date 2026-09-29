# 04 · Multi-Agent Orchestration — Commanding an Agent Fleet

> **BLUF:** One **orchestrator agent** ("the conductor") manages a fleet of **command agents** ("the performers") through **8 management tools** exposed as an in-process MCP server. The orchestrator plans and dispatches; the workers do the heavy lifting in the background. Everything goes to Postgres and streams over WebSocket, so a human (or the orchestrator) watches **summarized events**, not raw transcripts. The orchestrator's context stays small because it only ever reads summaries.

**Source:** code in [`12. multi-agent-orchestration/`](../12.%20multi-agent-orchestration/README.md), app `apps/orchestrator_3_stream/` + `apps/orchestrator_db/`. There is no transcript; this pillar is derived from the code ([summary](../transcripts_summary/12_multi_agent_orchestration_code_derived.md)). Lessons 13 and 14 extend the same app with experts and ADWs.

---

## Architecture

```
 Engineer ──chat/Cmd+K──▶ Orchestrator agent (Agent SDK, own session, system prompt with {{SUBAGENT_MAP}})
                               │  mcp__mgmt__* tools
          ┌────────────────────┼─────────────────────────┐
          ▼                    ▼                         ▼
   Command agent A      Command agent B  …        (templates: build-agent, review-agent,
   (ClaudeSDKClient,    (resume=session_id)        scout-report-suggest[-fast], docs-scraper,
    hooks → DB + WS)                               playwright-validator, meta-agent)
          │                    │
          └──── hooks + response blocks ──▶ Postgres (agent_logs, prompts, …) ──▶ WebSocket ──▶ Vue UI
                                  └──▶ haiku summarizer (async) ──▶ agent_logs.summary
```

**Hub-and-spoke only:** there is no worker-to-worker channel. The orchestrator hands findings from one worker to the next through `command_agent` (the scout's report goes into the builder's command; the plan path goes to the builder and then the reviewer).

## The 8 management tools (fleet CRUD)

| CRUD | Tool | What it does |
|---|---|---|
| **C** | `create_agent(name, system_prompt?, model?, subagent_template?)` | Inserts an `agents` row (unique name per orchestrator), applies the template's prompt, tools and model, runs a warm-up query to get a `session_id`, broadcasts `agent_created` |
| **R** | `list_agents()` | Name, status, model, tokens, cost |
| **R** | `check_agent_status(agent_name, tail_count=10, offset=0, verbose_logs=false)` | Tail of **summarized** events for the latest task |
| **R** | `read_system_logs(offset, limit, message_contains, level)` | App logs |
| **R** | `report_cost()` | Orchestrator cost, tokens, context %, with a warning at 80% or more |
| **U** | `command_agent(agent_name, command)` | **Fire-and-forget**: `asyncio.create_task(...)`, returns immediately; the worker resumes its session |
| **U** | `interrupt_agent(agent_name)` | `client.interrupt()` on the registered active client |
| **D** | `delete_agent(agent_name)` | Deletes the row (logs cascade), drops file tracking, broadcasts `agent_deleted` |

Details, lifecycle and code: [fleet-crud.md](fleet-crud.md).

## Orchestration patterns (slash commands)

| Command | Pattern | Flow |
|---|---|---|
| `/orch_one_shot_agent <task>` | Ephemeral worker | create → command ("ultrathink") → poll every 10s → delete → report |
| `/orch_scout_and_build <problem>` | Scout → builder | `scout-<kw>` (fast template) → findings into `build-<kw>`; agents kept for inspection |
| `/orch_plan_w_scouts_build_review <task>` | Three-phase pipeline | planner → build-agent → review-agent, sequential |
| `/plan_w_scouters <prompt>` | Scout swarm → plan | 3 base + 5 fast scouts in parallel ("divide and conquer"), then the planner **manually validates** the file list → `specs/<name>.md` |
| `/build_in_parallel <plan>` | Parallel builders | **one file per agent**; files grouped into dependency batches; each batch is one message with multiple `Task(build-agent)` calls; report is `git diff --stat` |

**Completion detection:** workers don't return values. The orchestrator polls `check_agent_status` until it sees a `response` event followed by a `Stop` hook event, using `Bash(sleep N)` between checks.

## Design rules

1. **The orchestrator dispatches; workers execute.** Keep the orchestrator's tool list to management tools plus light read tools.
2. **Summaries, not transcripts, go back to the orchestrator.** A haiku summarizer turns every event into about 50–100 characters. That is the reduce/delegate split from [pillar 1](../01_elite_context_engineering/README.md), applied to a fleet.
3. **Templates are reusable system prompts.** `.claude/agents/*.md` frontmatter (`name, description, tools, model`) plus the body as prompt.
4. **Every worker is resumable.** Store `session_id`; each `command_agent` resumes.
5. **Status is explicit.** `idle → executing → idle`, or `blocked` on error.
6. **Compact workers deliberately.** `command_agent(name, "/compact")` at 80% context (a fleet-level exception to pillar 1's "prefer reset" rule, because workers keep long-running roles).

## Known gaps in the lesson code (fix before relying on it)

| Gap | Fix |
|---|---|
| Template **tool limits apply only at creation**. `command_agent` hardcodes the full default toolset, so a "read-only" scout gets Write/Edit/Bash once commanded | Store the template's `allowed_tools` on the agent row and apply it on every command |
| `/orch_plan_w_scouts_build_review` asks for a per-agent tool list `create_agent` can't accept | Add a `tools` parameter to `create_agent` |
| Statuses `waiting`/`complete` and agent-side chat rows exist in the schema but are never written | Remove them or implement them |
| `PreCompact` resets tokens **and cost**, so spend history is lost | Reset tokens only; keep cost cumulative |
| Context % is estimated from cumulative tokens / 200K | Read real usage per turn; treat the estimate as a warning only |

## Domain adaptation

| Domain | Orchestrator job | Worker templates | Parallelism |
|---|---|---|---|
| Quant trading | research sprint over a watchlist | `data-scout` (haiku, read-only), `backtester` (sonnet), `risk-reviewer` (opus) | one backtester per symbol or parameter shard |
| Cybersecurity | incident response coordination | `log-scout` per source, `ioc-enricher`, `report-writer` | one scout per log source; the reviewer gates containment recommendations |
| Systems automation | multi-environment change | `drift-scout` per env, `iac-builder`, `plan-reviewer` | per-env scouts; the builder is serialized; a human approves before apply |
| Software | feature delivery | scouts, `build-agent`, `review-agent`, `playwright-validator` | `/build_in_parallel` by file |

**Next:** [fleet-crud.md](fleet-crud.md) · [observability.md](observability.md) · [pillar 5: experts](../05_agent_experts/README.md)
