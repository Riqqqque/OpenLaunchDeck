from __future__ import annotations

from .base import ActionResult, BaseAction


MEDIA_KEYS = {
    "play_pause": "playpause",
    "next": "nexttrack",
    "previous": "prevtrack",
    "stop": "stop",
    "volume_up": "volumeup",
    "volume_down": "volumedown",
    "mute": "volumemute",
}


class MediaControlAction(BaseAction):
    type_name = "media_control"
    display_name = "Media Control"
    description = "Send a media key."
    config_fields = [{"name": "control", "label": "Control", "type": "choice", "choices": list(MEDIA_KEYS)}]
    blocking = True

    def execute(self, context, config: dict) -> ActionResult:
        control = str(config.get("control") or "play_pause")
        key = MEDIA_KEYS.get(control)
        if not key:
            return ActionResult.fail("Unknown media control.")
        try:
            import pyautogui
            pyautogui.press(key)
        except Exception as exc:
            return ActionResult.fail(f"Media control failed: {exc}")
        return ActionResult.ok(f"Sent media control {control}.")
