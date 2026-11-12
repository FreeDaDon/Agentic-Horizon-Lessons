# Agentic Horizon — Lessons, Frameworks & Playbooks

> **BLUF:** A working curriculum for agentic engineering. Six Agentic Horizon lessons (9–14) become six pillar guides, then five production modules take the same systems to the point where you can trust them unattended: **evals, expertise drift checks, sandboxing, prompt-injection defense, and cost governance**. Every pillar has a self-grading lab. The original lesson code sits next to the guides, hardened (guard hooks that actually fire, least-privilege agents, capped and gated ADWs), and one offline CI run checks all of it with no API key and no database.

## The stack in one picture

```
 11 Cost governance       budgets per call, agent, ADW and day; circuit breakers; spend dashboard
 10 Injection defense     agents that read untrusted text get no tools; escape at the side-effect boundary
 09 Sandboxing            path confinement → worktree per agent → container with no network
 08 Expertise drift       CI proves an expert's claims about the code are still true
 07 Agent evals           hidden-test graders, oracle/noop sanity, a scoreboard per model alias
 ───────────────────────  production layer: what makes the stack below safe to leave running
 06 Agentic layers        ADWs: deterministic code orchestrating agents → the layer maintains itself
 05 Agent experts         ACT → LEARN → REUSE with agent-owned expertise files
 04 Orchestration         one conductor, a fleet of workers, 8 CRUD tools, summarized events
 03 Agent SDK             custom agents: your system prompt, your tools, sessions, hook guardrails
 02 Prompts               7 levels of reusable, composable prompts for you, your team, your agents
 01 Context               R&D: Reduce and Delegate; a focused agent is a performant agent
```

Each layer depends on the ones below it. Start at the bottom. Add the production layer before anything runs without you watching.

## Pillars

| # | Pillar | Bottom line | Lab | Lesson code | Source |
|---|---|---|---|---|---|
| 01 | [Elite Context Engineering](01_elite_context_engineering/README.md) | 12 techniques, 4 levels, 2 levers (Reduce, Delegate) | [Cut boot context](01_elite_context_engineering/lab.md) | [`9. elite-context-engineering/`](9.%20elite-context-engineering/README.md) | transcript |
| 02 | [Agentic Prompt Engineering](02_agentic_prompt_engineering/README.md) | 7 prompt levels; Workflow is the S-tier section; meta prompts give the biggest speed-up | [Control-flow prompt](02_agentic_prompt_engineering/lab.md) | [`10. agentic-prompt-engineering/`](10.%20agentic-prompt-engineering/README.md) | transcript |
| 03 | [Claude Agent SDK Mastery](03_claude_agent_sdk_mastery/README.md) | 8 agents from pong to multi-agent apps; 12 SDK patterns | [Narrow proposing agent](03_claude_agent_sdk_mastery/lab.md) | [`11. building-specialized-agents/`](11.%20building-specialized-agents/README.md) | code |
| 04 | [Multi-Agent Orchestration](04_multi_agent_orchestration/README.md) | Orchestrator + fleet CRUD + real-time observability | [Read-only fleet template](04_multi_agent_orchestration/lab.md) | [`12. multi-agent-orchestration/`](12.%20multi-agent-orchestration/README.md) | code |
| 05 | [Agent Experts](05_agent_experts/README.md) | Expertise YAML validated against the code; self-improve loop | [Drift-proof expert](05_agent_experts/lab.md) | [`13. agent-experts/`](13.%20agent-experts/README.md) | code |
| 06 | [Building Agentic Layers](06_building_agentic_layers/README.md) | 9-stage roadmap to a self-maintaining layer; ADW anatomy + hardening | [Gated ADW](06_building_agentic_layers/lab.md) | [`14.orchestrator-agent-with-adws-singularity/`](14.orchestrator-agent-with-adws-singularity/README.md) | code |

**Source** says where each pillar's content comes from: *transcript* means the lesson video transcript is in this repo; *code* means no transcript exists and the pillar is derived from the lesson's code and README (labeled in each doc).

## Production modules

