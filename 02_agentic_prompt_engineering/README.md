# 02 · Agentic Prompt Engineering — the 7 Levels

> **BLUF:** *"The prompt is the fundamental unit of engineering."* Build a library of reusable prompts from **composable sections** (swappable Lego blocks) in one **consistent format**, written for the **stakeholder trifecta**: you, your team, and your agents. Levels 1–4 cover 80–90% of real work. The **Workflow** section is the single most valuable block. The biggest speed-up comes at level 6, the template meta prompt that writes your other prompts.

**Source:** Lesson 10 transcript ([summary](../transcripts_summary/10_seven_levels.md)) and code in [`10. agentic-prompt-engineering/.claude/commands/`](../10.%20agentic-prompt-engineering/README.md).

**Mental model:** every prompt is **Input → Workflow → Output**. Variables are the input and Report is the output; those two are what you and your team scan. The workflow is what the agent executes, and it is where you spend your tuning time.

**Litmus test:** *"If I handed this to a coworker, could they complete this work top to bottom?"* If yes, the prompt is probably good. Keep the format identical across prompts, because *"consistency is the greatest weapon against confusion."*

---

## The 7 levels

| Lvl | Format | What it adds | Required / key sections | Example prompts in the repo |
|---|---|---|---|---|
| 1 | **High-level prompt** | Reusable, ad hoc, static one-off | Title, **High-level prompt** (required), Purpose | `all_tools.md`, `start.md` |
| 2 | **Workflow prompt** | A sequential step-by-step play | Metadata, **Workflow** (required), Variables, Instructions, Report, Relevant Files, Codebase Structure | `prime.md`, `build.md`, `quick-plan.md`, `prime_tier_list.md` |
| 3 | **Control-flow prompt** | Conditions, loops and early returns *inside* the workflow | Same as 2, with `if…STOP` lines and `<loop>` blocks | `build.md`, `create_image.md`, `edit_image.md` |
| 4 | **Delegate prompt** | Launches other agents (sub-agents or primary agents) | Variables with agent config (model, count, tools) | `parallel_subagents.md`, `load_ai_docs.md`, `background.md` |
| 5 | **Higher-order prompt** | Takes *another prompt/plan file* as input | A variable that is a path to a prompt or spec | `build.md` (takes `PATH_TO_PLAN`) |
| 6 | **Template meta prompt** | A prompt that *creates* prompts in a fixed format | **Specified Format / Template**, Documentation (a context map) | `t_metaprompt_workflow.md`, `plan_vite_vue.md` |
| 7 | **Self-improving prompt** | A prompt whose content gets *updated* by agents | **Expertise** (dynamic, agent-maintained) | `experts/cc_hook_expert/*` |

Copy-paste templates for each level: [`templates/`](templates/).

---

## Section tier list (graded for user prompts)

Each grade gives usefulness first, then the skill needed to operate it (S = highest). The transcript's grades are used where it states them; ⚑ marks a relative placement the lesson describes without naming an exact tier.

| Section | Usefulness | Skill | Notes |
|---|---|---|---|
| **Workflow** | **S** | C | The step-by-step play. Claude Code turns it into its to-do list. |
| Variables | A | B | Dynamic (`$1`, `$ARGUMENTS`) and static (`PLAN_OUTPUT_DIRECTORY: specs/`). Refer to them by `NAME` throughout. |
| Examples | A | low ⚑ | Shows the output or result you want; a big effect for little effort. |
| **Expertise** (L7) | A | A–S | Agent-maintained knowledge; the section is easier than the full prompt around it. |
| Purpose | B | D | One direct sentence addressed to the agent: *"Create a detailed implementation plan…"* |
| Report | above Metadata ⚑ | ⚑ | Output format: JSON, YAML, a fixed template, required fields. |
| Instructions | ≈ Report ⚑ | ⚑ | Supporting rules for the workflow. They matter more in **system** prompts. |
| High-level prompt | decent value | no skill | A great place to start and a terrible place to end. |
| Metadata | C | C | Frontmatter: `description`, `argument-hint`, `allowed-tools`, `model`. |
| Codebase Structure (context map) | C | low | A map of *where* files are. Speeds the agent up; it doesn't make the agent more capable. |
| Relevant Files | C | C | A lighter version of the context map. |
| Title | C | D | |

**Prompt formats themselves:** Workflow prompt A/C · Control-flow A/B · **Delegate S/A** · Higher-order B/A · **Template meta prompt S-tier value, very hard** · Self-improving A/A–S.

