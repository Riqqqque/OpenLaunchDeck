from openlaunchdeck.actions.registry import create_default_registry


def test_default_registry_contains_default_actions():
    registry = create_default_registry()
    for action_type in [
        "noop",
        "switch_page",
        "open_url",
        "open_path",
        "run_command",
        "powershell",
        "hotkey",
        "type_text",
        "media_control",
        "volume_control",
        "http_request",
        "play_sound",
        "stop_sound",
        "multi_action",
        "delay",
        "ssh_command",
        "obs_websocket",
    ]:
        assert registry.get(action_type).type_name == action_type


def test_unknown_action_falls_back_to_noop():
    registry = create_default_registry()
    assert registry.get("missing").type_name == "noop"
