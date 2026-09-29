# Agent SDK Pattern Catalog

> **BLUF:** Twelve copyable patterns from lesson 11. Each has the code, where it lives, and when to use it. Models are aliases (`opus`/`sonnet`/`haiku`), so the code follows the latest model without edits.

All paths are relative to [`11. building-specialized-agents/apps/`](../11.%20building-specialized-agents/README.md).

---

### 1. Full system-prompt override — `custom_1_pong_agent/pong_agent.py`
*Use for narrow single-purpose agents with no engineering behavior.*
```python
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage, TextBlock

options = ClaudeAgentOptions(system_prompt=load_system_prompt(), model="haiku")
async for message in query(prompt=user_input, options=options):
    if isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, TextBlock):
                print(block.text)
    elif isinstance(message, ResultMessage):
        print(message.session_id, message.duration_ms, message.total_cost_usd)
```

### 2. Preset + append — `custom_7_micro_sdlc_agent/backend/modules/agent_orchestrator.py`
*Keep Claude Code's engineering prompt and add a role.*
```python
options = ClaudeAgentOptions(
    system_prompt={"type": "preset", "preset": "claude_code", "append": planner_instructions},
    model="opus", cwd=working_dir, hooks=hooks, permission_mode="acceptEdits",
    resume=resume_session_id,
)
```

### 3. Custom in-process tool — `custom_2_echo_agent/echo_agent.py`
```python
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool("echo", "Echo a message with transformations", {"message": str, "repeat": int, "transform": str})
async def echo_tool(args):
    return {"content": [{"type": "text", "text": transform(args)}]}

server = create_sdk_mcp_server(name="echo_server", version="1.0.0", tools=[echo_tool])
options = ClaudeAgentOptions(mcp_servers={"echo": server}, allowed_tools=["mcp__echo__echo"])
```
The tool name prefix comes from the **`mcp_servers` dict key** (`echo`), not the server's `name`.

### 4. Deny built-ins — `custom_3_calc_agent/calc_agent.py`
```python
disallowed_tools=["Read", "Write", "Edit", "MultiEdit", "NotebookEdit", "Glob", "Grep",
                  "WebFetch", "WebSearch", "TodoWrite", "Task", "ExitPlanMode",
                  "Bash", "BashOutput", "KillShell"]
```

### 5. Tool-level errors — `calc_agent.py`
```python
except Exception as e:
    return {"content": [{"type": "text", "text": f"Calculation error: {e}"}], "is_error": True}
```

### 6. Session continuity — `calc_agent.py`
```python
options = ClaudeAgentOptions(..., resume=current_session_id)

async def messages():
    yield {"type": "user", "message": {"role": "user", "content": user_input}}

async with ClaudeSDKClient(options=options) as client:
    await client.query(messages())
    async for msg in client.receive_response():
        if isinstance(msg, ResultMessage):
            current_session_id = msg.session_id
            total_cost += msg.total_cost_usd or 0
```

### 7. Tool as structured output — `custom_4_social_hype_agent/modules/agent.py`
```python
options = ClaudeAgentOptions(system_prompt=prompt, model="sonnet",
    mcp_servers={"tools": tools_server},
    allowed_tools=["mcp__tools__submit_analysis", "mcp__tools__notify"],
    disallowed_tools=BUILTINS, max_turns=3)
...
elif isinstance(block, ToolUseBlock) and block.name == "mcp__tools__submit_analysis":
    record = {"summary": block.input["summary"], "sentiment": block.input["sentiment"]}
```
Pair with an `asyncio.Queue(maxsize=N)` worker when the input is a live stream.

### 8. Inline guardrail hook (also covers sub-agents) — `custom_5_qa_agent/qa_agent.py`
```python
from claude_agent_sdk import HookMatcher

async def block_env_files(input_data, tool_use_id, context):
    path = input_data.get("tool_input", {}).get("file_path", "")
    if ".env" in path:
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": "Security policy: .env files are blocked"}}
    return {}

hooks = {"PreToolUse": [HookMatcher(matcher="Read", hooks=[block_env_files]),
                        HookMatcher(hooks=[log_tool_usage])],
         "PostToolUse": [HookMatcher(hooks=[log_tool_usage])]}
```
Returning `{}` allows the call. Unit-test hooks directly (see `custom_5_qa_agent/test_inline_hooks.py`).

### 9. Write-scope per role — `agent_orchestrator.py`
```python
async def planner_write_hook(input_data, tool_use_id, context):
    if input_data.get("tool_name") == "Write":
        path = os.path.normpath(input_data["tool_input"]["file_path"])
        if not path.startswith(PLAN_DIR):
            return {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Planner can only write to {PLAN_DIR}"}}
    return {}
```
The planner writes only to `specs/` and the reviewer only to `reviews/`. Only the builder writes code.

### 10. Stage state machine + realtime callback — `custom_7_micro_sdlc_agent/backend/main.py`
```python
valid_transitions = {"idle": ["plan", "archived"], "plan": [], "build": [], "review": [],
                     "shipped": ["errored", "archived"], "errored": ["idle", "archived"],
                     "archived": ["idle"]}

async def on_message(formatted, stage):
    counts = await append_agent_message(ticket_id, formatted, stage)
    await ws.send_json({"type": "agent_message", "ticket_id": ticket_id,
                        "message": formatted, "counts": counts})
```
Each stage gets its own client and its own stored session ID. Workflows run as named `asyncio` tasks so several tickets can run at once.

### 11. Long-running agent with session rotation — `custom_8_ultra_stream_agent/backend/main.py`
```python
while running:
    await client.query(str(cursor))
    async for msg in client.receive_response():
        ...
    processed += batch
    if processed >= ROTATE_AFTER:
        await client.disconnect()
        client = await new_client(resume=None)   # fresh context; the lesson resumed the same session
        processed = 0
```
Persist the summaries the agent produced to the DB. The next session reads them through a tool instead of carrying them in context.

### 12. JSON-contract output — `custom_6_tri_copy_writer/backend/main.py`
*Use when the agent has no tools and must return data.* The prompt says *"Output ONLY valid JSON"* with a fixed schema. The host finds the last opening key, strips code fences, and runs `json.loads`, retrying on failure. Prefer pattern 7 when you can register a tool.

---

## Model selection by role

| Role | Alias | Why |
|---|---|---|
| Planner, reviewer, orchestrator of complex work | `opus` | Reasoning depth pays off once and feeds many steps |
| Builder, general worker | `sonnet` | Strong coding at lower cost and latency |
| Summarizer, classifier, autocomplete, pong-class | `haiku` | Fast and cheap; high call volume |

← [Pillar 3 overview](README.md)