| # | Module | Bottom line | What ships |
|---|---|---|---|
| 07 | [Agent Evals](07_agent_evals/README.md) | Measure whether an agent, prompt or ADW does the job, not just whether helpers pass | [`eval_harness.py`](07_agent_evals/eval_harness.py) (`run`, `report`, `check`), 4 golden tasks with hidden graders and reference solutions, [`scoreboard.md`](07_agent_evals/scoreboard.md) |
| 08 | [Expertise Drift](08_expertise_drift/README.md) | Deterministic code checks an expert's facts; the model only maintains meaning | [`check_expertise.py`](08_expertise_drift/check_expertise.py) with `--fix` for line numbers; runs on every expertise file in CI |
| 09 | [Sandboxing and Blast Radius](09_sandboxing/README.md) | A five-rung isolation ladder; climb as far as the blast radius demands | [`worktree_sandbox.py`](09_sandboxing/worktree_sandbox.py): idempotent worktree per agent, path-confinement hook, no-network container argv |
| 10 | [Prompt-Injection Defense](10_prompt_injection_defense/README.md) | Untrusted input × capability = risk; remove the capability first, detect last | [`defenses.py`](10_prompt_injection_defense/defenses.py): locked options for untrusted-input agents, quarantine, detector, PostToolUse hook; 27 red-team and 27 benign fixtures; a CI lint that bans `bypassPermissions` |
| 11 | [Cost Governance](11_cost_governance/README.md) | Track cost, then cap it at every scope | [`budget.py`](11_cost_governance/budget.py) (hierarchical ledger, circuit breaker, SDK caps), [`dashboard.sql`](11_cost_governance/dashboard.sql), [`cost_report.py`](11_cost_governance/cost_report.py) |

## Labs

Every pillar ends in a lab: a broken starter, a short guide, and an offline check. Pass the check, then compare with the reference solution.

```bash
cp labs/starters/lab3/signal_analyst.py /tmp/ && labs/check_lab.py 3 /tmp/signal_analyst.py
```

| Lab | You build | The check proves |
|---|---|---|
| 1 | A lean project boot | `CLAUDE.md` under ~1.5K tokens, no default MCP, a prime with Run/Read/Report, a terse output style |
| 2 | A level-3 prompt | Variables, numbered workflow, `STOP` early returns, a `<…-loop>` block, a Report |
| 3 | A narrow SDK agent | Only `mcp__` tools allowed, built-ins denied, turn cap, no bypass, typed `submit_*` output |
| 4 | A fleet worker template | Read-only tools, model alias, Purpose/Workflow/Report |
| 5 | An agent expert | Valid YAML under 1,000 lines whose claims pass the drift check |
| 6 | A gated ADW | Pinned deps, steps from the shared runner, plan before build, ends on a review gate |

## What the hardening changed in the lesson code

The lesson code was reviewed end to end and every gap found was fixed with a test. The highlights:

| Area | Before | Now |
|---|---|---|
| Guard hooks (lessons 9–14) | Fail open: hook commands split on the space in the folder name, scripts were not executable, and the `rm` blocker missed `find / -delete`, `git push --force`, `curl \| sh`, `terraform destroy` and more | Quoted `uv run --script` commands, one shared detector, `.env` guard on; [`test_hook_wiring.py`](tests/test_hook_wiring.py) runs the real `settings.json` strings |
| Lesson 11 apps | Any web page could drive app 7's `bypassPermissions` builder; AppleScript injection from Bluesky posts; escapable `eval`; bypassable `.env` block | Origin checks, `acceptEdits` plus write confinement, argv-only osascript, AST calculator, read-only Bash hooks |
| Orchestrator (12–14) | Summarizer ran with every tool and no permission checks on untrusted tool output; read-only scouts became writable on first command; open `/ws` and `/api/open-file` | Tool-less summarizers, template tool policy persisted per agent, origin and path guards |
| ADWs (14) | No caps, verdicts parsed from prose, plan paths picked by newest mtime, one unverified fix pass, output to `/dev/null` | Per-step permission profiles and turn/dollar/time caps, `submit_plan`/`submit_review` tools, bounded review ⇄ fix loop, run logs, `cancel_adw` |
| Nile (13–14) | Name-only login; any user's data readable by id; unsanitized `v-html` | Session tokens bound to the user, CORS from config, DOMPurify |