**Rule:** only add a section when you need it. `edit_image.md` has no Report because the output format doesn't matter there.

---

## Level details

### L1 — High-level prompt
Once you've done something three times, *"three times marks a pattern"*: paste it into `.claude/commands/<name>.md` and move it up the levels later.

### L2 — Workflow prompt
- **Workflow vs Instructions:** the workflow is the ordered play; instructions are supporting rules for its steps. Nested bullets under workflow steps are often enough.
- **Static vs dynamic variables:** change a static variable once (for example `specs/` → `prds/`) and every reference follows.
- **Codebase Structure** gives a map but tells the agent *"IMPORTANT: Read these files exclusively"* in the workflow. Strong, information-dense keywords (`IMPORTANT`, `STOP`, `THINK HARD`) carry weight with the model.

### L3 — Control flow
```md
- If no `PATH_TO_PLAN` is provided, STOP immediately and ask the user to provide it.
...
- IMPORTANT: Then generate `NUMBER_OF_IMAGES` images following the `image-loop` below.
<image-loop>
  - Call the generation tool with MODEL and ASPECT_RATIO
  - Wait for completion; save prompt + output to IMAGE_OUTPUT_DIR/<date_time>/
</image-loop>
```
XML-style tags mark where the loop starts and ends for both the agent and the human reading the prompt.

### L4 — Delegate
The primary agent becomes **the prompt engineer for its sub-agents**. `parallel_subagents.md` step 2: *"Create detailed, self-contained prompts for each agent… Define clear output expectations… Remember agents are stateless and need complete context."* Launch all of them in a single parallel batch. Non-determinism works in your favor here: N agents give N different angles. This is the **D** in R&D ([pillar 1](../01_elite_context_engineering/README.md)).

### L5 — Higher-order
Scaffolds a stable outer workflow and takes the variable part (a plan or spec) as input: `/build specs/<plan>.md`. Pair it with any planner (`/quick-plan`, chore/feature/bug planners, experts).

### L6 — Template meta prompt
A prompt that builds prompts. Key blocks: a **Documentation** context map (`WebFetch` everything first, one `Task` per doc in parallel) and a **Specified Format** whose `<placeholders>` the agent fills in. It also enforces *"Do not create any additional sections…"*, puts dynamic variables before static ones, and prefers `$1, $2` over `$ARGUMENTS`. Plan templates such as `plan_vite_vue.md`'s *Plan Format* are the same idea applied to specs. *"Once you can create the prompt that helps you create prompts, you start moving much faster."*

### L7 — Self-improving
The **Expertise** section is live context. A separate *improve* prompt analyzes `git diff`, decides whether there's anything worth learning (and stops if not), and updates **only** the `## Expertise` sections of the plan and build prompts, never their workflows. See [pillar 5](../05_agent_experts/README.md).

---

## System prompts vs user prompts

| | User prompt | System prompt |
|---|---|---|
| Scope | One conversation turn or task | **Rules for every conversation**; can't change mid-conversation |
| Blast radius | One run; iterate to success | *"Mistakes scale to everything"*, roughly 1–3 orders of magnitude more impact |
| Key sections | Everything in the tier list | **Purpose, Instructions, Examples** (plus a *loose* workflow when needed) |
| Avoid | n/a | Dynamic variables, rigid workflows (*"workflows reduce agency to increase determinism"*), templates, expertise, relevant files |

Where you touch system prompts: sub-agent definitions (`.claude/agents/*.md` *are* system prompts; the only dynamic input is what the primary agent passes), `--append-system-prompt` (safe, additive), and SDK full overrides (dangerous; [pillar 3](../03_claude_agent_sdk_mastery/README.md)).

## Domain adaptation

| Level | Trading | Cybersecurity | Systems automation |
|---|---|---|---|
| L2 workflow | `/backtest <strategy> <range>` → run, compute metrics, report a table | `/triage <alert_id>` → enrich, score, report a verdict | `/drift_check <env>` → plan, diff, summarize |
| L3 control flow | STOP if the data range is under 2 years; loop over parameter grid | loop per IOC; STOP if the asset isn't in inventory | STOP on a prod plan with deletes; loop per module |
| L4 delegate | one sub-agent per symbol | one sub-agent per log source | `/background` per region |
| L6 meta | generates new `/backtest_*` prompts in house format | generates detection-rule prompts | generates runbook prompts |
| L7 expert | strategy expert learns from past backtests | detection expert learns from false positives | infra expert learns from failed applies |

**Next:** [templates](templates/) · [pillar 3: SDK](../03_claude_agent_sdk_mastery/README.md)
