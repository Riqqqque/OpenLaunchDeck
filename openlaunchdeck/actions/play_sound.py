from __future__ import annotations

from pathlib import Path

from .base import ActionResult, BaseAction


class PlaySoundAction(BaseAction):
    type_name = "play_sound"
    display_name = "Play Sound"
    description = "Play a local sound through your selected soundboard output, with optional voice-chat routing."
    config_fields = [
        {
            "name": "file_path",
            "label": "Sound File",
            "type": "sound_file",
            "placeholder": "Choose a local WAV, MP3, or OGG file",
            "help": "WAV, MP3, and OGG files are supported when the Windows media codecs can decode them.",
        },
        {"name": "volume", "label": "Clip Volume", "type": "number", "min": 0, "max": 100, "default": 80, "suffix": "%"},
        {
            "name": "route_to_voice_chat",
            "label": "Also Send To Voice Chat",
            "type": "bool",
            "default": False,
            "help": "Requires a working voice route configured in Soundboard settings.",
        },
        {"name": "loop", "label": "Loop Until Stopped", "type": "bool", "default": False},
        {
            "name": "behavior_when_already_playing",
            "label": "When Pressed Again",
            "type": "choice",
            "choices": ["restart", "overlap", "ignore", "toggle_stop"],
            "default": "restart",
        },
        {"name": "active_color", "label": "Playing Color", "type": "color", "default": "cyan"},
        {"name": "stop_on_page_change", "label": "Stop When Page Changes", "type": "bool", "default": False},
    ]

    def validate(self, config: dict) -> list[str]:
        file_path = str(config.get("file_path") or "").strip().strip('"')
        if not file_path:
            return ["Choose a local sound file."]
        path = Path(file_path).expanduser()
        if path.suffix.casefold() not in {".wav", ".mp3", ".ogg"}:
            return ["Choose a WAV, MP3, or OGG sound file."]
        behavior = str(config.get("behavior_when_already_playing") or "restart")
        if behavior not in {"restart", "overlap", "ignore", "toggle_stop"}:
            return ["Choose a valid behavior for repeated presses."]
        return []

    def execute(self, context, config: dict) -> ActionResult:
        file_path = str(config.get("file_path") or "").strip().strip('"')
        if not file_path:
            return ActionResult.fail("Choose a sound file.")
        if not Path(file_path).exists():
            return ActionResult.fail(f"Sound file does not exist: {file_path}")
        if context.audio_engine is None:
            return ActionResult.fail("Audio engine is unavailable.")
        config = dict(config)
        config.setdefault("_page_id", context.current_page.id)
        return context.audio_engine.play_button_sound(context.button_id, config)
