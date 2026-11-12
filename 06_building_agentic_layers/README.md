# 06 · Building Agentic Layers — Roadmap to Codebase Singularity

> **BLUF:** The **agentic layer** is a second layer over your codebase (prompts, agents, hooks, experts, workflows) that *builds and maintains the application layer*. *"We're building the system that builds the system… You want your agentic layer operating your code base and you operate the agentic layer."* The top of the stack is the **ADW (AI Developer Workflow)**: *"deterministic Python code orchestrates non-deterministic Claude agents."* In lesson 14 an orchestrator agent launches ADWs (plan → build → review → fix) and experts keep the layer's own knowledge current. That self-maintaining state is what the course calls the *singularity*.

**Sources:** lesson 9 transcript ("agentic layer", ADWs, one agent one purpose) and code in [`14.orchestrator-agent-with-adws-singularity/`](../14.orchestrator-agent-with-adws-singularity/README.md) ([summary](../transcripts_summary/14_adws_singularity_code_derived.md)). Lesson 14 has no transcript. "Singularity" appears only in its folder name, so the definition above is an interpretation from the artifacts, labeled as such.

> *"Raw agents are unreliable. Raw code is inflexible. Combined, they're unstoppable."* · *"One Agent, One Prompt, One Purpose."* · *"The pattern is the product."*

---

## The roadmap: 9 stages from plain code to a self-maintaining layer

Each stage adds a capability, and each is useful on its own. Stop at the stage your blast radius justifies.

| # | Stage | Capability gained | Concrete artifacts in this repo | Pillar |
|---|---|---|---|---|
| 0 | **Plain codebase** | none | `apps/pomodoro_timer/`, `apps/markdown_preview/` | n/a |
| 1 | **Memory and context** | Agents start oriented | slim `CLAUDE.md`, `ai_docs/`, `/prime*`, `/load_ai_docs`, `/load_bundle` | [1](../01_elite_context_engineering/README.md) |
| 2 | **Reusable prompts with fixed output locations** | Repeatable work; machine-findable outputs | `/plan` → `specs/`, `/build`, `/review` → `app_review/`, `/fix` → `app_fix_reports/` | [2](../02_agentic_prompt_engineering/README.md) |
| 3 | **Specialized sub-agents and skills** | Delegation with isolated context | `.claude/agents/{planner,build-agent,scout-report-suggest,playwright-validator,docs-scraper,meta-agent}.md`, `.claude/skills/` | [1](../01_elite_context_engineering/README.md), [3](../03_claude_agent_sdk_mastery/README.md) |
| 4 | **Hooks: observability and guardrails** | See and block agent actions | `.claude/settings.json` hooks, `pre_tool_use.py` (blocks `rm -rf`), `send_event.py` | [3](../03_claude_agent_sdk_mastery/README.md), [4](../04_multi_agent_orchestration/observability.md) |
| 5 | **Agent experts** | Domain memory that improves itself | `.claude/commands/experts/{database,websocket,adw}/` | [5](../05_agent_experts/README.md) |
| 6 | **Custom SDK agents** | Domain agents with their own system prompt and tools | lesson 11 apps, `adw_agent_sdk.py` typed wrapper | [3](../03_claude_agent_sdk_mastery/README.md) |
| 7 | **Orchestrator agent** | One agent that creates, commands and deletes a fleet | `apps/orchestrator_3_stream/`, `apps/orchestrator_db/` | [4](../04_multi_agent_orchestration/README.md) |
| 8 | **ADWs** | Deterministic multi-step pipelines of agents with database-backed state | `adws/adw_workflows/adw_plan_build_review_fix.py`, migration `9_ai_developer_workflows.sql`, `AdwSwimlanes.vue` | this page, [adw-layers.md](adw-layers.md) |
| 9 | **Orchestrator drives ADWs; the layer maintains itself** | Hand off whole feature cycles; the layer updates its own knowledge | `start_adw`/`check_adw` tools, `{{AVAILABLE_ADW_TYPES}}` discovery, `experts/adw/` (the ADW expert improves the ADW system), `scripts/copy_claude.py` | this page |

Stages 8 and 9 are new in lesson 14.

---

## ADW anatomy (stage 8)

