from __future__ import annotations

from .base import ActionResult, BaseAction


class StopSoundAction(BaseAction):
    type_name = "stop_sound"
    display_name = "Stop Sound"
    description = "Stop sounds by button, page, or globally."
    config_fields = [
        {"name": "scope", "label": "Scope", "type": "choice", "choices": ["this_button", "current_page", "all"]},
        {"name": "fade_out_ms", "label": "Fade Out", "type": "number"},
    ]

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
        context.audio_engine.stop_all()
        return ActionResult.ok("Stopped all sounds.")
