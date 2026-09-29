# Playbook — Software Development

> **BLUF:** This is the lessons' home domain, so almost everything can be copied as is. Start with `/prime` + `/quick-plan` + `/build` in separate agents, add `/review` with a machine-readable verdict, promote your riskiest module to an expert, then wrap it all in `plan_build_review_fix`.

## Layer by layer

| Layer | Do this | Copy from |
|---|---|---|
| Context | Trim `CLAUDE.md` to universals; `/prime`, `/prime_feature`, `/prime_bug`; no default `.mcp.json` | `9. elite-context-engineering/.claude/commands/prime*.md` |
| Prompts | `/quick-plan` → `specs/`; `/build <spec>`; `/review` → `app_review/`; `/fix` | `10. …/quick-plan.md`, `14. …/.claude/commands/{plan,build,review,fix}.md` |
| SDK agent | Read-only QA agent with a `.env` read block | `11. …/apps/custom_5_qa_agent/qa_agent.py` |
| Fleet | Scouts (haiku, read-only) → build-agent → review-agent | `12. …/.claude/commands/orch_*.md`, `/plan_w_scouters`, `/build_in_parallel` |
| Expert | `experts/database`, `experts/api`, `experts/auth` | `13. agent-experts/.claude/commands/experts/` |
| ADW | `plan_build_review_fix` with marker-based verdicts | [adw-layers.md](../06_building_agentic_layers/adw-layers.md) |

## Guardrails
- `PreToolUse` Bash hook: block `rm -rf`, `git push --force`, `git reset --hard origin`, and `DROP TABLE`.
- Review prompt has no `Edit`; build agent has no web tools on sensitive repos.
- Agents never merge. A human merges after review PASS + green CI.

## Metrics to track
One-shot success rate per ADW · review FAIL rate · average fix passes · cost per merged PR · tokens at agent boot (`/context`).
