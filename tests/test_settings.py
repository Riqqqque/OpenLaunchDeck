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
        }
    )

    assert settings.soundboard_voice_chat_output_device == "voice-cable"
    assert settings.soundboard_monitor_voice_chat is False
