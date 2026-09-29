# Fix Nested Slash Command Discovery

## Problem Statement

The slash command discovery system in `apps/orchestrator_3_stream/backend/modules/slash_command_parser.py` is not loading commands from nested directories. Specifically, the command file at `.claude/commands/experts/websocket/question.md` is not being discovered and loaded into the GlobalCommandInput component.

**Current Behavior:**
- Only `.md` files directly in `.claude/commands/` are discovered
- Nested commands like `experts/websocket/question.md` are ignored
- Frontend GlobalCommandInput component doesn't display nested commands

**Expected Behavior:**
- All `.md` files in `.claude/commands/` and subdirectories should be discovered
- Nested paths should be converted to namespaced command names (e.g., `experts:websocket:question`)
- Frontend should display all commands including nested ones

## Root Cause Analysis

### File Discovery Issue

**Location:** `apps/orchestrator_3_stream/backend/modules/slash_command_parser.py` (line 229)

```python
# Current implementation - ONLY searches immediate directory
for file_path in commands_dir.glob("*.md"):
```

**Problem:** The `glob("*.md")` pattern only matches files in the immediate directory. It does not search subdirectories.

**Evidence:**
- Directory structure shows nested command: `.claude/commands/experts/websocket/question.md`
- Current code only finds commands in `.claude/commands/*.md`
- Need to support nested directory structure with double underscore separator

### Command Naming Issue

**Location:** `apps/orchestrator_3_stream/backend/modules/slash_command_parser.py` (line 236)

```python
commands.append({
    "name": file_path.stem,  # Only uses filename without path
    ...
})
```

**Problem:** Using `file_path.stem` only gets the filename (e.g., "question") without the directory path. For nested commands, we need to build a namespaced name like `experts:websocket:question`.

## Technical Approach

### 1. Update Glob Pattern for Recursive Search

**Change:** Use `glob("**/*.md")` to recursively search all subdirectories.

**Rationale:**
- `*` matches files in current directory only
- `**` matches all subdirectories recursively
- `**/*.md` matches all `.md` files at any depth

### 2. Build Namespaced Command Names

**Strategy:** Convert directory path to colon-separated namespace

**Why Colon (`:`) Instead of Double Underscore?**
- Visually distinct and easy to read as a separator
- Familiar from many namespace conventions (CSS, XML, package names)
- More intuitive and readable than double underscores
- Clear hierarchical structure representation
- Standard in command-line tools and configurations

**Examples:**
- `.claude/commands/question.md` → `question`
- `.claude/commands/experts/websocket/question.md` → `experts:websocket:question`
- `.claude/commands/build/parallel.md` → `build:parallel`

**Algorithm:**
1. Calculate relative path from `.claude/commands/` to the file
2. Get parent directory path (if any)
3. Convert path separators to colons (`:`)
4. Append filename (without extension)

### 3. Maintain Backward Compatibility

**Consideration:** Commands in the root `.claude/commands/` directory should keep their simple names (e.g., `plan`, not `:plan` or `commands:plan`).

**Solution:** Only add namespace prefix if the file is in a subdirectory.

## Implementation Plan

### Step 1: Update `discover_slash_commands()` Function

**File:** `apps/orchestrator_3_stream/backend/modules/slash_command_parser.py`

**Changes:**

```python
def discover_slash_commands(working_dir: str) -> List[dict]:
    """
    Discover slash commands from .claude/commands/ directory.

    Searches recursively for all .md files in subdirectories and creates
    namespaced command names based on directory structure.

    Examples:
        .claude/commands/plan.md → "plan"
        .claude/commands/experts/websocket/question.md → "experts:websocket:question"
    """
    from pathlib import Path
    import logging

    logger = logging.getLogger(__name__)
    commands = []
    commands_dir = Path(working_dir) / ".claude" / "commands"

    if not commands_dir.exists():
        return commands

    # ✅ CHANGE: Use **/*.md to search recursively
    for file_path in commands_dir.glob("**/*.md"):
        try:
            content = file_path.read_text()
            frontmatter = parse_slash_command_file(content)

            # ✅ NEW: Build namespaced command name
            # Calculate relative path from commands_dir
            relative_path = file_path.relative_to(commands_dir)

            # Get parent directory (if nested)
            if relative_path.parent != Path('.'):
                # Convert path separators to colons
                namespace = str(relative_path.parent).replace('/', ':').replace('\\', ':')
                command_name = f"{namespace}:{file_path.stem}"
            else:
                # Root level command - use simple name
                command_name = file_path.stem

            if frontmatter:
                commands.append({
                    "name": command_name,  # ✅ CHANGE: Use namespaced name
                    "description": frontmatter.description or "",
                    "arguments": frontmatter.argument_hint or "",
                    "model": frontmatter.model or "",
                    "allowed_tools": frontmatter.allowed_tools or [],
                    "disable_model_invocation": frontmatter.disable_model_invocation or False,
                })
            else:
                commands.append({
                    "name": command_name,  # ✅ CHANGE: Use namespaced name
                    "description": "",
                    "arguments": "",
                    "model": "",
                    "allowed_tools": [],
                    "disable_model_invocation": False,
                })

        except Exception as e:
            logger.error(
                f"Failed to parse slash command file {file_path.name}: {e}",
                exc_info=True
            )
            raise

    # Sort by name
    commands.sort(key=lambda x: x["name"])

    return commands
```