```
adws/
├── adw_modules/     adw_steps.py (shared step runner: profiles, caps, submit tools, fix loop)
│                    adw_agent_sdk.py (typed SDK wrapper, no bypass mode) · adw_database.py · adw_logging.py
│                    adw_websockets.py · adw_summarizer.py (tool-less haiku event summaries)
│                    adw_plan.py · adw_review.py (plan-path validation, fail-closed verdict fallback)
├── adw_workflows/   adw_plan_build.py · adw_plan_build_review.py · adw_plan_build_review_fix.py (~20 lines each)
├── adw_triggers/    adw_scripts.py (`uv run … --adw-id` in its own process group, log file, cancel)
│                    adw_manual_trigger.py (CLI)
└── adw_tests/       offline suite: recorded SDK streams, in-memory DB sink
```

**Every step is a slash command with a fixed output location**, and that is what lets deterministic code chain them:

| Step | Command | Output | Tools (least privilege) | Model |
|---|---|---|---|---|
| Plan | `/plan "<prompt>"` | `specs/<kebab-name>.md`, returned through `submit_plan(plan_path)` | `acceptEdits` | `model` (default opus) |
| Build | `/build <plan_path>` | code changes | `acceptEdits` | `model` |
| Review | `/review "<prompt>" <plan_path>` | `submit_review(verdict, report, blocker_count)`; Python writes `app_review/review_<adw8>_r<round>.md` | `dontAsk`, read-only tools and read-only git | `review_model` |
| Fix | `/fix "<prompt>" <plan> <review>` (**only on FAIL**) | `app_fix_reports/fix_<ts>.md`, then re-review | `acceptEdits` | `fix_model` |

Default caps per step (override per ADW with `input_data.step_caps`): plan 40 turns / $3 / 30 min, build 80 / $8 / 60 min, review 40 / $3 / 30 min, fix 60 / $5 / 45 min. The run refuses to start a step whose cap would push total spend past `max_budget_usd` (default $20).

**The ADW step lifecycle** (same for every step, owned by `adw_steps.py`): check the budget, create an agent row, log step start, set the ADW `current_step`, run the slash command under the step's permission profile and caps with logging hooks, collect the submit-tool result, write session/tokens/cost back, log step end. Any exception, including before the first step, marks the row failed. Details and copyable skeleton: [adw-layers.md](adw-layers.md).

**The database is the contract.** The trigger passes **only `--adw-id`**. The workflow loads prompt, working directory and models from `ai_developer_workflows.input_data` and writes `status`, `current_step`, `completed_steps`, `duration_seconds`, `error_step` and `error_message` back.

**Orchestrator integration (stage 9).** The orchestrator's system prompt includes a "Use ADW vs Direct Agents" table: complex or hands-off work goes to `start_adw`, interactive work goes to `command_agent`. After launch, *"your role is to observe, not control"* and *"monitor sparingly."* New workflows are discovered by globbing `adw_workflows/adw_*.py`, so **adding a file adds a capability**.

---

## Review → fix loop

- **Review report:** header (plan reference, git diff summary, **Verdict ⚠️ FAIL / ✅ PASS**) → executive summary → quick-reference table → issues by tier 🚨 BLOCKER / ⚠️ HIGH / ⚡ MEDIUM / 💡 LOW (location, offending code, 1–3 ranked fixes) → plan-compliance check against acceptance criteria and validation commands → final verdict (*FAIL if any blocker*).
- **Fix report:** status ✅ ALL FIXED / ⚠️ PARTIAL / ❌ BLOCKED → fixes by tier with before and after → skipped issues → validation-command results → files changed.
- Real example: [`review_2025-12-24T121500.md`](../14.orchestrator-agent-with-adws-singularity/app_review/review_2025-12-24T121500.md) flagged an XSS blocker (`v-html` without sanitizing). [`fix_2025-12-24T122000.md`](../14.orchestrator-agent-with-adws-singularity/app_fix_reports/fix_2025-12-24T122000.md) added DOMPurify and cut the bundle from 1,048 KB to 200 KB.

## Hardening checklist: gaps found in the lesson code, and their status

