# Opus Model Update Implementation Plan

## Objective

Update the default model configuration from Claude Sonnet (`sonnet`) to Claude Opus (`opus`) for both the orchestrator agent and command-level agents in the multi-agent orchestration system.

## Requirements Summary

1. **Change default model** from Sonnet to Opus
2. **Add 'opus' alias** to model alias mapping
3. **Support full model name** `opus`
4. **Keep haiku/fast model logic unchanged**
5. **Orchestrator agent** must use Opus as default
6. **Command-level agents** must use Opus as default (unless overridden)

---

## Current Architecture Analysis

### Model Configuration Flow

```
config.py (DEFAULT_MODEL, ORCHESTRATOR_MODEL, DEFAULT_AGENT_MODEL)
    │
    ├── orchestrator_service.py → Uses ORCHESTRATOR_MODEL for orchestrator agent
    │
    └── agent_manager.py → Uses DEFAULT_AGENT_MODEL for command-level agents
                          → Has model_aliases dict for alias resolution
```

### Key Files Identified

| File | Role | Lines of Interest |
|------|------|-------------------|
| `backend/modules/config.py` | Central configuration | Lines 89-102, 145-146 |
| `backend/modules/agent_manager.py` | Model alias mapping | Lines 126-140, 668, 698, 726 |
| `backend/modules/orchestrator_service.py` | Orchestrator model | Line 242 |
| `backend/modules/single_agent_prompt.py` | Fast model (Haiku) | Line 35 |
| `backend/modules/subagent_models.py` | Documentation only | Lines 24, 30 |
| `backend/modules/autocomplete_agent.py` | Uses Haiku explicitly | Line 189 |

---

## Files to Modify

### 1. `backend/modules/config.py`

**Location:** Lines 89-102, 145-146

**Current Code:**
```python
# Line 89-95
# Default model for agents
DEFAULT_MODEL = "sonnet"

FAST_MODEL = "haiku"

# Available models
AVAILABLE_MODELS = ["sonnet", "haiku"]

# Line 101-102
# Orchestrator agent model
ORCHESTRATOR_MODEL = os.getenv("ORCHESTRATOR_MODEL", DEFAULT_MODEL)
```

**New Code:**
```python
# Line 89-95
# Default model for agents (Opus is the primary model)
DEFAULT_MODEL = "opus"

FAST_MODEL = "haiku"

# Available models
AVAILABLE_MODELS = ["opus", "sonnet", "haiku"]

# Line 101-102
# Orchestrator agent model
ORCHESTRATOR_MODEL = os.getenv("ORCHESTRATOR_MODEL", DEFAULT_MODEL)
```

**Rationale:**
- `DEFAULT_MODEL` is the single source of truth for the default model
- `ORCHESTRATOR_MODEL` already uses `DEFAULT_MODEL` as fallback, so it will automatically use Opus
- Adding Opus to `AVAILABLE_MODELS` documents valid options

---

### 2. `backend/modules/agent_manager.py`

**Location:** Lines 129-134

**Current Code:**
```python
# Model alias mapping
model_aliases = {
    "sonnet": "sonnet",
    "haiku": "haiku",
    "fast": "haiku",  # Alias for haiku
}
```

**New Code:**
```python
# Model alias mapping
model_aliases = {
    "opus": "opus",
    "sonnet": "sonnet",
    "haiku": "haiku",
    "fast": "haiku",  # Alias for haiku
}
```

**Rationale:**
- Adds `opus` alias to allow users to specify `model: opus` in agent creation
- Maintains backward compatibility with existing `sonnet`, `haiku`, and `fast` aliases
- Full model names still work via the `model_aliases.get(model_input.lower(), model_input)` pattern

---

### 3. `backend/modules/subagent_models.py` (Documentation Update)

**Location:** Lines 24, 30

**Current Code:**
```python
# Line 24
        model: Optional model override (sonnet, haiku, opus)
# Line 30
    model: Optional[str] = Field(None, description="Model override (sonnet, haiku, opus)")
```

**No Changes Required** - Documentation already includes `opus` as a valid option.

---

## Files NOT to Modify

### `backend/modules/single_agent_prompt.py`

