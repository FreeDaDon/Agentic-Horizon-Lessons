# 01 · Elite Context Engineering — the R&D Framework

> **BLUF:** There are only two ways to manage an agent's context window: **R**educe what goes in, and **D**elegate work to other context windows. Every one of the 12 techniques below is one or both. Measure first, prime instead of bloating memory files, reset instead of compacting, and scale by adding focused agents rather than stuffing one.

**Source:** Lesson 9 transcript ([summary](../transcripts_summary/09_rd_framework.md)) and code in [`9. elite-context-engineering/`](../9.%20elite-context-engineering/README.md).

**Core belief:** *"A focused agent is a performant agent."* Every agent has a **sweet spot**, a range of context in which it performs at full capability for its task. Context engineering is how you hit that sweet spot on every run. Adding the right context is the easy part. The real skill is **"search and destroy"**: finding context agentically, then removing or delegating everything else before it turns into **context rot** (stale or contradictory state) or **context bloat** (irrelevant state).

---

## The 12 techniques at a glance

| # | Technique | Level | R / D | One-line rule |
|---|---|---|---|---|
| 1 | Measure to manage | Beginner | Foundation | Run `/context` and use a tokenizer. What gets measured gets managed. |
| 2 | Avoid default MCP servers | Beginner | Reduce | No default `.mcp.json`. Load servers per task with `--mcp-config … --strict-mcp-config`. |
| 3 | Prime more, `CLAUDE.md` less | Beginner | Reduce | Keep the memory file to 100%-of-the-time universals and prime per task with `/prime*`. |
| 4 | Control output tokens | Intermediate | Reduce | Output styles such as "Done." cut response tokens by about 99%. |
| 5 | Use sub-agents properly | Intermediate | Delegate | Sub-agents fork context. Their work stays out of the primary window. |
| 6 | Architect/editor (planner/builder) | Intermediate | R&D | One agent plans to a spec; a fresh agent builds from it. |
| 7 | Reset and prime instead of `/compact` | Advanced | Reduce | `/clear` then `/prime`, so you know exactly what is in context. |
| 8 | Context bundles | Advanced | Reduce | Hooks log reads, writes and prompts, and `/load_bundle` remounts a new agent. |
| 9 | One agent, one purpose | Advanced | R&D | Design the pipeline of agents (the ADW), and ship one thing per agent. |
| 10 | System prompt control | Agentic | Reduce | `--append-system-prompt` steers behavior. A full override is dangerous. |
| 11 | Primary multi-agent delegation | Agentic | Delegate | `/background` launches a full, independent agent that reports to a file. |
| 12 | Agent experts | Agentic | R&D | Plan, build and improve prompts with a self-updating `## Expertise` section. |

The levels are **Beginner → Intermediate → Advanced → Agentic**. The fourth, "hidden" level is where your patterns start scaling into pipelines. Mistakes at that level scale too.

---

## Beginner

### 1. Measure to manage
- **`/context`** shows exactly what your agent loads with every prompt: system prompt, tools, MCP tools, memory files and messages. In the lesson demo, **63K tokens (31%) were spent before the first prompt.**
- **A token counter in your editor** shows what a file will cost *before* the agent reads it. A README that agents read often (2.6K tokens in the demo) is a per-read tax.
- Without measurement you are "vibe coding" and limited to the easiest, already saturated work.

### 2. Avoid default MCP servers (Reduce)
- Four MCP servers cost **24K tokens (~12%)** at startup whether or not you use them. Five agents an hour at 10K each wastes 25% of a window's worth of tokens.
- **Delete the default `.mcp.json`.** Keep per-purpose configs whose file names record their token cost (the repo uses names like `.mcp.json.firecrawl_7k.sample` and `.mcp.json.all_16k.sample`).
- Load only what the task needs:

```bash
claude --mcp-config .mcp.json.firecrawl_7k --strict-mcp-config   # only this server; ignores global/user MCP
claude mcp list                                                   # audit what is loading
```

