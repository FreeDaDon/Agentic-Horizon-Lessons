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
├── adw_modules/     adw_agent_sdk.py (typed SDK wrapper) · adw_database.py · adw_logging.py
│                    adw_websockets.py · adw_summarizer.py (haiku one-line event summaries)
├── adw_workflows/   adw_plan_build.py · adw_plan_build_review.py · adw_plan_build_review_fix.py
└── adw_triggers/    adw_scripts.py (detached `uv run … --adw-id`) · adw_manual_trigger.py (CLI)
```

**Every step is a slash command with a fixed output location**, and that is what lets deterministic code chain them:

| Step | Command | Output | Tools (least privilege) | Model |
|---|---|---|---|---|
| Plan | `/plan "<prompt>"` | `specs/<kebab-name>.md` | full set | default: opus |
| Build | `/build <plan_path>` | code changes | full set | default: opus |
| Review | `/review "<prompt>" <plan_path>` | `app_review/review_<ts>.md` with **PASS/FAIL** | no `Edit`: *"You are NOT building anything."* | opus |
| Fix | `/fix "<prompt>" <plan> <review>` (**only on FAIL**) | `app_fix_reports/fix_<ts>.md` | no web tools | opus |

**The ADW step lifecycle** (same for every step): create an agent row, log step start, set the ADW `current_step`, run `query_to_completion(prompt="/<step> …")` with logging hooks, write session/tokens/cost back, log step end. Details and copyable skeleton: [adw-layers.md](adw-layers.md).

**The database is the contract.** The trigger passes **only `--adw-id`**. The workflow loads prompt, working directory and models from `ai_developer_workflows.input_data` and writes `status`, `current_step`, `completed_steps`, `duration_seconds`, `error_step` and `error_message` back.

**Orchestrator integration (stage 9).** The orchestrator's system prompt includes a "Use ADW vs Direct Agents" table: complex or hands-off work goes to `start_adw`, interactive work goes to `command_agent`. After launch, *"your role is to observe, not control"* and *"monitor sparingly."* New workflows are discovered by globbing `adw_workflows/adw_*.py`, so **adding a file adds a capability**.

---

## Review → fix loop

- **Review report:** header (plan reference, git diff summary, **Verdict ⚠️ FAIL / ✅ PASS**) → executive summary → quick-reference table → issues by tier 🚨 BLOCKER / ⚠️ HIGH / ⚡ MEDIUM / 💡 LOW (location, offending code, 1–3 ranked fixes) → plan-compliance check against acceptance criteria and validation commands → final verdict (*FAIL if any blocker*).
- **Fix report:** status ✅ ALL FIXED / ⚠️ PARTIAL / ❌ BLOCKED → fixes by tier with before and after → skipped issues → validation-command results → files changed.
- Real example: [`review_2025-12-24T121500.md`](../14.orchestrator-agent-with-adws-singularity/app_review/review_2025-12-24T121500.md) flagged an XSS blocker (`v-html` without sanitizing). [`fix_2025-12-24T122000.md`](../14.orchestrator-agent-with-adws-singularity/app_fix_reports/fix_2025-12-24T122000.md) added DOMPurify and cut the bundle from 1,048 KB to 200 KB.

## Hardening checklist before you trust an ADW unattended

These are real gaps found in the lesson code. Fix them before running ADWs against anything that matters.

| Gap in the lesson code | Harden to |
|---|---|
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
