# Playbook — Systems Automation (IaC, Ops, CI/CD)

> **BLUF:** Let agents write and review infrastructure changes and read plans. Never let them apply to production unattended. The deterministic gate is the plan itself: any destroy or replace in prod needs explicit human approval. Filter `plan`/`kubectl` output before the agent reads it; those dumps are the biggest context bloat in this domain.

## Layer by layer

| Layer | Do this |
|---|---|
| Context | `/prime_infra` reads the module map (context map section), the target env's `tfvars`, and the CI deploy workflow. Pipe `terraform show -json plan \| jq` summaries into context, never raw plans. |
| Prompts | `/drift_check <env>` (L3: loop per module; STOP on auth errors). `/iac_change <request>` → `specs/infra/<name>.md` with rollback steps and validation commands. |
| SDK agent | `drift_inspector`: preset + append system prompt; tools `run_plan(env)` (read-only wrapper) and `submit_drift_report`. A `PreToolUse` Bash hook denies `apply`, `destroy`, `delete`, `kubectl … --force`, and any command with prod credentials. |
| Fleet | One `drift-scout` per environment in parallel (`/background` or `create_agent`) → `iac-builder` (serialized) → `plan-reviewer` (opus). |
| Expert | `experts/infra/expertise.yaml`: module map, env differences, apply-order constraints, past failed applies with causes. Self-improve after every apply, failed or successful. |
| ADW | `plan_apply_verify`: plan change → write IaC → `terraform plan` (deterministic) → review (**a destroy in prod is a BLOCKER**) → **human approval** → apply (CI job, not the agent) → verify (smoke checks) → self-improve. |

## Hard rules
1. The apply runs in CI with scoped credentials, triggered after approval. Agents never hold prod credentials.
2. Every change spec includes rollback steps; the reviewer fails specs without them.
3. Background agents run in containers with no cloud credentials beyond read-only plan roles.
4. Budget every unattended run (`max_turns`, dollar cap) and alert on stalled heartbeats.

## Metrics
Change failure rate · drift detected vs remediated · human approval latency · cost per change.
