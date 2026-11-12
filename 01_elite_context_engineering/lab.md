# Lab 1 · Cut Boot Context and Prime Instead

> **Goal:** take a project whose agents boot bloated and make it boot lean: a universals-only `CLAUDE.md`, no default MCP servers, a prime command, and a terse output style for build agents.

**Pillar:** [01 Elite Context Engineering](README.md) · **Time:** 30 minutes · **Cost:** none (the check is offline)

## Start
Copy the starter into a scratch folder and look at what an agent would load every session:

```bash
cp -r labs/starters/lab1 /tmp/lab1 && cd /tmp/lab1
claude          # then run /context and note the tokens used before your first prompt
```

## Steps
1. **Reduce `CLAUDE.md`** to what every agent needs every time (about 1,500 tokens at most). Move the rest into primes. [Technique 3](README.md#3-prime-more-claudemd-less-reduce).
2. **Remove the default `.mcp.json`.** Keep a per-task file named with its cost, such as `.mcp.json.firecrawl_7k.sample`, and load it with `--mcp-config … --strict-mcp-config`. [Technique 2](README.md#2-avoid-default-mcp-servers-reduce).
3. **Write `.claude/commands/prime.md`** with `## Run`, `## Read` and `## Report` sections. Use the [priming guide](priming-guide.md).
4. **Add `.claude/settings.local.concise.json`** with an `outputStyle` for build agents. [Technique 4](README.md#4-control-output-tokens-reduce).
5. Run `/context` again and compare.

## Check
```bash
labs/check_lab.py 1 /tmp/lab1
```

Reference solution: [`labs/solutions/lab1/`](../labs/solutions/lab1/). Read it after you pass, not before.

## Stretch
Write a second, stacked prime (`prime_feature.md`) that runs `prime.md` first, then reads only one feature's folder.