### Step 2: Test Command Discovery

**Create test script:** `apps/orchestrator_3_stream/backend/tests/test_slash_command_discovery.py`

```python
"""
Test slash command discovery with nested directories
"""
import pytest
from pathlib import Path
from modules.slash_command_parser import discover_slash_commands

def test_discover_nested_commands(tmp_path):
    """Test that nested slash commands are discovered with namespaced names"""

    # Create test directory structure
    commands_dir = tmp_path / ".claude" / "commands"
    commands_dir.mkdir(parents=True)

    # Create root level command
    root_cmd = commands_dir / "test.md"
    root_cmd.write_text("""---
description: Root level test command
---
# Test Command
""")

    # Create nested command
    nested_dir = commands_dir / "experts" / "websocket"
    nested_dir.mkdir(parents=True)
    nested_cmd = nested_dir / "question.md"
    nested_cmd.write_text("""---
description: Nested websocket command
argument-hint: [question]
---
# Websocket Question
""")

    # Discover commands
    commands = discover_slash_commands(str(tmp_path))

    # Verify both commands found
    assert len(commands) == 2

    # Verify root command has simple name
    root = next((c for c in commands if c["name"] == "test"), None)
    assert root is not None
    assert root["description"] == "Root level test command"

    # Verify nested command has namespaced name
    nested = next((c for c in commands if c["name"] == "experts:websocket:question"), None)
    assert nested is not None
    assert nested["description"] == "Nested websocket command"
    assert nested["arguments"] == "[question]"

def test_discover_multiple_nesting_levels(tmp_path):
    """Test commands at different nesting levels"""

    commands_dir = tmp_path / ".claude" / "commands"
    commands_dir.mkdir(parents=True)

    # Level 0 (root)
    (commands_dir / "root.md").write_text("---\ndescription: Root\n---\n")

    # Level 1
    level1_dir = commands_dir / "level1"
    level1_dir.mkdir()
    (level1_dir / "cmd1.md").write_text("---\ndescription: Level 1\n---\n")

    # Level 2
    level2_dir = level1_dir / "level2"
    level2_dir.mkdir()
    (level2_dir / "cmd2.md").write_text("---\ndescription: Level 2\n---\n")

    # Level 3
    level3_dir = level2_dir / "level3"
    level3_dir.mkdir()
    (level3_dir / "cmd3.md").write_text("---\ndescription: Level 3\n---\n")

    commands = discover_slash_commands(str(tmp_path))

    assert len(commands) == 4

    names = [c["name"] for c in commands]
    assert "root" in names
    assert "level1:cmd1" in names
    assert "level1:level2:cmd2" in names
    assert "level1:level2:level3:cmd3" in names

def test_empty_commands_directory(tmp_path):
    """Test with no commands"""
    commands_dir = tmp_path / ".claude" / "commands"
    commands_dir.mkdir(parents=True)

    commands = discover_slash_commands(str(tmp_path))
    assert len(commands) == 0

def test_missing_commands_directory(tmp_path):
    """Test with missing .claude/commands directory"""
    commands = discover_slash_commands(str(tmp_path))
    assert len(commands) == 0
```

### Step 3: Verify Frontend Display

**File:** `apps/orchestrator_3_stream/frontend/src/components/GlobalCommandInput.vue`

**Verification:** No changes needed to frontend. The component already handles command names from the API response and displays them in badges. The namespaced names will automatically appear in the format `experts:websocket:question`.

**Test:**
1. Start backend server
2. Open frontend and press Cmd+K
3. Verify `experts__websocket__question` appears in Slash Commands section
4. Click badge to verify it inserts `/experts__websocket__question` into input

### Step 4: Integration Testing

**Manual test checklist:**

1. ✅ Backend discovers nested commands
   - Run: `uv run python -c "from modules.slash_command_parser import discover_slash_commands; import json; print(json.dumps(discover_slash_commands('.'), indent=2))"`
   - Verify: `experts:websocket:question` appears in output

2. ✅ API endpoint returns nested commands
   - Run backend: `./start_be.sh`
   - Test: `curl http://localhost:8002/get_orchestrator | jq '.slash_commands'`
   - Verify: `experts:websocket:question` in response

3. ✅ Frontend displays nested commands
   - Run frontend: `./start_fe.sh`
   - Open browser and press Cmd+K
   - Verify: Badge shows `experts:websocket:question`

4. ✅ Clicking badge inserts command
   - Click `experts:websocket:question` badge
   - Verify: `/experts:websocket:question` appears in input field

5. ✅ Command can be invoked
   - Type: `/experts:websocket:question what events do we have?`
   - Send message
   - Verify: Command executes successfully

