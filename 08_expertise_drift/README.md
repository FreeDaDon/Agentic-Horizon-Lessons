# 08 · Expertise Drift — Keeping Agent Memory Honest

> **BLUF:** An expertise file ([pillar 5](../05_agent_experts/README.md)) is only useful while its claims about the code are true. Self-improve prompts repair it with a model, but nothing tells you *when* it has gone stale. [`check_expertise.py`](check_expertise.py) does, deterministically: every file path must exist, every named function must live where the file says, and every line count must be close. It runs in CI with no key and no model, and `--fix` repairs the purely numeric claims so the model only has to handle meaning.

**Why this module exists.** The first review of this repo found the lesson 13 and 14 websocket experts claiming `websocket_manager.py` had 260 lines (it had 308), store actions at lines 316-418 (they were at 700-791), and a `websocket_counter` symbol that never existed. The ADW expert missed four modules added after it was written. All of it would have been caught the day the code moved.

---

## What the checker verifies

| Finding | Meaning | Repair |
|---|---|---|
| `missing-file` | A `file:` value, or any path-like string, resolves to nothing under the project | Model: the file was renamed or deleted. Run `self-improve` |
| `missing-symbol` | A key with `lines: "a-b"` under a `file:` names a def, class, interface or const that the file doesn't define | Model: rename the key to the real symbol, or drop it |
| `moved-symbol` | The symbol exists but starts outside `a-b` (beyond `--tolerance`, default 15 lines) | `--fix` rewrites the range when the symbol has one definition |
| `line-count` | `lines: <int>` beside `file:` is off by more than `--count-tolerance` (default 15%) | `--fix` rewrites the count |

Paths resolve against the project that owns the `.claude/` folder, the lesson root above it, and each `apps/*` folder, which matches how the lesson experts write paths. A bare filename such as `main.py` passes if any file of that name exists.

The checker reads the shape the lesson experts converged on. It needs no schema:

```yaml
core_implementation:
  websocket_manager:
    file: "apps/orchestrator_3_stream/backend/modules/websocket_manager.py"
    lines: 308              # total line count, checked against the file
    broadcast:              # key = symbol name
      lines: "99-131"       # where it is defined, checked against the source
```

## Usage

```bash
08_expertise_drift/check_expertise.py                  # every tracked expertise.yaml
08_expertise_drift/check_expertise.py path/to/expertise.yaml --json
08_expertise_drift/check_expertise.py --fix            # repair numeric drift, then re-check
```

Exit status is 0 when clean, 1 when drift is found, and 2 when a file can't be parsed. `scripts/check.sh` runs it on every push, so a pull request that moves code under an expert fails until the expertise is updated.

## Where it sits in the loop

```
code change ──▶ CI: check_expertise.py ──▶ drift? ──▶ --fix (numbers) ──▶ still drift? ──▶ /experts:<domain>:self-improve true
                                              │
                                              └── clean ──▶ merge
```

Division of labor: **deterministic code checks facts; the model maintains meaning.** That is the same rule pillar 5 draws for runtime experts ("do the learning deterministically in code wherever the signal is structured"), applied to the expertise files themselves.

## Writing expertise the checker can verify

| Do | Don't |
|---|---|
| Name keys after the real symbol (`websocketEventCount`) | Invent labels (`websocket_counter`) for things the code calls something else |
| Put `file:` on the block that owns the symbols | Repeat the same path on every method |
| Use `lines: "a-b"` for definitions and `lines: N` for file totals | Mix prose into `lines:` (`"76-179 (file total: 194 lines)"`) |
| Keep behavioral claims short and testable ("broadcast snapshots the connection list") | Claim properties nobody checked ("safe for concurrent calls") |

## Domain adaptation

| Domain | Expert | What the checker protects |
|---|---|---|
| Software | `database`, `websocket`, `adw` | Function locations after refactors |
| Quant trading | `strategy` | Signal functions and risk-limit config paths the expert tells planners to read |
| Cybersecurity | `detections` | Rule files and parser functions referenced by triage prompts |
| Systems automation | `infra` | Module paths and variable files after a Terraform restructure |

**Tests:** [`tests/test_expertise_drift.py`](../tests/test_expertise_drift.py). **Next:** [pillar 5](../05_agent_experts/README.md) · [self-improve loop](../05_agent_experts/self-improve-loop.md)
