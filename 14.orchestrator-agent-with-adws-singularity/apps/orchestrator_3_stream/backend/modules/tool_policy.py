"""
Tool Policy - which built-in tools each kind of Claude session may use.

allowed_tools only pre-approves tools; it does not hide the others, and
permission_mode="acceptEdits" approves Write/Edit on its own. A tool is out of
reach only when it is in disallowed_tools (or the `tools` base set is empty),
so every restriction below is written as a disallow list.
"""

from typing import Any, Dict, List, Optional

from claude_agent_sdk import ClaudeAgentOptions

BUILTIN_TOOLS = (
    "Read",
    "Write",
    "Edit",
    "MultiEdit",
    "NotebookEdit",
    "Glob",
    "Grep",
    "Bash",
    "BashOutput",
    "KillShell",
    "WebFetch",
    "WebSearch",
    "Task",
    "TodoWrite",
    "ExitPlanMode",
    "SlashCommand",
    "Skill",
    "AskUserQuestion",
)

DEFAULT_COMMAND_ALLOWED_TOOLS = (
    "Read",
    "Write",
    "Edit",
    "Bash",
    "Glob",
    "Grep",
    "Task",
    "WebFetch",
    "WebSearch",
    "BashOutput",
    "SlashCommand",
    "TodoWrite",
    "KillShell",
    "AskUserQuestion",
    "Skill",
)

DEFAULT_COMMAND_DISALLOWED_TOOLS = ("NotebookEdit", "ExitPlanMode")


def text_only_options(**options: Any) -> ClaudeAgentOptions:
    """
    Options for a session that reads untrusted text (tool inputs, tool output,
    user typing) and must answer with text only: no tools, one turn.
    """
    return ClaudeAgentOptions(
        tools=[],
        allowed_tools=[],
        disallowed_tools=list(BUILTIN_TOOLS),
        max_turns=1,
        **options,
    )


def command_tool_policy(allowed_tools: Optional[List[str]]) -> Dict[str, List[str]]:
    """
    Tool policy for a command agent, stored in agents.metadata at creation.

    None means the general-purpose default set. A list (from a subagent
    template's `tools` or create_agent's `tools`) is the whole allowance:
    every other built-in is disallowed.
    """
    if allowed_tools is None:
        return {
            "allowed_tools": list(DEFAULT_COMMAND_ALLOWED_TOOLS),
            "disallowed_tools": list(DEFAULT_COMMAND_DISALLOWED_TOOLS),
        }
    return {
        "allowed_tools": list(allowed_tools),
        "disallowed_tools": [t for t in BUILTIN_TOOLS if t not in allowed_tools],
    }


def stored_tool_policy(agent_metadata: Dict[str, Any]) -> Dict[str, List[str]]:
    """The policy persisted on an agent; agents created before it was persisted get the default."""
    if "allowed_tools" in agent_metadata:
        return {
            "allowed_tools": list(agent_metadata["allowed_tools"]),
            "disallowed_tools": list(agent_metadata.get("disallowed_tools", [])),
        }
    return command_tool_policy(None)
