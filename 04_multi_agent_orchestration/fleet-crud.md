# Fleet CRUD — Management Tools and Agent Lifecycle

> **BLUF:** Put the fleet behind a small typed tool surface: create, list, check, command, interrupt, delete, and report cost. Build the tools as closures over your DB and client registry, register them as an in-process MCP server, and give the orchestrator **only** those tools plus light read access.

Code: [`agent_manager.py`](../12.%20multi-agent-orchestration/apps/orchestrator_3_stream/backend/modules/agent_manager.py) and [`orchestrator_service.py`](../12.%20multi-agent-orchestration/apps/orchestrator_3_stream/backend/modules/orchestrator_service.py).

## Registering the tools

```python
mcp_server = create_sdk_mcp_server(name="mgmt", version="1.0.0", tools=self.management_tools)
options = ClaudeAgentOptions(
    system_prompt=orchestrator_prompt,            # with {{SUBAGENT_MAP}} filled from .claude/agents/*.md
    model="sonnet",
    mcp_servers={"mgmt": mcp_server},
    allowed_tools=["mcp__mgmt__create_agent", "mcp__mgmt__list_agents",
                   "mcp__mgmt__command_agent", "mcp__mgmt__check_agent_status",
                   "mcp__mgmt__delete_agent", "mcp__mgmt__interrupt_agent",
                   "mcp__mgmt__read_system_logs", "mcp__mgmt__report_cost",
                   "Bash", "Read", "SlashCommand", "Skill"],
    setting_sources=["project"],                  # loads CLAUDE.md + .claude/commands
    resume=orchestrator_session_id,
)
```

## Fire-and-forget command

```python
@tool("command_agent", "Send a command to an agent. REQUIRED: agent_name, command.",
      {"agent_name": str, "command": str})
async def command_agent_tool(args):
    agent = await get_agent_by_name(orchestrator_id, args["agent_name"])
    asyncio.create_task(self.command_agent(agent.id, args["command"]))
    return {"content": [{"type": "text", "text": f"✅ Command dispatched to '{agent.name}'"}]}
```

## Worker execution

```python
options = ClaudeAgentOptions(
    system_prompt=agent.system_prompt, model=agent.model, cwd=agent.working_dir,
    resume=agent.session_id, hooks=hooks_for(agent), max_turns=MAX_AGENT_TURNS,
    allowed_tools=agent.allowed_tools,            # lesson code hardcodes a default list here; store per agent
    disallowed_tools=["NotebookEdit", "ExitPlanMode"],
    permission_mode="acceptEdits", setting_sources=["project"],
)
await update_agent_status(agent.id, "executing")
try:
    async with ClaudeSDKClient(options=options) as client:
        active_clients[agent.name] = client       # enables interrupt_agent
        await client.query(command)
        session_id = await process_messages(client, agent)
    await update_agent_session(agent.id, session_id)
    await update_agent_status(agent.id, "idle")
except Exception:
    await update_agent_status(agent.id, "blocked")
    raise
finally:
    active_clients.pop(agent.name, None)
```

## Lifecycle

```
create_agent ──▶ idle ──command_agent──▶ executing ──done──▶ idle
                  ▲                          │
                  └──────── interrupt ───────┤
                                             └─error──▶ blocked
delete_agent (any state) ──▶ row deleted, logs cascade
```

The DB `CHECK` also allows `waiting` and `complete`. The lesson code never sets them.

## Templates (`.claude/agents/*.md`)

| Template | Tools | Model | Role |
|---|---|---|---|
| `scout-report-suggest` | Read, Glob, Grep | sonnet | Read-only investigation → report with suggestions |
| `scout-report-suggest-fast` | Read, Glob, Grep | haiku | Cheap, wide scouting |
| `build-agent` | Write, Read, Edit, Grep, Glob, Bash, TodoWrite | sonnet | Implement one file or task |
| `review-agent` | Write, Read, Bash, Grep, Glob | sonnet | Review against the plan; write the review report |
| `docs-scraper` | fetch tools | haiku | Pull docs into `ai_docs/` |
| `playwright-validator` | Playwright MCP | sonnet | UI validation |
| `meta-agent` | Write | opus | Generates new templates |

A template = YAML frontmatter (`name, description, tools, model, color`) + a body used as the system prompt. The registry injects the template list into the orchestrator's prompt, so the orchestrator knows what it can create.

## Minimal orchestrator system prompt skeleton

```md
# Purpose
You orchestrate a fleet of command agents. You plan, create, command, monitor, and clean up agents. You do not do the heavy lifting yourself.

## Variables
COMMAND_LEVEL_COMPACT_PERCENTAGE: 80%
POLL_INTERVAL_SECONDS: 15

## Available Agent Templates
{{SUBAGENT_MAP}}

## Instructions
- Prefer creating a specialized agent from a template over doing work directly.
- Give every command complete, self-contained context (agents don't share memory).
- A task is complete when check_agent_status shows a `response` event followed by a `Stop` hook.
- Poll with `sleep POLL_INTERVAL_SECONDS` between checks; don't poll in a tight loop.
- Delete ephemeral agents when finished unless the user wants to inspect them.
- If an agent's context passes COMMAND_LEVEL_COMPACT_PERCENTAGE, send it `/compact`.

## Report
Concise status: agents used, outcome, cost (from report_cost).
```

← [Pillar 4 overview](README.md)
