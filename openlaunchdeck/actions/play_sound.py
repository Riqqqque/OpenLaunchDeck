from __future__ import annotations

from pathlib import Path

from .base import ActionResult, BaseAction


class PlaySoundAction(BaseAction):
    type_name = "play_sound"
    display_name = "Play Sound"
    description = "Play a local sound file."
    config_fields = [
        {"name": "file_path", "label": "Sound File", "type": "file"},
        {"name": "volume", "label": "Volume", "type": "number", "min": 0, "max": 100, "default": 80},
        {"name": "route_to_voice_chat", "label": "Route To Voice Chat", "type": "bool"},
        {"name": "loop", "label": "Loop", "type": "bool"},
        {"name": "behavior_when_already_playing", "label": "Already Playing", "type": "choice", "choices": ["restart", "overlap", "ignore", "toggle_stop"]},
        {"name": "active_color", "label": "Active Color", "type": "color"},
        {"name": "stop_on_page_change", "label": "Stop On Page Change", "type": "bool"},
    ]

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