## Edge Cases and Considerations

### 1. Windows Path Separators

**Issue:** Windows uses backslash `\` instead of forward slash `/`

**Solution:** Replace both `/` and `\` with `:` when building namespace

```python
namespace = str(relative_path.parent).replace('/', ':').replace('\\', ':')
```

**Note:** While colons are reserved in Windows for drive letters (e.g., `C:`), this only affects the command *name* in memory/database, not the directory structure on disk. The actual `.md` files remain in their normal directory paths.

### 2. Special Characters in Directory Names

**Issue:** What if directory name contains colons or other special characters?

**Solution:** Current approach assumes directory names follow standard conventions (alphanumeric, hyphens, underscores). Colons are not valid in directory names on most filesystems anyway.

**Recommendation:** Document naming conventions:
- Use lowercase
- Use hyphens or underscores for word separation
- Avoid special characters except hyphens and underscores
- Example: `experts/web-socket/advanced-question.md` → `experts:web-socket:advanced-question`
- Example: `experts/websocket/advanced_query.md` → `experts:websocket:advanced_query`

### 3. Command Name Collisions

**Issue:** What if there's both `plan.md` and `plan/default.md`?

**Result:** Two different commands:
- `plan` (from root)
- `plan:default` (from subdirectory)

**Verdict:** This is acceptable. They are different commands.

### 4. Hidden Directories and Files

**Issue:** Should we skip hidden directories (starting with `.`)?

**Solution:** `glob("**/*.md")` will include hidden directories by default. If needed, add filter:

```python
for file_path in commands_dir.glob("**/*.md"):
    # Skip hidden directories
    if any(part.startswith('.') for part in file_path.relative_to(commands_dir).parts):
        continue
```

**Decision:** Not needed for MVP. Hidden directories are uncommon in command structures.

### 5. Performance with Large Directory Trees

**Issue:** Will recursive glob be slow with many files?

**Analysis:**
- Typical command directories have 10-50 files
- `glob("**/*.md")` is implemented in C and is very fast
- Even with 1000 files, performance impact is negligible

**Verdict:** No optimization needed.

## Testing Strategy

### Unit Tests
- ✅ Test recursive discovery of nested commands
- ✅ Test namespace generation for different depths
- ✅ Test backward compatibility with root-level commands
- ✅ Test empty/missing directories
- ✅ Test sorting of namespaced commands

### Integration Tests
- ✅ Test API endpoint returns nested commands
- ✅ Test frontend receives and displays nested commands
- ✅ Test clicking badge inserts correct command text

### Manual Tests
- ✅ Verify `experts__websocket__question` appears in Cmd+K panel
- ✅ Verify clicking badge works correctly
- ✅ Verify command can be invoked successfully

## Success Criteria

1. ✅ All `.md` files in `.claude/commands/` subdirectories are discovered
2. ✅ Nested commands have proper namespaced names using colon separator (e.g., `experts:websocket:question`)
3. ✅ Root-level commands maintain simple names (e.g., `plan`)
4. ✅ Backend API returns nested commands in `/get_orchestrator` response
5. ✅ Frontend GlobalCommandInput displays nested commands as badges
6. ✅ Clicking nested command badge inserts correct text into input
7. ✅ All tests pass
8. ✅ No regressions for existing root-level commands

## Implementation Checklist

- [ ] Update `discover_slash_commands()` to use `glob("**/*.md")`
- [ ] Add namespace building logic based on directory structure
- [ ] Create unit tests for slash command discovery
- [ ] Run unit tests and verify all pass
- [ ] Test backend API manually with curl
- [ ] Test frontend display in browser
- [ ] Test clicking badges in frontend
- [ ] Test invoking nested commands
- [ ] Update CLAUDE.md documentation with nested command support
- [ ] Commit changes with descriptive message

## Files to Modify

1. **apps/orchestrator_3_stream/backend/modules/slash_command_parser.py**
   - Update `discover_slash_commands()` function
   - Add namespace building logic

2. **apps/orchestrator_3_stream/backend/tests/test_slash_command_discovery.py** (new)
   - Add comprehensive unit tests

3. **apps/orchestrator_3_stream/CLAUDE.md** (documentation)
   - Document nested slash command support
   - Add examples of namespaced commands

## Risk Assessment

**Risk Level:** Low

**Rationale:**
- Changes are isolated to command discovery function
- Backward compatible (root-level commands unchanged)
- No database changes required
- Frontend already handles any command name format
- Easy to test and verify

**Mitigation:**
- Comprehensive unit tests
- Manual testing before deployment
- Can easily revert if issues arise

## Timeline Estimate

- Implementation: 30 minutes
- Testing: 20 minutes
- Documentation: 10 minutes
- **Total:** ~1 hour

## Next Steps

1. Implement changes to `slash_command_parser.py`
2. Create and run unit tests
3. Manual testing with backend and frontend
4. Update documentation
5. Commit changes

---

**Created:** 2025-11-10
**Status:** Ready for implementation
**Priority:** Medium
**Complexity:** Low
