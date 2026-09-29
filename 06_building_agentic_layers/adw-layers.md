# ADW Layers — Building an AI Developer Workflow

> **BLUF:** An ADW is a plain script that runs a fixed sequence of agent steps. Each step is one fresh agent executing one slash command, and each writes its output to a known place. The script (not the model) decides what runs next, records state in a database row, and logs every agent event. Build the smallest one first (plan → build), then add review → fix, then hand it to an orchestrator.

## Build order

| Step | Add | Why |
|---|---|---|
| 1 | Slash commands with **fixed output locations** (`/plan` → `specs/`, `/review` → `app_review/`) | Deterministic code needs a predictable handle on each agent's output |
| 2 | A typed SDK wrapper (`query_to_completion`, `quick_prompt`) | One place for options, hooks, cost capture, and error handling |
| 3 | `adw_plan_build.py` | Smallest useful pipeline |
| 4 | State row + step logging | Resume, audit, and a UI can read progress |
| 5 | `review` + conditional `fix` | Quality gate without a human |
| 6 | Trigger (CLI → orchestrator tool → webhook or cron) | Hand off without watching |
| 7 | ADW expert (`experts/adw/`) | The workflow system keeps its own documentation current |

## Minimal ADW skeleton (pattern from `adw_plan_build_review_fix.py`)

```python
#!/usr/bin/env -S uv run
# /// script
# dependencies = ["claude-agent-sdk", "asyncpg", "pydantic"]
# ///
"""ADW: plan -> build -> review -> fix(on FAIL). Receives only --adw-id; everything else comes from the DB."""
import argparse, asyncio, json, re
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, ResultMessage

STEPS_TOOLS = {
    "plan":   ["Read", "Glob", "Grep", "Bash", "Write", "Edit", "Task", "TodoWrite", "WebFetch"],
    "build":  ["Read", "Glob", "Grep", "Bash", "Write", "Edit", "Task", "TodoWrite"],
    "review": ["Read", "Glob", "Grep", "Bash", "Write"],          # no Edit: analysis only
    "fix":    ["Read", "Glob", "Grep", "Bash", "Write", "Edit", "Task", "TodoWrite"],
}

async def run_step(step: str, prompt: str, cwd: str, model: str, max_turns: int = 80) -> ResultMessage:
    options = ClaudeAgentOptions(
        model=model,                        # alias: "opus" | "sonnet" | "haiku"
        cwd=cwd,
        allowed_tools=STEPS_TOOLS[step],
        permission_mode="acceptEdits",      # set explicitly; never rely on an unmapped flag
        max_turns=max_turns,                # hard cap per step
        setting_sources=["project"],        # load the target repo's .claude/commands + hooks
    )
    result = None
    async with ClaudeSDKClient(options=options) as client:
        await client.query(prompt)
        async for msg in client.receive_response():
            if isinstance(msg, ResultMessage):
                result = msg
    if result is None or result.is_error:
        raise RuntimeError(f"{step} failed")
    return result

def parse_marker(text: str, key: str) -> str:
    """Steps must end with a machine-readable line, e.g. 'PLAN_PATH: specs/x.md' or 'VERDICT: PASS'."""
    m = re.search(rf"^{key}:\s*(\S+)\s*$", text, re.MULTILINE)
    if not m:
        raise ValueError(f"missing {key} marker")
    return m.group(1)

async def main(adw_id: str) -> None:
    adw = await db_get_adw(adw_id)                       # input_data: prompt, working_dir, models
    p, cwd = adw["input_data"]["prompt"], adw["input_data"]["working_dir"]
    await db_status(adw_id, "in_progress", step="plan")
    plan = await run_step("plan", f"/plan {json.dumps(p)}", cwd, "opus")
    plan_path = parse_marker(plan.result, "PLAN_PATH")
    await db_status(adw_id, "in_progress", step="build")
    await run_step("build", f"/build {plan_path}", cwd, "sonnet")
    for attempt in range(2):                             # bounded review -> fix loop
        await db_status(adw_id, "in_progress", step=f"review_{attempt}")
        review = await run_step("review", f"/review {json.dumps(p)} {plan_path}", cwd, "opus")
        if parse_marker(review.result, "VERDICT") == "PASS":
            break
        review_path = parse_marker(review.result, "REVIEW_PATH")
        await db_status(adw_id, "in_progress", step=f"fix_{attempt}")
        await run_step("fix", f"/fix {json.dumps(p)} {plan_path} {review_path}", cwd, "opus")
    else:
        await db_status(adw_id, "failed", step="review", error="unresolved blockers after 2 fix passes")
        return
    await db_status(adw_id, "completed")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--adw-id", required=True)
    asyncio.run(main(ap.parse_args().adw_id))
```

`db_get_adw` and `db_status` are your persistence functions. Lesson 14 implements them in [`adw_database.py`](../14.orchestrator-agent-with-adws-singularity/adws/adw_modules/adw_database.py) over the `ai_developer_workflows` table, and pairs them with WebSocket broadcasts in `adw_logging.py`.

**What this skeleton changes from the lesson code:**
- Steps emit **explicit markers**: `PLAN_PATH:`, `VERDICT:`, `REVIEW_PATH:`. The script doesn't guess by file modification time or substring search.
- The review → fix loop is **bounded** (2 passes) and fails loudly instead of shipping.
- `permission_mode` and `max_turns` are set explicitly per step.

Add one line to each command's Report section, e.g. `End your response with a final line: VERDICT: PASS or VERDICT: FAIL`.

## State table (from migration `9_ai_developer_workflows.sql`)

| Column | Purpose |
|---|---|
| `id`, `orchestrator_agent_id`, `adw_name`, `workflow_type` | Identity |
| `status` | `pending → in_progress → completed / failed / cancelled` |
| `current_step`, `total_steps`, `completed_steps` | Progress for the UI |
| `input_data`, `output_data` (JSONB) | **The contract**: the prompt and working directory in; paths and verdicts out |
| `started_at`, `completed_at`, `duration_seconds` | Timing |
| `error_message`, `error_step`, `error_count` | Failure triage |

Agent rows and log rows carry `adw_id` and `adw_step`, so every tool call is traceable to a workflow step.

## Triggers

| Trigger | Lesson 14 | Production addition |
|---|---|---|
| CLI | `adw_manual_trigger.py <name> <type> <prompt> <dir> [model]` | ✔ keep for testing |
| Orchestrator tool | `start_adw` → DB row → detached `uv run adw_<type>.py --adw-id` | ✔ plus log files per ADW |
| Issue / PR label webhook | not present | map a label to a workflow type |
| Cron | not present | nightly `review`-only ADW on main |

## ADW catalog to build next

| ADW | Steps | Gate |
|---|---|---|
| `plan_build` | plan → build | none (for low blast radius) |
| `plan_build_test` | plan → build → test | test exit code |
| `plan_build_review_fix` | as above | review verdict |
| `expert_plan_build_improve` | expert plan → build → self-improve | self-improve report |
| `patch` | build from an issue body → test | tests |

*"Want `plan_build_test`? Copy a workflow, swap `/review` for `/test`."*

← [Pillar 6 overview](README.md)
