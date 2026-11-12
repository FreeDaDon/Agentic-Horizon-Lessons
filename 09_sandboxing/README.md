# 09 · Sandboxing and Blast Radius: Where an Agent Can Reach

> **BLUF:** Every lesson runs its agents directly on your host checkout, with your shell, your network and your credentials. Sandboxing shrinks what one bad tool call can touch. Climb the **isolation ladder** only as far as the blast radius demands: tool allowlists, then a path-confinement hook, then **one git worktree per agent**, then a **no-network container with a read-only base**, then a separate VM or account for anything that touches money or production. The cheapest rung with the biggest payoff is the worktree. It stops concurrent agents from writing the same files and turns every agent's output into a branch you review like a PR.

**Code:** [`worktree_sandbox.py`](worktree_sandbox.py) (worktrees, the confinement hook, the docker argv) · tests in [`tests/test_sandboxing.py`](../tests/test_sandboxing.py).

**Lesson hooks this builds on:** the orchestrator schema already has an unused `agents.git_worktree` column ([`1_agents.sql`](../14.orchestrator-agent-with-adws-singularity/apps/orchestrator_db/migrations/1_agents.sql)), and lesson 11 app 7 confines the planner's and reviewer's writes with a PreToolUse hook ([`agent_orchestrator.py`](../11.%20building-specialized-agents/apps/custom_7_micro_sdlc_agent/backend/modules/agent_orchestrator.py), `is_inside_directory`).

---

## The isolation ladder

Each rung adds to the one below it. None replaces the one below.

| # | Rung | Mechanism | Stops | Does not stop |
|---|---|---|---|---|
| 1 | **Permission mode and tool allowlist** | `ClaudeAgentOptions(allowed_tools=[...], disallowed_tools=[...], permission_mode=...)` | Tools the role never needs (a reviewer with no `Edit`, a scout with no `Bash`) | Anything an allowed tool can do. `Bash` alone can do almost anything |
| 2 | **Path-confinement hook** | `confine_paths_hook(root)` as a PreToolUse hook | File tools reading or writing outside `root`, including `..` and symlink escapes. Obvious `cd ..` and absolute paths in Bash | Bash that hides the path (`$HOME`, `$(...)`, `eval`, a script that opens files itself). It is a heuristic |
| 3 | **Git worktree per agent** | `create_worktree(repo, "builder-1")`, then `cwd=wt.path` | Two agents editing the same file. Half-finished work landing on your branch. Untracked secrets such as `.env` (a worktree only has tracked files) | Anything outside the repo. The agent still runs as you, with your network |
| 4 | **Container, no network, read-only base** | `docker_command(wt, image, cmd)` | Exfiltration, package-install side effects, writes outside `/work` and `/tmp`, reads of your home directory | Bad code inside `/work`. Kernel escapes (rare, but a container is not a VM) |
| 5 | **Separate VM or cloud account** | A throwaway VM, a sandbox cloud account, scoped short-lived credentials | Anything touching money, production data or real infrastructure | Nothing on this list. This is the line for irreversible actions |

**How to pick.** Rungs 1 to 3 cost almost nothing and suit every unattended agent. Rung 4 is for running code the agent wrote or fetched: tests, builds, scrapers, samples. Rung 5 is mandatory for broker keys, production databases and `terraform apply`.

---

## Rung 2: the confinement hook

```python
from claude_agent_sdk import ClaudeAgentOptions, HookMatcher
from worktree_sandbox import confine_paths_hook, create_worktree

wt = create_worktree(repo, "builder-1")
options = ClaudeAgentOptions(
    cwd=str(wt.path),
    hooks={"PreToolUse": [HookMatcher(hooks=[confine_paths_hook(wt.path)])]},
)
```

- `Read`, `Write`, `Edit`, `MultiEdit`, `NotebookEdit`, `Glob` and `Grep` paths are joined to the root and passed through `Path.resolve()`. That follows `..` and symlinks, so `src/../../x` and a symlink inside the root that points out are both denied.
- `Bash` is tokenized with `shlex`. Every path-like token (anything with a `/`, or starting with `~` or `..`) is resolved the same way. A bare `cd` is denied because it goes to your home directory. `/dev/null` and the standard streams are allowed.
- **It is a heuristic.** It cannot see paths built at runtime. If commands are untrusted, run them in rung 4.
- A denial returns the same `permissionDecision: "deny"` shape that lesson 11 uses, so the model sees the reason and can correct itself.

---

## Rung 3: one worktree per agent

```bash
09_sandboxing/worktree_sandbox.py create builder-1        # prints <repo>/.worktrees/builder-1, branch agent/builder-1
09_sandboxing/worktree_sandbox.py list
09_sandboxing/worktree_sandbox.py remove builder-1 --delete-branch
```

