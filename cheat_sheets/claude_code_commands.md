# Claude Code Command Cheat Sheet

## CLI flags used across the lessons

| Command | Purpose |
|---|---|
| `claude --model opus` / `sonnet` / `haiku` | Pick the model by alias (always resolves to the latest) |
| `claude -p "<prompt>"` | Print (headless) mode, one shot |
| `claude --output-format text\|json\|stream-json` | Output format for headless runs |
| `claude --append-system-prompt "<rules>"` | Add rules to the default system prompt (technique #10) |
| `claude --mcp-config <file> --strict-mcp-config` | Load only these MCP servers (technique #2) |
| `claude --settings <file>` | Per-run settings, e.g. an output style (technique #4) |
| `claude --resume` / `claude -r <session>` | Resume a session |
| `claude --dangerously-skip-permissions` | Skip permission prompts. **Only in sandboxes/containers.** |
| `claude mcp list` / `add` / `remove` | Manage MCP servers |

## Aliases (from lesson 9)

```bash
alias cld="claude"
alias cldp="claude -p"
alias cldo="claude --model opus"
alias clds="claude --model sonnet"
alias cldys="claude --dangerously-skip-permissions --model sonnet"
alias cldyo="claude --dangerously-skip-permissions --model opus"
alias cldpy="claude -p --dangerously-skip-permissions"
alias cldr="claude --resume"
```

## In-session commands

| Command | Use |
|---|---|
| `/context` | See the context breakdown (measure first) |
| `/clear` | Reset context; follow with a prime |
| `/compact` | Avoid for single agents; the fleet uses it at 80% for long-lived workers |
| `/output-style` | Switch output style |
| `/agents` | Manage sub-agents |

## Reusable slash commands in this repo

| Command | Level | Lesson | Purpose |
|---|---|---|---|
| `/prime`, `/prime_cc` | L2 | 9, 10 | Task-specific context priming |
| `/quick-plan <req>` | L2 | 9, 10 | Plan to `specs/` |
| `/build <spec>` | L3/L5 | 9, 10 | Implement a plan (higher-order) |
| `/load_ai_docs` | L4 | 9, 10 | Sub-agents refresh `ai_docs/` |
| `/load_bundle <jsonl>` | L2 | 9 | Remount a previous agent's context |
| `/background <prompt> <model> <report>` | L4 | 9, 10 | Background primary agent |
| `/parallel_subagents <req> <n>` | L4 | 10 | Fan out N sub-agents |
| `/t_metaprompt_workflow <desc>` | L6 | 10 | Generate a new prompt |
| `/experts:cc_hook_expert:*` | L7 | 9, 10 | Plan/build/improve expert (Gen 1) |
| `/scout_plan_build <req> <docs>` | L4 | 11 | Scout → plan → build chain |
| `/plan_w_scouters <req>` | L4 | 12 | Scout swarm → plan |
| `/build_in_parallel <spec>` | L4 | 12 | One build-agent per file, batched |
| `/orch_one_shot_agent`, `/orch_scout_and_build`, `/orch_plan_w_scouts_build_review` | L4 | 12 | Orchestrator fleet patterns |
| `/experts:<domain>:question\|plan\|self-improve\|plan_build_improve` | L7 | 13, 14 | Gen 2 experts |
| `/plan`, `/review`, `/fix` | L2/L3 | 14 | ADW steps with fixed outputs |

## Hook events worth wiring

`PreToolUse` (block dangerous commands, scope writes) · `PostToolUse` (context bundles, file tracking) · `UserPromptSubmit` (bundle prompts) · `Stop` / `SubagentStop` (completion signals) · `PreCompact` (token accounting) · `SessionStart` / `SessionEnd` · `Notification`.