Every row below was a real gap in lesson 14. All are fixed in this repo and covered by the offline suite in `adws/adw_tests/` (run by CI). Use the table as the checklist for any ADW layer you build.

| Gap in the original lesson code | Fix now in the code |
|---|---|
| Verdict parsed by substring from chat text | `/review` must call `submit_review(verdict, …)`; text parsing is a fail-closed fallback only |
| Plan and review paths chosen as the newest file by mtime (races across concurrent ADWs) | `submit_plan(plan_path)` returns the exact path; it is validated and stored in `output_data` |
| `bypass_permissions=True` accepted but never mapped to the SDK | Explicit `permission_mode` per step; the bypass mode is not representable in the type |
| No `max_turns`, dollar or time cap | Per-step `max_turns`, `max_budget_usd`, wall-clock timeout; per-ADW budget checked before each step ([module 11](../11_cost_governance/README.md)) |
| One fix pass, never re-reviewed; FAIL still reported `completed` | `review_until_pass` loops review ⇄ fix up to `max_fix_rounds`, then fails with an escalation message; `review_must_pass` fails the ADW on FAIL |
| Detached process sent stdout/stderr to `/dev/null` | `agents/adw/<adw_id>/run.log`; pid and log path stored on the row; `cancel_adw` kills the process group |
| Summarizer ran with `bypassPermissions` and no tool limit | Tool-less, one-turn summaries, at most 4 concurrent, drained before shutdown |
| Dangerous-command hook blocked only `rm`; `.env` guard commented out | Shared detector blocks destructive git, dd, mkfs, chmod -R /, curl \| sh, terraform destroy, DROP; `.env` guard on ([tests](../tests/test_guard_hooks.py)) |
| Hooks failed open: unquoted `$CLAUDE_PROJECT_DIR` in a folder name with a space, non-executable scripts | Quoted `uv run --script` commands; [`tests/test_hook_wiring.py`](../tests/test_hook_wiring.py) runs the real command strings |
| Commands and hooks load only if the target `working_dir` has `.claude/` | Still true: sync the layer into targets with `scripts/copy_claude.py`, or run targets inside a [sandbox worktree](../09_sandboxing/README.md) of this repo |

---|---|
| Verdict parsed as `"PASS" in text and "FAIL" not in text`, so "no FAIL conditions" counts as FAIL | Have `/review` write a machine-readable line (`VERDICT: PASS`) or JSON; parse only that |
| Plan and review paths chosen as the newest file by modification time, which races across concurrent ADWs | Have the step return the exact path in structured output; store it in `output_data` |
| `bypass_permissions=True` is accepted but never mapped to the SDK's `permission_mode` | Set `permission_mode` explicitly per step; keep review read-only |
| No `max_turns`, token or dollar cap on ADW steps (cost is tracked, not capped) | Set `max_turns` and a per-ADW budget; fail the step when it is exceeded |
| One fix pass, with no re-review | Loop review → fix up to N times, then escalate to a human |
| Detached process sends stdout and stderr to `/dev/null` | Log to `agents/adw/<adw_id>/` and link from the database row |
| Commands and hooks load only if the target `working_dir` has `.claude/` | Sync the agentic layer into targets (`copy_claude.py`) or pass `setting_sources` explicitly |
| Dangerous-command hook blocks only `rm`; `.env` protection commented out | Enable env-file protection; add patterns for `git push --force`, `DROP`, `terraform destroy`, and the like |

---

## Domain adaptation

| Domain | ADW | Steps | Deterministic gate |
|---|---|---|---|
| Software | `plan_build_review_fix` | as above | tests + review verdict |
| Quant trading | `research_backtest_review` | plan hypothesis → implement signal → backtest → review for leakage and overfitting → fix | walk-forward metrics thresholds; **never** a live-order step inside the ADW |
| Cybersecurity | `detect_tune_validate` | plan rule change → implement rule → replay against labeled logs → review false positives and negatives → fix | precision and recall on the replay set |
| Systems automation | `plan_apply_verify` | plan change → write IaC → `plan` → review diff (deletes are a blocker) → human approval → apply → verify | a plan with no destroys, or explicit human approval |

**Next:** [adw-layers.md](adw-layers.md) · [playbooks](../playbooks/)
