#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
Dangerous Command Blocker - Claude Code Hook
Prevents execution of dangerous commands like rm -rf
"""

import json
import re
import sys
import os
from datetime import datetime
from pathlib import Path

# Dangerous command patterns
DANGEROUS_PATTERNS = [
    # Direct rm -rf on critical paths
    r'rm\s+(-[rfRF]+\s+|\s+-[rfRF]+)(/\s*$|/\s+|\s+/\s*$|\s+/\s+)',
    r'rm\s+(-[rfRF]+\s+|\s+-[rfRF]+)(\*|\.\s*$|\.\.\s*$)',
    r'rm\s+(-[rfRF]+\s+|\s+-[rfRF]+)(~|\$HOME|\${HOME})',

    # Recursive + force with wildcards
    r'rm\s+.*-r.*-f.*\*',
    r'rm\s+.*-f.*-r.*\*',

    # Long form options
    r'rm\s+.*(--recursive|--force).*(/\s*$|\*)',

    # Prevent removal of current directory or parent
    r'rm\s+-[rfRF]+\s+\./?(\s|$)',
    r'rm\s+-[rfRF]+\s+\.\./?(\s|$)',
]

# Additional context-aware checks
CRITICAL_PATHS = [
    '/',
    '/etc',
    '/usr',
    '/bin',
    '/sbin',
    '/boot',
    '/dev',
    '/lib',
    '/proc',
    '/sys',
    '/var',
    os.path.expanduser('~'),
    '~',
    '$HOME',
    '${HOME}',
]


def is_dangerous_command(command: str) -> tuple[bool, str]:
    """
    Check if command is dangerous.
    Returns (is_dangerous, reason)
    """
    # Check regex patterns
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, f"Command matches dangerous pattern: {pattern}"

    # Flags are case-insensitive here: rm -R is the same as rm -r
    lowered = command.lower()

    # Check for rm on critical paths
    if 'rm' in command:
        for critical_path in CRITICAL_PATHS:
            if critical_path in command and '-r' in lowered:
                return True, f"Recursive removal targeting critical path: {critical_path}"

    # Check for multiple wildcards with force/recursive
    if 'rm' in command and ('*' in command or '?' in command):
        if '-rf' in lowered or '-fr' in lowered or ('-r' in lowered and '-f' in lowered):
            wildcard_count = command.count('*') + command.count('?')
            if wildcard_count > 1:
                return True, "Multiple wildcards with force/recursive flags"

    return False, ""


def suggest_safer_alternative(command: str) -> str:
    """Suggest a safer alternative to the dangerous command."""
    suggestions = []

    if 'rm -rf' in command or 'rm -fr' in command:
        suggestions.append("• Use 'rm -r' without -f for important deletions (allows prompting)")
        suggestions.append("• Specify exact paths instead of using wildcards")
        suggestions.append("• Consider using 'trash' command to move to trash instead")
        suggestions.append("• Use 'find' with -delete for more controlled deletion")

    if '*' in command:
        suggestions.append("• List files first with 'ls' before using wildcards")
        suggestions.append("• Use specific file patterns instead of broad wildcards")

    return "\n".join(suggestions) if suggestions else "Consider a more specific, safer command"


def log_blocked_command(session_id: str, command: str, reason: str):
    """Log blocked commands for security audit."""
    try:
        project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
        log_dir = Path(project_dir) / "agents" / "security_logs" / session_id
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / "blocked_commands.jsonl"
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "reason": reason,
            "action": "blocked"
        }

        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception:
        # Silently fail logging - don't let it affect the blocking
        pass


def main():
    try:
        # Read input from stdin
        input_data = json.load(sys.stdin)

        # Only process Bash tool calls
        if input_data.get("tool_name") != "Bash":
            sys.exit(0)

        # Extract command
        tool_input = input_data.get("tool_input", {})
        command = tool_input.get("command", "")

        if not command:
            sys.exit(0)

        # Check if command is dangerous
        is_dangerous, reason = is_dangerous_command(command)

        if is_dangerous:
            # Log the blocked command for audit
            session_id = input_data.get("session_id", "unknown")
            log_blocked_command(session_id, command, reason)

            # Provide detailed feedback to Claude
            error_message = f"""BLOCKED: Dangerous command detected!

Command: {command}
Reason: {reason}

This command could cause irreversible data loss or system damage.

Safer alternatives:
{suggest_safer_alternative(command)}

Please reconsider your approach and use a safer command."""

            print(error_message, file=sys.stderr)
            sys.exit(2)  # Block execution and show stderr to Claude

        # Command is safe, allow execution
        sys.exit(0)

    except Exception as e:
        # Fail closed: exit 1 would let the command run unchecked
        print(f"BLOCKED: dangerous command check could not run ({type(e).__name__}: {e})", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()