# Playbook — Quantitative Trading

> **BLUF:** Use agents for **research, code, backtests and review**, never for execution. Order-placing capability lives outside every agent, behind a deterministic risk gate and typed human confirmation. The expert pattern is valuable here because data quirks, leakage traps and past failed hypotheses are exactly the knowledge that gets forgotten.

## Layer by layer

| Layer | Do this |
|---|---|
| Context | `/prime_strategy` reads the strategy module, signal interface, risk config and backtest entry point. **Never** loads raw OHLCV into context; a script computes stats and the agent reads the summary table. Market-data MCP servers load only for research runs (`--mcp-config .mcp.json.marketdata_Nk`). |
| Prompts | `/backtest <strategy> <range>` (L3: STOP if under 2 years of data; loop over the parameter grid; report a metrics table). `/hypothesis <idea>` → `specs/research/<name>.md` with a pre-registered success metric. |
| SDK agent | `signal_analyst`: haiku, string system prompt, tools `get_bars`, `compute_indicators`, `submit_signal(symbol, side, confidence, rationale)`; all built-ins denied; **no broker tools registered at all**. Output is a proposal record, not an order. |
| Fleet | Orchestrator fans out one `backtester` per symbol or parameter shard (`/background` or `create_agent`); `risk-reviewer` (opus) reads the results for leakage, survivorship bias and overfitting. |
| Expert | `experts/strategy/expertise.yaml`: signal definitions, data-source quirks (splits, holidays, timezone), known leakage traps, rejected hypotheses and why. Self-improve after every research cycle. |
| ADW | `research_backtest_review`: plan hypothesis → implement signal → run walk-forward backtest (deterministic script) → review → fix. Gate: pre-registered metric thresholds **and** an overfitting check (e.g. deflated Sharpe / PBO). The output is a report, never a deployment. |

## Hard rules
1. **No agent holds an order-placing tool.** The execution path is a separate service: paper mode by default, a live-mode env flag, typed per-order confirmation, and an audit log.
2. Agents run backtests via scripts that emit JSON metrics; they don't compute P&L in their heads.
3. Record every tried configuration (trial count feeds the overfitting statistics).
4. The expert's `known_issues` must list look-ahead and survivorship traps specific to your data vendor.

## Metrics
Hypotheses tested per week · share that pass the overfitting gate · paper-vs-backtest divergence · cost per research cycle.
