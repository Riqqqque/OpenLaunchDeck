from __future__ import annotations

import sys

from .base import ActionResult, BaseAction
from .hotkey import send_hotkey


MEDIA_KEYS = {
    "play_pause": "playpause",
    "next": "nexttrack",
    "previous": "prevtrack",
    "stop": "stop",
    "volume_up": "volumeup",
    "volume_down": "volumedown",
    "mute": "volumemute",
}

WINDOWS_MEDIA_KEYS = {
    "play_pause": "media_play_pause",
    "next": "media_next",
    "previous": "media_previous",
    "stop": "media_stop",
    "volume_up": "volume_up",
    "volume_down": "volume_down",
    "mute": "volume_mute",
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
            if sys.platform == "win32":
                send_hotkey([WINDOWS_MEDIA_KEYS[control]])
            else:
                import pyautogui

                pyautogui.press(key)
        except Exception as exc:
            return ActionResult.fail(f"Media control failed: {exc}")
        return ActionResult.ok(f"Sent media control {control}.")