**Line 35:** `FAST_MODEL = "haiku"`

**Reason:** This module is specifically designed for fast, cheap summarization operations. Haiku should remain the default here for cost efficiency. The module explicitly states: "Fast single-shot queries using Claude Haiku for speed and cost efficiency."

### `backend/modules/autocomplete_agent.py`

**Line 189:** `"model": "haiku",  # LATEST HAIKU MODEL`

**Reason:** Autocomplete functionality is intentionally using Haiku for speed and cost. This is a deliberate design choice, not a default configuration issue.

### `backend/modules/orchestrator_service.py`

**Line 242:** Uses `config.ORCHESTRATOR_MODEL`

**Reason:** Already references `config.ORCHESTRATOR_MODEL`, which will automatically pick up the new default from `config.py`.

---

## Implementation Steps

### Step 1: Update `config.py`

1. Change `DEFAULT_MODEL` from `"sonnet"` to `"opus"`
2. Update `AVAILABLE_MODELS` to include Opus first (as primary model)

```python
# Before
DEFAULT_MODEL = "sonnet"
AVAILABLE_MODELS = ["sonnet", "haiku"]

# After
DEFAULT_MODEL = "opus"
AVAILABLE_MODELS = ["opus", "sonnet", "haiku"]
```

### Step 2: Update `agent_manager.py`

1. Add `"opus": "opus"` to `model_aliases` dict

```python
# Before
model_aliases = {
    "sonnet": "sonnet",
    "haiku": "haiku",
    "fast": "haiku",
}

# After
model_aliases = {
    "opus": "opus",
    "sonnet": "sonnet",
    "haiku": "haiku",
    "fast": "haiku",
}
```

---

## Acceptance Criteria

### Functional Tests

1. **Orchestrator uses Opus by default**
   - Start orchestrator without `ORCHESTRATOR_MODEL` env var
   - Verify orchestrator options show `model: opus`

2. **Command agents use Opus by default**
   - Create agent without specifying model: `create_agent(name="test", system_prompt="...")`
   - Verify agent.model is `opus`

3. **'opus' alias works**
   - Create agent with `model: "opus"`
   - Verify agent.model resolves to `opus`

4. **Full model name works**
   - Create agent with `model: "opus"`
   - Verify agent.model is `opus`

5. **'sonnet' alias still works**
   - Create agent with `model: "sonnet"`
   - Verify agent.model resolves to `sonnet`

6. **'haiku'/'fast' aliases still work**
   - Create agent with `model: "haiku"` or `model: "fast"`
   - Verify agent.model resolves to `haiku`

7. **Environment variable override works**
   - Set `ORCHESTRATOR_MODEL=sonnet`
   - Verify orchestrator uses Sonnet instead of Opus

8. **Fast/summarization models unchanged**
   - Verify `single_agent_prompt.py` still uses Haiku
   - Verify `autocomplete_agent.py` still uses Haiku

### Code Review Checklist

- [ ] `DEFAULT_MODEL` changed to Opus in `config.py`
- [ ] `AVAILABLE_MODELS` updated in `config.py`
- [ ] `opus` alias added to `model_aliases` in `agent_manager.py`
- [ ] Existing aliases (`sonnet`, `haiku`, `fast`) unchanged
- [ ] `FAST_MODEL` unchanged in `config.py` and `single_agent_prompt.py`
- [ ] No changes to autocomplete agent model

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Opus API costs higher than Sonnet | High | Medium | Users can override via env var or model param |
| Opus latency differences | Medium | Low | Fast operations still use Haiku |
| Backward compatibility | Low | Low | All existing aliases preserved |

---

## Rollback Plan

If issues arise, revert by:
1. Change `DEFAULT_MODEL` back to `"sonnet"` in `config.py`
2. Keep `opus` alias in `agent_manager.py` (no harm in keeping it)

---

## Summary of Changes

| File | Change | Lines |
|------|--------|-------|
| `backend/modules/config.py` | Update `DEFAULT_MODEL` to Opus | ~89-95 |
| `backend/modules/agent_manager.py` | Add `opus` alias to `model_aliases` | ~129-134 |

**Total: 2 files, ~6 lines changed**
