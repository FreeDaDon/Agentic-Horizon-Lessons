---
description: Backtest a strategy over a parameter grid and report a metrics table
argument-hint: [strategy-name] [start-date] [end-date]
allowed-tools: Read, Bash(uv run *), Write
model: sonnet
---

# Backtest

Run a walk-forward backtest of `STRATEGY` over a parameter grid and report the results.

## Variables

STRATEGY: $1
START_DATE: $2
END_DATE: $3
RESULTS_DIR: research/backtests/

## Workflow

1. If `STRATEGY`, `START_DATE` or `END_DATE` is missing, STOP and ask the user for it.
2. Read `strategies/STRATEGY.py` and its `PARAM_GRID`. If the file does not exist, STOP and report the strategies that do exist.
3. If the date range is shorter than two years, STOP and explain that the result would not be meaningful.
4. Run the grid following the `param-loop` below.
<param-loop>
- Run `uv run backtest.py STRATEGY --params <params> --start START_DATE --end END_DATE --json`.
- Save the JSON to `RESULTS_DIR/STRATEGY/<params>.json`.
- If the run fails, record the error and continue with the next parameter set.
</param-loop>
5. Count every parameter set you tried. The overfitting check needs the trial count.

## Report

A markdown table with one row per parameter set: params, Sharpe, max drawdown, trades, and status. End with the number of trials and the path of the results folder.
