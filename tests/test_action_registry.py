from openlaunchdeck.actions.registry import create_default_registry


def test_default_registry_contains_mvp_actions():
    registry = create_default_registry()
    for action_type in [
        "noop",
        "switch_page",
        "open_url",
        "open_path",
        "run_command",
        "hotkey",
        "play_sound",
        "stop_sound",
        "multi_action",
        "delay",
    ]:
        assert registry.get(action_type).type_name == action_type


def test_unknown_action_falls_back_to_noop():
    registry = create_default_registry()
    assert registry.get("missing").type_name == "noop"
