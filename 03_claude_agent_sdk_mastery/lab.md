# Lab 3 · Build a Narrow Agent That Can Only Propose

> **Goal:** build a custom Agent SDK agent with its own system prompt, exactly the tools it needs, every built-in denied, a turn cap, and a `submit_*` tool as its typed output.

**Pillar:** [03 Claude Agent SDK Mastery](README.md) · **Time:** 45 minutes · **Cost:** a few cents to run it once (the check itself is offline)

## Start
```bash
cp labs/starters/lab3/signal_analyst.py /tmp/signal_analyst.py
```
The starter can do anything Claude Code can, skips every permission prompt, and returns prose. That is the opposite of what a trading-adjacent agent should be.

## Steps
1. Replace `query()` with a `ClaudeSDKClient` and set `system_prompt` to a narrow role ([pattern 1](patterns.md#1-full-system-prompt-override--custom_1_pong_agentpong_agentpy)).
2. Add a read tool (`get_bars`) and a `submit_signal(symbol, side, confidence, rationale)` tool with `@tool` and `create_sdk_mcp_server` ([pattern 3](patterns.md#3-custom-in-process-tool--custom_2_echo_agentecho_agentpy), [pattern 7](patterns.md#7-tool-as-structured-output--custom_4_social_hype_agentmodulesagentpy)).
3. Allow only `mcp__<server>__<tool>` names and deny the built-ins, at least `Bash`, `Write` and `Edit` ([pattern 4](patterns.md#4-deny-built-ins--custom_3_calc_agentcalc_agentpy)).
4. Set `max_turns`. Remove `bypassPermissions`.
5. Read the result from the `ToolUseBlock` input, not from text.

## Check
```bash
labs/check_lab.py 3 /tmp/signal_analyst.py
uv run --script /tmp/signal_analyst.py SPY     # optional live run
```

Reference solution: [`labs/solutions/lab3/signal_analyst.py`](../labs/solutions/lab3/signal_analyst.py).

## Stretch
Add `max_budget_usd` and an inline `PreToolUse` hook that denies `submit_signal` when `confidence` is above 0.9 without a rationale over 40 characters.