Full gap-by-gap tables: [pillar 4](04_multi_agent_orchestration/README.md#gaps-found-in-the-lesson-code-and-their-status) and [pillar 6](06_building_agentic_layers/README.md#hardening-checklist-gaps-found-in-the-lesson-code-and-their-status). What lessons 13 and 14 changed in the orchestrator they inherited: [12 → 13](05_agent_experts/orchestrator-delta-12-to-13.md), [13 → 14](06_building_agentic_layers/orchestrator-delta-13-to-14.md) (generated; CI fails if stale).

## Also in this repo

| Folder | Contents |
|---|---|
| [`transcripts_summary/`](transcripts_summary/) | Timestamped summaries of lessons 9 and 10; code-derived summaries of 11–14 with the gaps found in each |
| [`playbooks/`](playbooks/README.md) | [Software](playbooks/software.md) · [Quant trading](playbooks/trading.md) · [Cybersecurity](playbooks/cybersecurity.md) · [Systems automation](playbooks/systems_automation.md) |
| [`cheat_sheets/`](cheat_sheets/) | [BLUF reference](cheat_sheets/bluf_reference.md) · [Claude Code commands](cheat_sheets/claude_code_commands.md) · [Model aliases](cheat_sheets/model_aliases.md) |
| [`02_agentic_prompt_engineering/templates/`](02_agentic_prompt_engineering/templates/) | Copy-paste templates for prompt levels 1–7 |
| [`05_agent_experts/expertise-file-template.yaml`](05_agent_experts/expertise-file-template.yaml) | Starter expertise file |
| [`06_building_agentic_layers/adw-layers.md`](06_building_agentic_layers/adw-layers.md) | Hardened ADW skeleton |
| [`labs/`](labs/) | `check_lab.py`, starters and reference solutions for labs 1–6 |
| [`scripts/`](scripts/) | [`check.sh`](scripts/check.sh) (the whole offline CI run) and [`orchestrator_deltas.py`](scripts/orchestrator_deltas.py) |

## Quick start: the first hour

1. **Measure.** Start a fresh Claude Code session in your project and run `/context`. Note boot tokens ([pillar 1, #1](01_elite_context_engineering/README.md#1-measure-to-manage)).
2. **Reduce.** Remove the default `.mcp.json`; cut `CLAUDE.md` to universals; copy [`prime.md`](9.%20elite-context-engineering/.claude/commands/prime.md) into `.claude/commands/`. Check yourself with [lab 1](01_elite_context_engineering/lab.md).
3. **Plan and build in separate agents.** Copy [`quick-plan.md`](10.%20agentic-prompt-engineering/.claude/commands/quick-plan.md) and [`build.md`](10.%20agentic-prompt-engineering/.claude/commands/build.md). Run `/quick-plan "<task>"`, then `/build specs/<plan>.md` in a **new** session.
4. **Template your next prompt.** Use the [level-2 template](02_agentic_prompt_engineering/templates/level-2-workflow.md) for whatever you did three times this week.
5. **Pick a playbook** for your domain and follow its layer table until you reach the layer your blast radius justifies. Before anything runs unattended, add a budget ([11](11_cost_governance/README.md)) and an eval ([07](07_agent_evals/README.md)).

## Running the lesson apps

Prerequisites: the Claude Code CLI, [`uv`](https://docs.astral.sh/uv/), Node 20+ (or `bun`), and PostgreSQL 14+ for lessons 12–14.

Each lesson folder is self-contained, with its own `README.md`, `.env.sample` and `.claude/`. Copy `.env.sample` to `.env`, add `ANTHROPIC_API_KEY`, and follow that lesson's README. Open Claude Code **inside a lesson folder** so its `.claude/commands`, hooks and skills load; the hooks run through `uv run --script`, so `uv` must be on your `PATH`.

```bash
# lessons 12–14: database, then backend and frontend
docker run -d --name orch-pg -p 5432:5432 -e POSTGRES_PASSWORD=dev postgres:16
cd "14.orchestrator-agent-with-adws-singularity" && cp .env.sample .env    # set ANTHROPIC_API_KEY and DATABASE_URL
(cd apps/orchestrator_db && uv run run_migrations.py)                      # stops on the first SQL error
(cd apps/orchestrator_3_stream && ./start_be.sh) & (cd apps/orchestrator_3_stream && ./start_fe.sh)

# an ADW from the CLI, with a budget
uv run adws/adw_triggers/adw_manual_trigger.py demo plan_build_review_fix "<prompt>" "$PWD/apps/<target>" --max-budget-usd 10
```

## Checks and CI

```bash
scripts/check.sh
```

One script, run by [CI](.github/workflows/ci.yml) on every push and pull request, with API keys unset and no database. It parses every tracked Python file; runs the offline test suites of the lesson apps, the ADW layer and the orchestrator database scripts; type-checks the TypeScript SDK code; runs the repo-level tests (hook wiring, guard hooks, labs, modules 07–11, repo hygiene); checks that the orchestrator delta docs and every expertise file still match the code; and fails if any test changed the working tree. Tests that need a live database, an API key or a running server are listed at the top of the script.

## Conventions

- **Models:** aliases only (`opus`, `sonnet`, `haiku`). Raw-API scripts resolve the newest ID at runtime; pin with `ANTHROPIC_MODEL_<FAMILY>` ([details](cheat_sheets/model_aliases.md)). A hygiene test fails on any versioned model ID.
- **Least privilege by default.** No `bypassPermissions` anywhere in Python (a CI lint enforces it). Agents that read untrusted text get no tools.
- **Lockfiles everywhere.** Every `package.json` and `pyproject.toml` has a committed lockfile; a test enforces it.
- **Transcripts** (`9. …mp4.txt`, `10. …mp4.txt`) are verbatim source material and are never edited.
- **Blast radius decides the gate.** Low-risk work ships on an agent verdict. Anything touching money, production or data gets a deterministic check plus a human.
