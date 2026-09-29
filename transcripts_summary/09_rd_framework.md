# Lesson 9 — Elite Context Engineering: The R&D Framework (transcript summary)

> **Source:** [`9. rd-framework-context-window-mastery-v1 mp4.txt`](../9.%20rd-framework-context-window-mastery-v1%20mp4.txt) (~73 min) · code: [`9. elite-context-engineering/`](../9.%20elite-context-engineering/README.md) · pillar: [01](../01_elite_context_engineering/README.md)

## BLUF
The context window is *"a precious, renewable, but limited temporal resource"* and the single most important leverage point in agentic coding. There are **only two ways to manage it: Reduce and Delegate.** The lesson teaches 12 techniques at four levels (beginner, intermediate, advanced, agentic) and ends on **agent experts**. The real skill is *"search and destroy"*: removing and delegating context before it causes rot and bloat. *"It's not about saving tokens. It's about spending them properly."*

## Timeline

| Time | Segment | Key points |
|---|---|---|
| 0:00 | Framing | *"A focused agent is a performant agent."* Context sweet spot; the core four (context, model, prompt, tools); three levels plus a hidden fourth |
| 2:26 | R&D | Adding context is easy; finding it agentically, then removing or delegating it, is the skill |
| 3:10 | **#1 Measure** | `/context` showed 63K tokens (31%) used at boot; a token counter shows the README costs 2.6K per read |
| 5:40 | **#2 Avoid MCP** | 4 servers = 24K (~12%). Delete the default `.mcp.json`; `--mcp-config <file> --strict-mcp-config`; name configs by token cost |
| 9:21 | **#3 Prime, not CLAUDE.md** | A 23K-token memory file triggered the warning; always-on context grows, goes stale, and contradicts itself. Concise file ~350 tokens; `/prime` = Run/Read/Report; stacked `/prime_cc` |
| 16:26 | **#4 Output tokens** | Output costs 3–5× input. The "One Word Output" style gives 2 tokens vs ~150; output styles hot-swap a block of the system prompt |
| 22:42 | **#5 Sub-agents** | Partially forked context; a sub-agent definition is a *system prompt* (122 vs 900 tokens); `/load_ai_docs` kept ~40K tokens out of the primary window. Track every agent's core four |
| 28:36 | **#6 Planner/builder** | `/quick-plan` (opus) → fresh agent `/build spec`. *"Go overboard, then delete."* Builder context = surgical edits |
| 33:41 | **#7 Reset, don't compact** | After `/compact` you don't know what is in context. `/clear` + `/prime`; out-of-loop agents should never overflow |
| 37:15 | **#8 Context bundles** | Hooks write append-only JSONL of prompts, reads and writes; `/load_bundle` dedupes reads and recovers ~70% of prior state |
| 41:21 | **#9 One agent, one purpose** | Plan the problem without regard to technology, then plan the agent pipeline (the ADW) |
| 43:01 | **#10 System prompt** | `--append-system-prompt` with `-p`: read in 100-line increments, prefix ✅/❌; bundles proved fewer lines were read. A full SDK override is dangerous |
| 48:45 | **#11 Primary delegation** | `/background` launches a full Claude Code instance that reports to a file and renames it when done. *"Agents orchestrating agents."* |
| 56:25 | **#12 Agent experts** | `experts/cc_hook_expert/{plan,build,improve}`; the improve step reads `git diff` and updates only `## Expertise`; demo built a universal hook logger in one shot |
| 1:09:18 | Future bets | Larger windows, better effective windows, hot-swapped context, multi-agent architectures, specialized agents everywhere |

## Quotable
- *"What gets measured gets managed."*
- *"Prime, don't default."*
- *"The context window of your agents should not be handed off to any tool or team."*
- *"We build the system that builds the system."*
- *"What's better than an agent? Many focused specialized agents."*

## Aliases used in the demo

```bash
alias cldys="claude --dangerously-skip-permissions --model sonnet"
alias cldyo="claude --dangerously-skip-permissions --model opus"
alias cldpy="claude -p --dangerously-skip-permissions"
```
