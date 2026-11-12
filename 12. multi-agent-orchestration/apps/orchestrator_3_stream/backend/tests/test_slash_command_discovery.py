"""
Test slash command discovery (root-level .claude/commands/ only)

Ported from lesson 13's test_slash_command_discovery.py. Lesson 12's parser
predates nested command directories and the allowed-tools alias, so only the
tests for behavior this version has are kept:
- Discovers commands in root .claude/commands/ directory
- Handles empty and missing directories, missing frontmatter, special characters
"""

from pathlib import Path
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modules.slash_command_parser import discover_slash_commands


def test_discover_root_level_commands(tmp_path):
    """Test that root-level commands are discovered with simple names"""

    # Create test directory structure
    commands_dir = tmp_path / ".claude" / "commands"
    commands_dir.mkdir(parents=True)

    # Create root level command
    root_cmd = commands_dir / "test.md"
    root_cmd.write_text("""---
description: Root level test command
argument-hint: [arg1]
model: sonnet
---
# Test Command
""")

    # Discover commands
    commands = discover_slash_commands(str(tmp_path))

    # Verify command found
    assert len(commands) == 1

    # Verify root command has simple name
    assert commands[0]["name"] == "test"
    assert commands[0]["description"] == "Root level test command"
    assert commands[0]["arguments"] == "[arg1]"
    assert commands[0]["model"] == "sonnet"


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


def test_commands_without_frontmatter(tmp_path):
    """Test that commands without frontmatter still get discovered"""

    commands_dir = tmp_path / ".claude" / "commands"
    commands_dir.mkdir(parents=True)

    # Create command without frontmatter
    cmd = commands_dir / "no-frontmatter.md"
    cmd.write_text("# Just a regular markdown file\n\nWith no frontmatter")

    # Discover commands
    commands = discover_slash_commands(str(tmp_path))

    # Verify command found with empty metadata
    assert len(commands) == 1
    assert commands[0]["name"] == "no-frontmatter"
    assert commands[0]["description"] == ""
    assert commands[0]["arguments"] == ""
    assert commands[0]["model"] == ""


def test_special_characters_in_arguments(tmp_path):
    """Test that special characters in argument-hint are preserved"""

    commands_dir = tmp_path / ".claude" / "commands"
    commands_dir.mkdir(parents=True)

    # Create command with special characters in argument-hint
    cmd = commands_dir / "tag.md"
    cmd.write_text("""---
description: Manage tags
argument-hint: add [tagId] | remove [tagId] | list
---
# Tag Management
""")

    # Discover commands
    commands = discover_slash_commands(str(tmp_path))

    # Verify special characters are preserved
    assert len(commands) == 1
    assert commands[0]["arguments"] == "add [tagId] | remove [tagId] | list"