| Property | Behavior |
|---|---|
| Layout | Path `<repo>/.worktrees/<slug>`, branch `agent/<slug>`, created from `--base` (default `HEAD`) |
| Slug | Must match `[a-z0-9][a-z0-9-]{0,62}`. Rejects `../x`, `a/b`, `-rf` and uppercase, so a name can never become a path or a git flag |
| Idempotent | `create` twice returns the same worktree. If the branch exists without a worktree, it is checked out again with its commits |
| Main checkout | `/.worktrees/` is added to `.git/info/exclude`, so the main checkout's `git status` stays clean |
| Remove | Refuses when the worktree has uncommitted changes. `--delete-branch` runs `git branch -D`, which drops unmerged commits |

**Wiring it into the orchestrator.** `AgentManager.create_agent` in [`agent_manager.py`](../14.orchestrator-agent-with-adws-singularity/apps/orchestrator_3_stream/backend/modules/agent_manager.py) passes `working_dir=self.working_dir` to the database and `cwd=self.working_dir` to the SDK. Give each agent its own worktree instead and record it in the column that already exists:

```python
wt = create_worktree(self.working_dir, name)
agent_id = await create_agent(..., working_dir=str(wt.path), metadata=metadata)
async with get_connection() as conn:
    await conn.execute("UPDATE agents SET git_worktree = $1 WHERE id = $2", str(wt.path), agent_id)

hooks_dict = self._build_hooks_for_agent(agent_id, name, task_slug, entry_counter)
hooks_dict["PreToolUse"].insert(0, HookMatcher(hooks=[confine_paths_hook(wt.path)]))
options = ClaudeAgentOptions(cwd=str(wt.path), hooks=hooks_dict, ...)
```

Do the same in `command_agent`, which rebuilds `hooks_dict` on every command. The cleaner long-term change is a `git_worktree` parameter on `database.create_agent` so the row is written once.

`command_agent` already uses `cwd=agent.working_dir`, so every later command resumes inside the same worktree. ADW steps take their working directory from `ai_developer_workflows.input_data`, so an ADW gets one worktree for all of its steps: plan, build, review and fix see each other's work, and parallel ADWs never collide.

**Merge back like a PR.** The agent commits on `agent/<slug>`. You (or a review agent) read the diff, then:

```bash
git -C .worktrees/builder-1 push -u origin agent/builder-1 && gh pr create --head agent/builder-1   # remote review
git merge --no-ff agent/builder-1                                                                   # or merge locally after review
```

**Clean up.** Remove the worktree when the agent is deleted (`delete_agent`) or the ADW finishes. After a crash, `list` shows what is still registered and `git worktree prune` drops entries whose directories are gone. A worktree has only tracked files, so install dependencies inside it (`uv sync`, `bun install`) before running tests.

---

## Rung 4: a container with no network

```bash
docker run --rm --network none --read-only --tmpfs /tmp \
  --cap-drop ALL --security-opt no-new-privileges --user "$(id -u):$(id -g)" \
  -v "$PWD/.worktrees/builder-1:/work" -w /work python:3.12-slim pytest -q
```

`docker_command(wt, image, cmd)` builds exactly this argv; it does not run it. The root filesystem is read-only, `/tmp` is a tmpfs, only the worktree is writable, and files written to `/work` belong to your user. Verified on this host: inside the container a write to `/etc` fails, an HTTP request fails, and `/work` and `/tmp` are writable.

**Where the agent itself runs.** The agent loop needs to reach the model API, so `--network none` cannot hold the agent. The usual split: the agent runs on the host at rungs 1 to 3, and anything it wants to *execute* (tests, builds, downloaded samples) goes through `docker_command`. Running the whole agent inside a container needs an egress proxy that allows only the API host. That is a bigger project; start with the split.

**Bake dependencies into the image.** With no network, `pip install` inside the container fails by design. Build an image with the project's dependencies once, then run agent output against it.

---

## Rung 5: a separate account for real consequences

No sandbox on your laptop should hold production credentials. When an agent's job ends in a real action (an order, a deploy, a firewall change), the agent produces a **plan artifact** inside the sandbox and a human or a deterministic gate applies it outside. Credentials live only where the apply happens.

---

## Domain adaptation

| Domain | Sandbox the agent gets | Never inside the sandbox | Apply step |
|---|---|---|---|
| Quant trading | Worktree with strategy code and a frozen market-data snapshot; backtests run in a no-network container | Broker API keys, live order endpoints | A human (or a risk gate with hard limits) submits orders from a separate account |
| Cybersecurity | Detonation of samples in a `--network none` container from a disposable image; analysis output written to `/work` | Production EDR or IdP credentials | Containment actions go through the SOAR runbook with approval |
| Systems automation | Worktree for IaC changes; `terraform plan` against read-only credentials | Apply-capable credentials, state-file write access | `terraform apply` outside the sandbox, behind human approval of the saved plan |
| Software | Worktree per agent, confinement hook, tests in a container | Deploy keys, production `DATABASE_URL` | Merge via PR; CI deploys |

**Next:** [pillar 11: cost governance](../11_cost_governance/README.md) · [pillar 6: hardening checklist](../06_building_agentic_layers/README.md#hardening-checklist-before-you-trust-an-adw-unattended)
