# Lab 5 · Seed an Expert That Survives the Drift Check

> **Goal:** write an expertise file for a small domain whose every claim about the code is checkable, and make it pass the [drift checker](../08_expertise_drift/README.md).

**Pillar:** [05 Agent Experts](README.md) · **Time:** 30 minutes · **Cost:** none

## Start
```bash
cp -r labs/starters/lab5 /tmp/lab5
labs/check_lab.py 5 /tmp/lab5/.claude/commands/experts/billing/expertise.yaml   # fails: the file it names does not exist
```

## Steps
1. Read `/tmp/lab5/src/billing.py`. That is the source of truth.
2. Rewrite `expertise.yaml` with `overview` and `core_implementation`. Pin `file:`, the total `lines:`, and one key per function or class with its `lines: "a-b"` ([anatomy](README.md#expertiseyaml)).
3. Name keys after real symbols. Add `known_issues` for anything a planner should not trip over.
4. Edit `billing.py` (add a function above `total_cents`), run the check again, and repair the drift with `08_expertise_drift/check_expertise.py --fix <path>`.

## Check
```bash
labs/check_lab.py 5 /tmp/lab5/.claude/commands/experts/billing/expertise.yaml
```

Reference solution: [`labs/solutions/lab5/`](../labs/solutions/lab5/).

## Stretch
Add `question.md` and `self-improve.md` from [the templates](self-improve-loop.md) and run `/experts:billing:self-improve true` after a change. Compare what the model fixed with what `--fix` fixed.
