# 11 · Cost Governance: Caps, Breakers and Routing

> **BLUF:** The lessons **track** cost everywhere (`ResultMessage.total_cost_usd`, `agents.total_cost`, `orchestrator_agents.total_cost`) and **cap** it nowhere. Put a cap at every layer: per call with `max_turns` and `max_budget_usd`, then per agent, per workflow (ADW) and per day with a hierarchical ledger. Add a circuit breaker for runaway loops. On a trip, stop new work first, then decide about running work, then alert. The biggest lever is not the cap. It is **routing each role to the cheapest model that does the job** (haiku for scouts and summaries, sonnet for builders, opus for planning and review).

**Code:** [`budget.py`](budget.py) (ledger, breaker, per-call caps) · [`dashboard.sql`](dashboard.sql) · [`cost_report.py`](cost_report.py) · tests in [`tests/test_cost_governance.py`](../tests/test_cost_governance.py).

**Where cost is recorded today:** the orchestrator schema in [`14.orchestrator-agent-with-adws-singularity/apps/orchestrator_db/migrations/`](../14.orchestrator-agent-with-adws-singularity/apps/orchestrator_db/migrations/) (`agents.total_cost`, `agents.adw_id`, `agents.adw_step`, `orchestrator_agents.total_cost`, `ai_developer_workflows`). Pillar 6 lists "no `max_turns`, token or dollar cap on ADW steps" as a hardening gap ([checklist](../06_building_agentic_layers/README.md#hardening-checklist-before-you-trust-an-adw-unattended)). This pillar closes it.

---

## Budget layers

| Layer | Enforced by | Typical cap | What a trip means |
|---|---|---|---|
| **Per call** | SDK: `ClaudeAgentOptions(max_turns=..., max_budget_usd=...)` | 10 to 30 turns, a few dollars | The call ends with result subtype `error_max_turns` or `error_max_budget_usd` |
| **Per agent** | Ledger scope `agent:<name>` | Sized to the role | The agent takes no more commands |
| **Per workflow (ADW)** | Ledger scopes `adw:<id>` and `step:<name>` | Plan + build + review + fix | The ADW fails at that step with `error_step` set |
| **Per day / org** | Ledger scopes `org` and `day:<date>` | What you are willing to lose overnight | All new work stops until a human raises the cap |

**Per call.** `options_with_caps(max_turns, max_budget_usd, **kw)` returns `ClaudeAgentOptions` keyword arguments with both caps set and checked. Both fields exist in claude-agent-sdk 0.2.163 (checked against the installed package). The CLI stops *after* the budget is exceeded, so the last turn can overshoot the cap. On that error the SDK yields the `ResultMessage` and then may raise `ResultError`, a `ProcessError` subclass. Charge the result before you handle the error.

**Above the call: the ledger.** A scope path runs from widest to narrowest, such as `("org", "day:2026-11-12", "adw:123", "step:build")`. A charge counts against every prefix of the path. A limit key is an exact segment (`"adw:123"`) or a segment kind (`"adw"`, the text before the colon). The exact segment wins, and a prefix with no key is unlimited.

```python
from budget import BudgetLedger, BudgetExceeded, charge_result, options_with_caps

ledger = BudgetLedger({"org": 200, "day": 50, "adw": 5, "step": 2})
path = ("org", f"day:{date.today()}", f"adw:{adw_id}", "step:build")

if ledger.would_exceed(path, estimate=0.50):
    fail_step("budget")                                   # pre-flight: don't start what you can't finish
options = ClaudeAgentOptions(**options_with_caps(20, min(2.0, ledger.remaining(path)), model="sonnet"))
result = await query_to_completion(prompt, options)
charge_result(ledger, path, result)                       # raises BudgetExceeded after recording if a scope is now over
```

| Ledger rule | Why |
|---|---|
| Limits are **inclusive**: spending exactly the limit is allowed, one cent more is refused | The boundary is defined and tested. Amounts are kept as `Decimal`, so `0.1 + 0.2` reaches a `0.3` limit exactly |
| `charge(path, usd)` is for money **about to be spent**. If it would push any scope over, it raises and records nothing | Concurrent workers can never jointly overspend: 50 threads charging against a $10 limit stop at $9.94 |
| `charge(path, usd, already_spent=True)` is for money **already gone**. It always records, then raises | The ledger must match reality. The overshoot closes the scope, so `remaining()` is 0 and `would_exceed()` is true |
| One lock guards all state and no method awaits | One ledger can be shared by threads and asyncio tasks |
| `remaining(path)` is the headroom of the tightest scope | Feed it straight into `max_budget_usd` so one call cannot spend another step's money |

The ledger lives in process memory. A per-day cap that must survive restarts should be seeded at startup from the `daily_spend` query below.

---

## Circuit breakers

Budgets cap totals. Breakers catch the pattern that burns money fast: a loop of failures, or a burst of spend.

```python
breaker = CircuitBreaker(max_consecutive_failures=3, max_spend_per_minute=2.0, cooldown_seconds=60)
if not breaker.allow():
    raise RuntimeError(f"breaker open: {breaker.reason}")
result = await query_to_completion(prompt, options)
breaker.record(success=not result.is_error, usd_spent=result.total_cost_usd or 0)
```

| State | `allow()` | Leaves the state when |
|---|---|---|
| closed | always true | N consecutive failures, or spend in the last 60 s above the rate → open |
| open | false | `cooldown_seconds` pass → half-open |
| half-open | true for **one** trial call only | Trial succeeds → closed. Trial fails → open for another cooldown |

`breaker.reason` says why it tripped ("3 consecutive failures", "spent $5.01 in the last minute (limit $5)"). The clock is injectable, so tests use a fake clock instead of sleeping.

## What to do on a trip

1. **Stop new work.** Refuse `create_agent`, `command_agent` and `start_adw` while the ledger scope is closed or the breaker is open. This is the only step that must be automatic.
2. **Decide about running work.** A step within its own `max_budget_usd` can finish; it is already capped. A runaway (spend-rate trip) gets `interrupt_agent` (`client.interrupt()`), the tool the orchestrator already has ([pillar 4](../04_multi_agent_orchestration/README.md)).
3. **Record and alert.** Write the trip to `ai_developer_workflows.error_step` / `error_message` and `system_logs`, and send one alert with the scope, the spend and the reason. Raising a cap is a human decision.

---

## The biggest lever: model routing by role

A cap limits damage. Routing lowers the bill on every call. Route by what the role needs, not by habit.

| Role | Model | Why |
|---|---|---|
| Event summaries, classification, scouts that read and report | `haiku` | High volume, low judgment. The orchestrator's summarizer already uses it ([pillar 4](../04_multi_agent_orchestration/README.md)) |
| Builders following a written plan | `sonnet` | The plan carries the judgment; the builder executes |
| Planning, review, anything that gates a merge | `opus` | Mistakes here cost more than the tokens |

Set the model per agent template (`.claude/agents/*.md` frontmatter) and per ADW step, and let the dashboard tell you which role spends the most.

## Context levers

Spend is tokens. The context techniques in [pillar 1](../01_elite_context_engineering/README.md) are cost techniques too:

- **Prompt caching.** Keep the stable part of the prompt (system prompt, tool definitions, primed docs) first and unchanged between calls. Cached input is billed at a fraction of the base input price.
- **Output styles.** Output tokens cost several times more than input tokens. A terse output style for out-of-loop agents ([pillar 1, technique 4](../01_elite_context_engineering/README.md#4-control-output-tokens-reduce)) cuts the chatter.
- **Reset and prime, one agent per purpose.** A long-lived agent re-sends its whole history every turn. Short, focused agents keep the per-turn input small.

---

## Dashboard

[`dashboard.sql`](dashboard.sql) holds six named queries against the orchestrator schema. [`cost_report.py`](cost_report.py) runs them with `psql` in a read-only transaction and prints markdown tables.

```bash
DATABASE_URL=postgres://... 11_cost_governance/cost_report.py              # every section
DATABASE_URL=postgres://... 11_cost_governance/cost_report.py top_adws     # one section
11_cost_governance/cost_report.py --list                                   # section names
```

| Section | Answers |
|---|---|
| `spend_by_agent` | Which agents cost the most, with model, ADW and step |
| `spend_by_orchestrator` | Orchestrator's own cost plus its fleet's |
| `spend_by_adw_step` | Which step of which ADW spends the money |
| `top_adws` | The 10 most expensive ADWs |
| `daily_spend` | Spend per day for the last 30 days |
| `cost_by_adw_outcome` | Total and average cost of completed vs failed ADWs |

Costs are cumulative per row and there is no per-event cost table, so `daily_spend` attributes an agent's whole cost to the day it was created. The test suite parses the `CREATE TABLE` statements in the migrations and fails if a query names a column that does not exist. The queries were also run against Postgres 16 with the lesson 14 migrations applied and seed rows inserted.

---

## Domain adaptation

| Domain | Scope path | Hard caps | Breaker trigger |
|---|---|---|---|
| Quant trading | `org / day / sweep:<id> / backtest:<symbol>` | Per-sweep cap so a parameter grid cannot fan out unbounded | Consecutive data-load failures (a broken feed burns retries) |
| Cybersecurity | `org / day / incident:<id> / source:<log>` | Per-incident cap; enrichment calls capped separately from analysis | Spend rate during an alert storm |
| Systems automation | `org / day / change:<id> / env:<name>` | Per-change cap; drift checks on haiku | Consecutive `plan` failures in one environment |
| Software | `org / day / adw:<id> / step:<name>` | Per-ADW and per-step caps; review and fix share the ADW cap | Consecutive failed builds in a review-fix loop |

**Next:** [pillar 9: sandboxing](../09_sandboxing/README.md) · [pillar 6: ADWs](../06_building_agentic_layers/README.md)
