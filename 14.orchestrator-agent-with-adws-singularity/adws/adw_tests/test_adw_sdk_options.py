"""
QueryOptions reaches ClaudeAgentOptions intact, and query_to_completion reports what
the SDK said (offline: recorded message streams through fakes.ReplayClient).

Run: see fakes.py for the offline approach and the run command.
"""

import asyncio

from fakes import Replays, assistant, init_message, result  # first: puts adws/ on sys.path

from claude_agent_sdk import ClaudeAgentOptions, TextBlock, create_sdk_mcp_server

from adw_modules.adw_agent_sdk import (
    HookResponse,
    HooksConfig,
    HookMatcher,
    QueryInput,
    QueryOptions,
    SystemPromptConfig,
    SystemPromptMode,
    build_sdk_options,
    query_to_completion,
)


async def _allow(hook_input, tool_use_id, context):
    return HookResponse.allow()


def fully_populated() -> QueryOptions:
    """A value different from the SDK default for every QueryOptions field."""
    return QueryOptions(
        model="haiku",
        resume="sess-0",
        fork_session=True,
        cwd="/work",
        permission_mode="dontAsk",
        tools=["Read"],
        allowed_tools=["Read", "Bash(git diff:*)"],
        disallowed_tools=["Write"],
        hooks=HooksConfig(pre_tool_use=[HookMatcher(matcher="Bash", hooks=[_allow])]),
        mcp_servers={"adw": create_sdk_mcp_server(name="adw", tools=[])},
        setting_sources=["user", "project"],
        max_turns=7,
        max_budget_usd=1.25,
        system_prompt=SystemPromptConfig(mode=SystemPromptMode.APPEND, system_prompt="Be brief."),
    )


def test_every_query_option_reaches_the_sdk():
    """If a QueryOptions field is added without forwarding it, this fails: its SDK
    value stays at the ClaudeAgentOptions default."""
    opts = fully_populated()
    sdk = build_sdk_options(opts)
    defaults = ClaudeAgentOptions()

    dropped = [
        name for name in QueryOptions.model_fields
        if not hasattr(sdk, name) or getattr(sdk, name) == getattr(defaults, name)
    ]
    assert dropped == []

    passthrough = ["model", "resume", "fork_session", "cwd", "permission_mode", "tools", "allowed_tools",
                   "disallowed_tools", "setting_sources", "max_turns", "max_budget_usd"]
    assert {n: getattr(sdk, n) for n in passthrough} == {n: getattr(opts, n) for n in passthrough}
    assert sdk.mcp_servers["adw"]["type"] == "sdk"
    assert sdk.system_prompt == {"type": "preset", "preset": "claude_code", "append": "Be brief."}
    assert [m.matcher for m in sdk.hooks["PreToolUse"]] == ["Bash"]


def test_permission_mode_defaults_to_the_sdk_default_not_bypass():
    assert build_sdk_options(QueryOptions()).permission_mode == "default"


def test_result_fields_and_deduplicated_usage():
    usage = {"input_tokens": 10, "output_tokens": 5}
    replays = Replays([
        init_message(),
        # One API message split across two SDK messages that repeat its usage
        assistant(TextBlock("part 1"), message_id="m1", usage=usage),
        assistant(TextBlock("part 2"), message_id="m1", usage=usage),
        assistant(TextBlock("next"), message_id="m2", usage=usage),
        result(cost=0.42, turns=2, text="all done"),
    ])
    out = asyncio.run(query_to_completion(QueryInput(prompt="hi"), client_factory=replays))

    assert out.success and out.result == "all done"
    assert (out.result_subtype, out.num_turns, out.total_cost_usd) == ("success", 2, 0.42)
    assert out.usage_accumulator.processed_ids == {"m1", "m2"}
    assert out.usage_accumulator.total_input_tokens == 20


def test_error_result_keeps_the_sdk_subtype_and_reason():
    replays = Replays([init_message(), result("error_max_turns", is_error=True, text=None,
                                               errors=["Reached maximum number of turns (3)"])])
    out = asyncio.run(query_to_completion(QueryInput(prompt="hi"), client_factory=replays))

    assert not out.success
    assert out.result_subtype == "error_max_turns"
    assert out.error == "Reached maximum number of turns (3)"
