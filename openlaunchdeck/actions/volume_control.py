from __future__ import annotations

from .base import ActionResult, BaseAction
from .media_control import MEDIA_KEYS


class VolumeControlAction(BaseAction):
    type_name = "volume_control"
    display_name = "Volume Control"
    description = "Adjust system volume using Windows media keys."
    config_fields = [{"name": "mode", "label": "Mode", "type": "choice", "choices": ["volume_up", "volume_down", "mute"]}]
    blocking = True

    def execute(self, context, config: dict) -> ActionResult:
        mode = str(config.get("mode") or "volume_up")
        key = MEDIA_KEYS.get(mode)
        if key is None:
            return ActionResult.fail("Unknown volume mode.")
        try:
            import pyautogui
            pyautogui.press(key)
        except Exception as exc:
            return ActionResult.fail(f"Volume control failed: {exc}")
        return ActionResult.ok(f"Volume command sent: {mode}.")
