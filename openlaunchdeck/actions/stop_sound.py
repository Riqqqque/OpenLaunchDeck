from __future__ import annotations

from .base import ActionResult, BaseAction


class StopSoundAction(BaseAction):
    type_name = "stop_sound"
    display_name = "Stop Sound"
    description = "Stop the sound on this pad, every sound on this page, or all soundboard playback."
    config_fields = [
        {"name": "scope", "label": "Sounds To Stop", "type": "choice", "choices": ["this_button", "current_page", "all"], "default": "all"},
    ]

    def validate(self, config: dict) -> list[str]:
        scope = str(config.get("scope") or "all")
        return [] if scope in {"this_button", "current_page", "all"} else ["Choose which sounds to stop."]

    def execute(self, context, config: dict) -> ActionResult:
        if context.audio_engine is None:
            return ActionResult.fail("Audio engine is unavailable.")
        scope = str(config.get("scope") or "all")
        if scope == "this_button":
            context.audio_engine.stop_button(context.button_id)
            return ActionResult.ok("Stopped this button sound.")
        if scope == "current_page":
            context.audio_engine.stop_page(context.current_page.id)
            return ActionResult.ok("Stopped current page sounds.")
        if scope == "all":
            context.audio_engine.stop_all()
            return ActionResult.ok("Stopped all sounds.")
        return ActionResult.fail("Choose which sounds to stop.")
