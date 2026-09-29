# Model Aliases — Future-Proof Model Selection

> **BLUF:** This repo has no versioned model IDs outside the source transcripts. Anything that goes through Claude Code or the Agent SDK uses the family alias (`opus`, `sonnet`, `haiku`), which always resolves to the latest model. The raw Anthropic Messages API doesn't accept bare aliases, so those scripts look up the newest ID in a family at runtime. Nothing needs editing when a new model ships.

## Rule by call path

| Call path | What to write | Example in this repo |
|---|---|---|
| Claude Code CLI | `--model opus` | lesson 9 aliases: `claude --model sonnet` |
| Slash command / sub-agent frontmatter | `model: opus` | `10. …/.claude/commands/quick-plan.md` |
| Agent SDK (Python) | `ClaudeAgentOptions(model="haiku")` | `11. …/custom_1_pong_agent/pong_agent.py` |
| Agent SDK typed wrapper | `ModelName.OPUS` (= `"opus"`) | `14. …/adws/adw_modules/adw_agent_sdk.py` |
| App config / `.env` | `DEFAULT_MODEL = "sonnet"`, `FAST_MODEL=haiku` | `12. …/backend/modules/config.py`, `.env.sample` |
| **Raw Messages API** (`anthropic.Anthropic().messages.create`) | `model=resolve_model(client, "haiku")` | `.claude/utils/llm/anth.py`, `.claude/hooks/utils/summarizer.py` |

## The raw-API resolver (inlined in each standalone `uv` script)

```python
_MODEL_CACHE = {}


def resolve_model(client, family="haiku"):
    """Newest model ID in a family ("opus", "sonnet", "haiku").

    The Messages API needs a full model ID, so look it up instead of hardcoding a
    version. Set ANTHROPIC_MODEL_<FAMILY> (e.g. ANTHROPIC_MODEL_HAIKU) to pin one.
    """
    override = os.getenv(f"ANTHROPIC_MODEL_{family.upper()}")
    if override:
        return override
    if family not in _MODEL_CACHE:
        # models.list() returns the most recently released models first
        _MODEL_CACHE[family] = next(m.id for m in client.models.list() if family in m.id)
    return _MODEL_CACHE[family]
```

- **Cost:** one extra `models.list()` call per process per family. Set `ANTHROPIC_MODEL_HAIKU` to skip it on hot paths such as hooks that fire on every tool call.
- **Pinning:** when you need reproducibility (evals, regulated workflows), pin with the env var, not in code.
- **Failure:** if no model matches, `next()` raises inside the caller's existing `try/except`, which returns `None`. That is the same behavior as any other API failure in these scripts.

## Choosing a family

| Family | Use for |
|---|---|
| `opus` | Planning, review, orchestrators of complex work, meta-agents |
| `sonnet` | Building, general workers, default agents |
| `haiku` | Summarizers, classifiers, autocomplete, high-volume hooks |

## What was changed in the lesson code

- 428 full model IDs and 56 versioned display names were replaced across 127 files: code, configs, `.env.sample`, SQL comments, YAML expertise, specs, reviews, READMEs and prompt frontmatter.
- The duplicate versioned enum members in `adw_agent_sdk.py` were removed, leaving `OPUS`/`SONNET`/`HAIKU`.
- Nine raw-API scripts got `resolve_model`.
- `test_agent_expert.py` now asserts `haiku`, the model the Nile agent actually uses. Its old assertion was already out of date.
- `model_extractor.py` docstrings describe full IDs generically (`claude-haiku-<version>`), because they document what transcripts contain.
- **Not changed:** the two lesson transcripts (`*.txt`) are verbatim source recordings, and lockfiles pin package versions, not models.

## Keeping it clean

```bash
# should print nothing (transcripts and lockfiles excluded)
grep -rInE --exclude-dir=.git --exclude-dir=node_modules --exclude='*.txt' --exclude='*.lock' \
  "claude-[0-9a-z-]*(sonnet|opus|haiku)-?[0-9]|\b(sonnet|opus|haiku)[- ._][0-9]|\b(Sonnet|Opus|Haiku) [0-9]" .
```
