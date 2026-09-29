# 05 · Agent Experts — Turning Forgetful Agents into Learning Systems

> **BLUF:** *"Your agents forget. And that means your agents don't learn."* An **agent expert** fixes that with a loop, **ACT → LEARN → REUSE**, and an **expertise file**: a YAML "mental model" of one domain that the agent itself maintains. The code stays the source of truth. The expertise file is working memory that the agent **validates against the code** before trusting it. You don't edit expertise by hand; *"you teach your agents how to learn by writing self-improve prompts."*

**Sources:** lesson 9 transcript (technique #12, the first version of the pattern) and code in [`13. agent-experts/`](../13.%20agent-experts/README.md) and [`14.orchestrator-agent-with-adws-singularity/.claude/commands/experts/adw/`](../14.orchestrator-agent-with-adws-singularity/.claude/commands/experts/adw/expertise.yaml). Lesson 13 has no transcript; this pillar is derived from its code and README ([summary](../transcripts_summary/13_agent_experts_code_derived.md)).

---

## Two generations of the pattern

| | Gen 1 — lessons 9 and 10 | Gen 2 — lessons 13 and 14 |
|---|---|---|
| Where the knowledge lives | `## Expertise` section **inside** the plan and build prompts | A separate **`expertise.yaml`** next to the expert's prompts |
| Prompts | `*_plan`, `*_build`, `*_improve` | `question`, `plan`, `self-improve`, `plan_build_improve` (+ any `other.md`) |
| How it learns | *improve* reads `git diff`, edits only the Expertise sections | *self-improve* validates the **whole file against the code**, optionally focused by `git diff` and a `FOCUS_AREA` |
| Size control | none | `MAX_LINES: 1000`, enforced with a `wc -l` trim loop |
| Validation | none | YAML parse check: `python3 -c "import yaml; yaml.safe_load(open(F))"` |
| Example | [`cc_hook_expert/`](../10.%20agentic-prompt-engineering/.claude/commands/experts/cc_hook_expert/cc_hook_expert_improve.md) | [`experts/database/`, `experts/websocket/`](../13.%20agent-experts/.claude/commands/experts/websocket/expertise.yaml), [`experts/adw/`](../14.orchestrator-agent-with-adws-singularity/.claude/commands/experts/adw/expertise.yaml) |

**Use Gen 2.** A standalone file can be shared across all of an expert's prompts, parse-checked, and kept to a size limit. It also keeps workflows stable because the knowledge never touches them.

---

## Anatomy of a codebase expert (Gen 2)

```
.claude/commands/experts/<domain>/
├── expertise.yaml          # mental model (agent-owned, ≤1000 lines)
├── question.md             # REUSE — read-only Q&A, validated against code
├── plan.md                 # REUSE — loads expertise, then delegates to /plan
├── self-improve.md         # LEARN — resync expertise with the code
└── plan_build_improve.md   # ACT+LEARN+REUSE — the full chain via fresh subagents
```

Invoke with namespaced slash commands: `/experts:<domain>:question "<q>"`, `/experts:<domain>:plan "<req>"`, `/experts:<domain>:self-improve true [focus]`, `/experts:<domain>:plan_build_improve "<req>"`.

### expertise.yaml
There is no fixed schema (*"Let the agent define and maintain this structure"*). The real files converged on this shape: `overview → core_implementation (by file: file/lines/purpose) → domain sections → key_operations → testing → best_practices → known_issues`, with optional `key_file_locations` and `architecture_summary`. File paths and **line numbers** are pinned inline, e.g. `"get_or_create_orchestrator (line 122)"`. Ready-to-use template: [expertise-file-template.yaml](expertise-file-template.yaml).

### question.md (REUSE, read-only)
- Tools: `Bash, Read, Grep, Glob, TodoWrite`. It never writes (*"DO NOT write, edit, or create any files"*).
- Workflow: read the expertise → **validate it against the codebase** → answer with evidence (files and lines), adding diagrams where they help.

### plan.md (REUSE, higher-order)
Loads the expertise as its *mental model*, reads the critical files the expertise lists (*"back up claims in the expertise file with the source of truth in the codebase"*), then calls the generic `/plan` with the user request. The expert supplies domain context; the generic planner supplies the format.

### self-improve.md (LEARN)
Seven steps: optional `git diff` → read the whole expertise → read the key files it references and compare → list discrepancies (missing, outdated, removed-but-documented, wrong) → update → enforce `MAX_LINES` → parse-check the YAML. Instructions that carry weight:
- *"Always validate expertise against real implementation, not assumptions."*
- *"Don't include 'summaries' of work done… Focus on true, important information."*
- *"If there's nothing to be done, report that and stop."*

Full walkthrough and template: [self-improve-loop.md](self-improve-loop.md).

### plan_build_improve.md (the whole loop)
The top-level agent only orchestrates (tools: `Task, TaskOutput, TodoWrite`). Each step runs in a **fresh sub-agent** with complete instructions:
1. `/experts:<domain>:plan "<request>"` → returns the plan path (**REUSE**)
2. `/build <plan_path>` → returns files changed (**ACT**)
3. `/experts:<domain>:self-improve true` → returns the improvement report (**LEARN**)
4. Report. *"DO NOT STOP between steps."*

---

## Runtime (product) experts

Lesson 13 also applies the pattern **inside a product**, not just to the codebase:

| | Nile shop ([`agent_expert.py`](../13.%20agent-experts/apps/nile/server/src/services/agent_expert.py)) | Orchestrator autocomplete ([`autocomplete_agent.py`](../13.%20agent-experts/apps/orchestrator_3_stream/backend/modules/autocomplete_agent.py)) |
|---|---|---|
| Expertise store | `expertise` DB row per user: `expertise_data` JSON (`viewed_products`, `added_to_cart`, `checked_out`), `total_improvements` | YAML file: `previous_completions` (accepted vs typed-own) |
| LEARN | **Deterministic code**: every view, add-to-cart or checkout increments counts (no model involved) | Each accepted or rejected suggestion is appended |
| REUSE | Top 10 recent items per signal injected into `{{…}}` placeholders in the system prompt; signals ranked *checkout > cart > view* | Full history injected into `{{PREVIOUS_AUTOCOMPLETE_ITEMS}}` |
| Agent | Agent SDK, haiku, built-in tools disabled, two custom MCP tools (`find_related_products`, `stream_section`) | Agent SDK, haiku, resumed session |
| Guardrails | zero-state fallback, reset endpoint, live-prompt inspection endpoint | resets when the orchestrator changes |

**Lesson for your own builds:** do the learning **deterministically** in code wherever the signal is structured, and use the model only to *reuse* the result. That is cheaper, testable, and can't hallucinate its memory.

**Known gaps to fix if you copy it:** Nile's SDK session map is in-memory (lost on restart), and the autocomplete history has no cap. Cap it the way self-improve caps YAML.

---

## Meta-agents: experts that build the agentic layer
- **`meta-agent`** (`.claude/agents/meta-agent.md`) writes new sub-agent files: frontmatter plus exactly Purpose / Instructions / Workflow / Report.
- **`meta-skill`** (`.claude/skills/meta-skill/SKILL.md`) writes new Skills. It enforces a gerund name, a third-person *what + when* description, a body under 500 lines, and progressive disclosure.
- **`meta_prompt.md`** writes new slash commands in the house format (Level 6, [pillar 2](../02_agentic_prompt_engineering/templates/level-6-template-meta.md)).

Together these let the agentic layer generate new experts in a consistent format.

---

## Rollout procedure (for any domain)

1. **Pick one risky or complex area** (billing, auth, the database layer, the strategy engine, detection rules).
2. Create `.claude/commands/experts/<domain>/` with a *seed* `expertise.yaml` (just `overview` and `key_files`).
3. Add `self-improve.md` and `question.md` from the templates here.
4. **Bootstrap:** run `/experts:<domain>:self-improve true` repeatedly *"until your agent stops finding new things to update."*
5. Add `plan.md` and `plan_build_improve.md`. From then on, route changes in that domain through the chain.
6. After merges, run self-improve with `true` so the expertise absorbs the diff.
7. Review expertise diffs in PRs like code. It is agent-owned but human-audited.

## Domain adaptation

| Domain | Expert | Expertise sections worth seeding | LEARN trigger |
|---|---|---|---|
| Quant trading | `strategy` | signal definitions, data sources and their quirks, risk limits, known overfitting traps | after each backtest/strategy change: `self-improve true` |
| Cybersecurity | `detections` | rule inventory, log-source schemas, known false-positive patterns, response playbooks | after each tuned rule or closed incident |
| Systems automation | `infra` | module map, env differences, apply-order constraints, past failure modes | after each apply, both failed and successful |
| Software | `database`, `websocket`, `billing` | as in lesson 13 | after each merged PR touching the domain |

**Next:** [expertise-file-template.yaml](expertise-file-template.yaml) · [self-improve-loop.md](self-improve-loop.md) · [pillar 6: agentic layers](../06_building_agentic_layers/README.md)