### 3. Prime more, `CLAUDE.md` less (Reduce)
- A `CLAUDE.md` is great and terrible for the same reason: **it is always loaded.** Work changes constantly, but the file only grows. It ends up irrelevant to most tasks and, in the worst case, **contradictory**. The demo's `CLAUDE.large.md` was 23K tokens and triggered Claude Code's "Large CLAUDE.md will impact performance" warning.
- Shrink it to universals you are 100% sure every agent needs 100% of the time. The demo went from 23K tokens to about 350 with [`CLAUDE.concise.md`](../9.%20elite-context-engineering/CLAUDE.concise.md).
- **Context priming** means a reusable slash command that loads task-specific context: `/prime`, `/prime_bug`, `/prime_feature`, `/prime_cc`. Primes can stack; `/prime_cc` runs `/prime` and then reads the Claude Code files. See the [priming guide](priming-guide.md).

---

## Intermediate

### 4. Control output tokens (Reduce)
- **Output tokens cost 3–5× input tokens** and get added back into context.
- **Output styles** hot-swap the output-style block of Claude Code's system prompt. The "One Word Output" style ([`concise-done.md`](../9.%20elite-context-engineering/.claude/output-styles/concise-done.md)) answers "Done." (2 tokens) instead of about 150. It has three exceptions: when explicitly asked for something else, when asked a question (answer in 1–2 sentences), and on errors (explain in 1–2 sentences).
- Apply one per run with a settings file: `claude --settings .claude/settings.local.concise.json` (it sets `"outputStyle": "One Word Output"`).
- Most output tokens come from writing files, which you cannot trim. The saving is in the chatter, and it compounds across hundreds of out-of-loop runs.

### 5. Use sub-agents properly (Delegate)
- A sub-agent is a **partially forked context window**. Its definition is a *system prompt*: it costs the primary agent about 122 tokens to list, not the 900 of the full file. Its tool calls and reads never enter the primary window.
- Example: `/load_ai_docs` sends one `docs-scraper` sub-agent per URL. That is about 3K tokens × 8–10 agents that stayed out of the primary window, roughly 40K tokens saved in total.
- **Cost:** you now track the *core four* (context, model, prompt, tools) for every agent you spawn. Information flows primary → sub-agent → primary, never to you. Give each sub-agent **one concise prompt and one focused job**, and have it return a **reduced report**. If you can't yet keep one agent's context clean, you aren't ready for sub-agents.

### 6. Architect/editor, also called planner/builder (R&D)
- `/quick-plan "<request>"` → the planner explores and writes `specs/<name>.md` → a **fresh** agent runs `/build specs/<name>.md`.
- The planner is *supposed* to burn tokens searching. The builder gets a clean window for **surgical edits**, and those writes are your most expensive output tokens.
- Stacking prompt after prompt in one chat window is how context rot builds up. **Go overboard in planning, then delete** whatever the builder doesn't need.

---

## Advanced

### 7. Reset and prime instead of `/compact` (Reduce)
- After `/compact` you don't know what is in context. It is a band-aid for a window that has already grown too large.
- Run **`/clear` then `/prime`**, rebuild to where you were, and continue. You own the state.
- Out-of-loop rule: **no single agent should overflow its window and trigger a compact.** If one does, split the task.

### 8. Context bundles (Reduce)
- Hooks write an **append-only JSONL trail** of each session's prompts, reads and writes to `agents/context_bundles/<DAY_HOUR>_<session_id>.jsonl` (e.g. `MON_14_…`). The trail is deliberately trimmed: no write contents and no read bodies.
- Wiring (from [`.claude/settings.json`](../9.%20elite-context-engineering/.claude/settings.json)):
  - `PostToolUse` matcher `Read|Write` → `context_bundle_builder.py --type file_ops`
  - `UserPromptSubmit` → `context_bundle_builder.py --type user_prompt`
- `/load_bundle <path>` has a new agent read the prompts *as a story only* (it never runs them), deduplicate file reads (a full read wins; otherwise the largest `limit` from `offset: 0`; more than 3 entries means read the whole file), and re-read each file once. That recovers **about 70% of the previous agent's state** quickly.
- Use it selectively. Replaying everything just overflows the next window.

