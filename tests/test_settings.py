from openlaunchdeck.models.settings import Settings


def test_settings_grid_density_defaults_and_validation():
    assert Settings.from_dict({}).grid_density == "comfortable"
    assert Settings.from_dict({"grid_density": "compact"}).grid_density == "compact"
    assert Settings.from_dict({"grid_density": "huge"}).grid_density == "comfortable"


def test_settings_keep_soundboard_voice_chat_routing_fields():
    settings = Settings.from_dict(
        {
            "soundboard_voice_chat_output_device": "voice-cable",
            "soundboard_monitor_voice_chat": False,
            "soundboard_voice_route_microphone_enabled": True,
            "soundboard_voice_route_microphone_device": "mic-1",
            "soundboard_voice_route_microphone_volume": 120,
        }
    )

    assert settings.soundboard_voice_chat_output_device == "voice-cable"
    assert settings.soundboard_monitor_voice_chat is False
    assert settings.soundboard_voice_route_microphone_enabled is True
    assert settings.soundboard_voice_route_microphone_device == "mic-1"
    assert settings.soundboard_voice_route_microphone_volume == 100


def test_settings_recover_from_wrong_types():
    settings = Settings.from_dict(
        {
            "theme": ["dark"],
            "auto_connect": "false",
            "minimize_to_tray": "yes",
            "soundboard_global_volume": "loud",
            "update_channel": 7,
        }
    )

    assert settings.theme == "midnight"
    assert settings.auto_connect is False
    assert settings.minimize_to_tray is True
    assert settings.soundboard_global_volume == 100
    assert settings.update_channel == "stable"


def test_settings_ignore_retired_fields():
    settings = Settings.from_dict({"retired_setting": "retired-value"})

    assert "retired_setting" not in settings.to_dict()


def test_settings_migrate_legacy_theme_names_and_keep_new_themes():
    assert Settings.from_dict({"theme": "dark"}).theme == "midnight"
    assert Settings.from_dict({"theme": "light"}).theme == "arctic_white"
    assert Settings.from_dict({"theme": "galaxy_oled"}).theme == "galaxy_oled"


def test_launchpad_hardware_control_bindings_have_safe_defaults_and_validation():
    defaults = Settings.from_dict({}).launchpad_control_bindings
    custom = Settings.from_dict(
        {
            "launchpad_control_bindings": {
                "top_left": "next_page",
                "top_right": "not-a-binding",
                "unknown_control": "stop_all_sounds",
            }
        }
    ).launchpad_control_bindings

    assert defaults["top_left"] == "previous_page"
    assert defaults["scene_8"] == "page_8"
    assert custom["top_left"] == "next_page"
    assert custom["top_right"] == "next_page"
    assert "unknown_control" not in custom
