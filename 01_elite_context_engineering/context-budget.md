# Context Budget — Allocating the Window

> **BLUF:** Treat the context window like a budget with fixed overhead, a working allowance and a reserve. Keep the overhead (system prompt, tools, MCP servers, memory file) under about 15% of the window, spend the working allowance on task-specific priming and reads, and never let a single agent spill over into a compaction. When the budget won't fit the task, split the task across agents rather than squeezing more into one.

The lesson's numbers assume a 200K window. The ratios still hold for larger windows because effective performance drops as context grows, whatever the maximum.

## Budget layers

| Layer | What's in it | Target share | Lever (technique #) |
|---|---|---|---|
| **Fixed overhead** | Claude Code system prompt, built-in tools | unavoidable | #10 only (append or override) |
| **Controllable overhead** | MCP tool schemas, `CLAUDE.md`, sub-agent listings | **≤ 5%** | #2 no default MCP, #3 concise memory file |
| **Priming** | `/prime*` reads, context map, plan/spec | 5–15% | #3 priming, #6 a spec replaces exploration |
| **Working set** | Task reads, tool output, edits | the rest | #10 incremental reads, #5 delegate heavy reads |
| **Output** | Chat responses (3–5× input price) | minimal | #4 output styles |
| **Reserve** | Headroom so the agent finishes without compacting | ≥ 20% | #7 reset/prime, #9 split the task |

## Measured reference points (lesson 9 demo)

| Item | Tokens | Share of 200K |
|---|---|---|
| Boot with bloated setup | 63K | 31% |
| Four MCP servers | 24K | ~12% |
| One Firecrawl MCP server alone | 6–7K | ~3% |
| `CLAUDE.large.md` | 23K | ~10% |
| `CLAUDE.concise.md` | ~350 | 0.2% |
| Default "hi" response vs "Done." style | ~150 vs 2 | output |
| One doc-scraper sub-agent (kept out of the primary window) | ~3K each | delegated |

## Budget procedure (run before any long or repeated task)

1. **Boot audit:** start a fresh agent → `/context`. If the controllable overhead is over 5%, cut MCP servers and trim the memory file.
2. **Estimate the working set:** put a token counter on the files the task touches. Anything above about 40% of the window is a planner/builder split or a sub-agent fan-out.
3. **Pick the output style:** `concise-done` for build agents, verbose styles only for planners and reviewers whose output a human reads.
4. **Set a stop rule:** if `/context` passes about 80%, stop, write a context bundle or handoff note, then `/clear` and `/prime`.
5. **Record it:** name MCP configs with their cost (`.mcp.json.<server>_<N>k`) so the budget is visible without measuring again.

## Scaling math

Waste multiplies with agent count: `waste_per_agent × agents_per_hour × hours`. A 10K-token MCP overhead × 5 agents/hour is 50K tokens/hour, a quarter of a 200K window burned on unused tool schemas. For out-of-loop pipelines (ADWs), budget per stage, not per pipeline: each stage is a fresh agent with its own full budget.

## Domain notes

| Domain | Typical budget trap | Fix |
|---|---|---|
| Quant trading | Loading raw OHLCV or trade logs into context | Have a tool or script compute stats and return a summary table |
| Cybersecurity | Pasting full SIEM exports | One sub-agent per source, returning IOCs and timelines only |
| Systems automation | `terraform plan` / `kubectl get -o yaml` dumps | Filter with `jq`/`yq` before the agent reads, or read in chunks (#10) |
| Software | Reading whole generated files and lockfiles | Context map plus targeted `Grep`; exclude lockfiles from primes |

← [Pillar 1 overview](README.md)