### 9. One agent, one purpose (R&D)
- Two steps: **(1)** plan the solution for the user, ignoring technology; **(2)** plan how the work splits across agents. That split is your **AI Developer Workflow (ADW)**, the highest-leverage unit in agentic coding (see [pillar 6](../06_building_agentic_layers/README.md)).
- When something fails, fix that one stage.

---

## Agentic (the hidden level)

### 10. System prompt control (Reduce)
- `--append-system-prompt "<rules>"` adds rules without discarding Claude Code's tuned defaults. The demo forced reads in 100-line increments ("if you have enough, stop reading and proceed") and prefixed the final message with ✅/❌. The context bundle then showed `Read 100, Read 100…`, so the agent measurably read less.
- The SDK can also **replace** the system prompt entirely. The Agent SDK's `system_prompt` option does this; older SDK versions called it `customSystemPrompt`. **Only do this when you are building a domain agent on purpose.** It discards the defaults (see [pillar 3](../03_claude_agent_sdk_mastery/README.md)).
- Use this level only when nothing else works, or when you are building custom out-of-loop agents.

### 11. Primary multi-agent delegation (Delegate)
- Unlike sub-agents, these are **full, independent primary agents** with their own model, settings and prompt. You launch them via the CLI, the SDK, wrapper CLIs, MCP servers or UIs.
- The lightest version is [`/background`](../9.%20elite-context-engineering/.claude/commands/background.md), a single slash command that runs:

```bash
claude --model "$MODEL" --output-format text --dangerously-skip-permissions \
  --append-system-prompt "You are running as a background agent… continuously update $REPORT_FILE ## Progress…" \
  --print "$USER_PROMPT"
```

- The agent writes progress into a report file, which gets renamed on completion. You check the file instead of babysitting the agent. **It runs on your API key and skips permissions, so budget and sandbox accordingly.**

### 12. Agent experts (R&D)
- A three-prompt set per area of the codebase: **plan → build → improve**. Each has a dedicated `## Expertise` section. The *improve* prompt reads `git diff`/`git log`, decides whether anything is worth learning, and updates **only** the `## Expertise` sections of plan and build. It never touches their workflows.
- Chain the three as separate fresh agents; that chain is itself an ADW. Add a router agent to pick the right expert from a high-level prompt. Full pattern in [pillar 5](../05_agent_experts/README.md).

---

## What the lesson says is coming
Larger context windows · better *effective* context (less degradation as context grows) · **hot-swappable context** (tools, system prompt blocks, individual messages) · multi-agent architectures by default · **specialized agents everywhere**. The bet: model performance drops as context grows, so investing in context management keeps paying off.

> *"It's not about saving tokens. It's about spending them properly."* The goal is one-shot out-of-loop runs, not a cheaper failure.

---

## Mapping to common context-engineering vocabulary

| Common term | Where it lives in R&D |
|---|---|
| Context compression | #7 reset and prime (explicit), #8 bundles (trimmed replay), #4 output control |
| Retrieval optimization | #3 priming, the *codebase structure / context map* section ([pillar 2](../02_agentic_prompt_engineering/README.md)), #10 incremental reads |
| Dynamic priming | #3, and stacked primes (`/prime_cc` calls `/prime`) |
| Token budget allocation | #1 measurement, [context-budget.md](context-budget.md) |
| Context decay mitigation | #3 (no stale memory), #7 (no compaction drift), #9 (short-lived single-purpose agents) |

## Domain adaptation

| Domain | Reduce | Delegate |
|---|---|---|
| Software | `/prime_feature`, concise output style, no default MCP | planner/builder, doc-scraper sub-agents |
| Quant trading | `/prime_strategy` loads only the strategy module and its data schema; don't load market-data MCP servers for code edits | one background agent per backtest sweep, each writing to its own report file |
| Cybersecurity | `/prime_ir` loads the runbook and the affected asset inventory only | a sub-agent per log source (EDR, firewall, IdP) returning an IOC summary |
| Systems automation | `/prime_infra` loads the Terraform module map, not the whole repo | a `/background` drift check per environment |

**Next:** [context-budget.md](context-budget.md) · [priming-guide.md](priming-guide.md) · [Cheat sheet](../cheat_sheets/bluf_reference.md)
