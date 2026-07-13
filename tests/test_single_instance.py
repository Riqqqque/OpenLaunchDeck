from __future__ import annotations

import uuid

from openlaunchdeck.app import handle_single_instance_command, resolve_start_minimized
from openlaunchdeck.single_instance import (
    COMMAND_BACKGROUND,
    COMMAND_SHOW,
    notify_existing_instance,
    parse_launch_options,
)


class WindowDouble:
    def __init__(self) -> None:
        self.restore_calls = 0

    def restore_from_tray(self) -> None:
        self.restore_calls += 1


def test_parse_launch_options_defaults_to_show_command():
    options = parse_launch_options(["OpenLaunchDeck.exe"])

    assert options.command == COMMAND_SHOW
    assert options.start_minimized_override is None


def test_parse_launch_options_supports_background_launch():
    options = parse_launch_options(["OpenLaunchDeck.exe", "--background"])

    assert options.command == COMMAND_BACKGROUND
    assert options.start_minimized_override is True


def test_parse_launch_options_supports_explicit_show_launch():
    options = parse_launch_options(["OpenLaunchDeck.exe", "--show"])

    assert options.command == COMMAND_SHOW
    assert options.start_minimized_override is False


def test_resolve_start_minimized_allows_external_launch_override():
    assert resolve_start_minimized(True, parse_launch_options(["OpenLaunchDeck.exe", "--show"])) is False
    assert resolve_start_minimized(False, parse_launch_options(["OpenLaunchDeck.exe", "--background"])) is True
    assert resolve_start_minimized(True, parse_launch_options(["OpenLaunchDeck.exe"])) is True


def test_single_instance_background_command_does_not_restore_window():
    window = WindowDouble()

    handle_single_instance_command(window, COMMAND_BACKGROUND)

    assert window.restore_calls == 0


def test_single_instance_show_command_restores_window():
    window = WindowDouble()

    handle_single_instance_command(window, COMMAND_SHOW)

    assert window.restore_calls == 1


def test_notify_existing_instance_returns_false_without_server():
    server_name = f"OpenLaunchDeck.Test.{uuid.uuid4()}"

    assert notify_existing_instance(COMMAND_BACKGROUND, server_name=server_name, timeout_ms=25) is False
