# Lab 6 · Compose a Gated ADW

> **Goal:** replace a script that shells out to Claude Code twice with a real ADW: a short declarative list of steps that runs on the shared step runner, so every step gets least-privilege permissions, turn and dollar caps, a database row, and a review gate that can fail the run.

**Pillar:** [06 Building Agentic Layers](README.md) · **Time:** 30 minutes · **Cost:** none to pass the check; one ADW run costs what its caps allow (defaults sum to at most $20)

## Start
```bash
cp labs/starters/lab6/adw_plan_build_gated.py /tmp/adw_plan_build_gated.py
```
The starter skips every permission prompt, guesses the plan path, has no budget, and never reviews. Nothing records what happened.

## Steps
1. Read one of lesson 14's workflows, for example [`adw_plan_build_review.py`](../14.orchestrator-agent-with-adws-singularity/adws/adw_workflows/adw_plan_build_review.py). Each is about 20 lines because [`adw_steps.py`](../14.orchestrator-agent-with-adws-singularity/adws/adw_modules/adw_steps.py) owns the step lifecycle.
2. Pin every dependency in the PEP 723 header with `==`, matching the other workflows.
3. Import your steps from `adw_modules.adw_steps` and list them in `STEPS`: plan first, then build, then a review gate (`review_must_pass` fails the ADW on a FAIL verdict; `review_until_pass` adds bounded fix rounds).
4. Set `TOTAL_STEPS` and hand both to `run_cli` under `if __name__ == "__main__":`.
5. Note what you did not write: plan and review paths come back through the `submit_plan` and `submit_review` tools, not "newest file"; caps come from `input_data` (`max_budget_usd`, `step_caps`, `max_fix_rounds`).

## Check
```bash
labs/check_lab.py 6 /tmp/adw_plan_build_gated.py
```

Reference solution: [`labs/solutions/lab6/adw_plan_build_gated.py`](../labs/solutions/lab6/adw_plan_build_gated.py).

## Run it for real (optional)
Copy the file into `14.orchestrator-agent-with-adws-singularity/adws/adw_workflows/`. The orchestrator discovers it by glob, so `start_adw` accepts `plan_build_gated` with no other change. Launch from the CLI with a tight budget. The run checks `spent + next step's cap` before each step, so the total must cover the largest step cap (build defaults to $8):

```bash
cd 14.orchestrator-agent-with-adws-singularity
uv run adws/adw_triggers/adw_manual_trigger.py demo plan_build_gated "<prompt>" "$PWD/apps/<target>" --max-budget-usd 12
tail -f agents/adw/<adw-id>/run.log
```

## Stretch
Score your workflow with the [eval harness](../07_agent_evals/README.md): run it on the review task and compare its verdicts with the hidden tests.
