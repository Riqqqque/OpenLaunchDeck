from __future__ import annotations

from .base import ActionResult, BaseAction
from .media_control import MEDIA_KEYS, send_media_control
from .windows_volume import create_volume_controller


VOLUME_MODES = ["volume_up", "volume_down", "set_volume", "mute", "unmute", "toggle_mute"]


class VolumeControlAction(BaseAction):
    type_name = "volume_control"
    display_name = "Volume Control"
    description = "Adjust the default Windows playback volume."
    config_fields = [
        {"name": "mode", "label": "Control", "type": "choice", "choices": VOLUME_MODES, "default": "volume_up"},
        {
            "name": "target_volume",
            "label": "Set Volume To",
            "type": "number",
            "min": 0,
            "max": 100,
            "default": 50,
            "suffix": "%",
            "visible_if": {"mode": "set_volume"},
        },
    ]
    blocking = True
    execution_lane = "interactive"

    def execute(self, context, config: dict) -> ActionResult:
        mode = str(config.get("mode") or "volume_up")
        if mode not in VOLUME_MODES:
            return ActionResult.fail("Unknown volume mode.")
        controller = create_volume_controller()
        if controller is not None:
            try:
                if mode == "volume_up":
                    controller.step_up()
                    return ActionResult.ok("Volume raised.")
                if mode == "volume_down":
                    controller.step_down()
                    return ActionResult.ok("Volume lowered.")
                if mode == "set_volume":
                    target = max(0, min(100, int(config.get("target_volume") or 0)))
                    controller.set_volume_percent(target)
                    return ActionResult.ok(f"Volume set to {target}%.")
                if mode == "mute":
                    controller.set_muted(True)
                    return ActionResult.ok("Volume muted.")
                if mode == "unmute":
                    controller.set_muted(False)
                    return ActionResult.ok("Volume unmuted.")
                muted = controller.toggle_mute()
                return ActionResult.ok("Volume muted." if muted else "Volume unmuted.")
            except Exception as exc:
                if mode not in {"volume_up", "volume_down", "toggle_mute"}:
                    return ActionResult.fail(f"Volume control failed: {exc}")

        media_key = "mute" if mode == "toggle_mute" else mode
        if MEDIA_KEYS.get(media_key) is None:
            return ActionResult.fail("Windows endpoint volume control is unavailable.")
        try:
            send_media_control(media_key)
        except Exception as exc:
            return ActionResult.fail(f"Volume control failed: {exc}")
        return ActionResult.ok(f"Volume command sent: {media_key}.")
