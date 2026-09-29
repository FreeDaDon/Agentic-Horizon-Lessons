# Playbook — Cybersecurity (Detection, Triage, Response)

> **BLUF:** Agents are good at the reading-heavy work: enrichment, correlation, rule drafting, report writing. Put each log source behind its own scout so raw telemetry never floods the primary context. Agents **recommend** containment; a human or a pre-approved SOAR policy **executes** it.

## Layer by layer

| Layer | Do this |
|---|---|
| Context | `/prime_ir` reads the incident runbook, asset inventory for affected hosts, and the rule under investigation. Load SIEM/EDR MCP servers only for triage sessions. Concise output style for enrichment workers. |
| Prompts | `/triage <alert_id>` (L3: STOP if the asset is not in inventory; loop per IOC; report verdict + MITRE technique + evidence). `/tune_rule <rule_id>` → `specs/detections/<rule>.md`. |
| SDK agent | `alert_triager`: tools `query_siem(q, window)` (read-only), `lookup_ioc(value)`, `submit_verdict(alert_id, severity, technique, evidence[])`. A `PostToolUse` hook redacts secrets and PII from tool output before the model sees it. |
| Fleet | IR orchestrator: one `log-scout` (haiku) per source (EDR, firewall, IdP, cloud audit) returning a timeline + IOC list → `ioc-enricher` → `report-writer` (opus). |
| Expert | `experts/detections/expertise.yaml`: rule inventory, log-source schemas, known false-positive patterns with root causes, response playbooks. Self-improve after every tuned rule and closed incident. |
| ADW | `detect_tune_validate`: plan the rule change → implement → **replay against labeled logs** (deterministic) → review false positives and negatives → fix. Gate: precision and recall on the replay set not below the current rule's. |

## Hard rules
1. Containment tools (isolate host, disable account, block IP) are **not registered** in any agent. They live in SOAR with human approval or narrowly pre-approved policies.
2. Evidence is always cited: query + time window + record IDs. The reviewer rejects claims without them.
3. Keep incident data inside your boundary: self-hosted MCP servers and redaction hooks. Don't send raw logs to third-party tools.
4. Every agent action is logged to an immutable store (the hook → DB pattern from [observability](../04_multi_agent_orchestration/observability.md)).

## Metrics
Mean time to triage · false-positive rate per rule after tuning · analyst override rate on agent verdicts · cost per incident.
