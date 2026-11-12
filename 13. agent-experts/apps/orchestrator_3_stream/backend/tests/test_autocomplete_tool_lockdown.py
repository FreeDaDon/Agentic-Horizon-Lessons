"""
Offline test that the autocomplete session gets no tools.

The prompt carries whatever the user typed. The test builds the real
AutocompleteAgent and reads the options of the Claude Agent SDK client it
creates; the client is never connected, so no API key is needed.
"""

import sys
import uuid
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.autocomplete_agent import AutocompleteAgent  # noqa: E402

EVERY_BUILTIN_TOOL = {
    "Read", "Write", "Edit", "MultiEdit", "NotebookEdit", "Glob", "Grep", "Bash",
    "BashOutput", "KillShell", "WebFetch", "WebSearch", "Task", "TodoWrite",
    "ExitPlanMode", "SlashCommand", "Skill", "AskUserQuestion",
}


def test_autocomplete_session_has_no_tools(tmp_path):
    agent = AutocompleteAgent(str(uuid.uuid4()), Mock(), str(tmp_path))

    options = agent.client.options
    assert options.tools == []
    assert options.allowed_tools == []
    assert set(options.disallowed_tools) >= EVERY_BUILTIN_TOOL
    assert options.max_turns == 1
    assert options.permission_mode != "bypassPermissions"
