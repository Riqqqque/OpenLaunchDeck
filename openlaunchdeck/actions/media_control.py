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

WINDOWS_APP_COMMANDS = {
    "play_pause": 14,
    "next": 11,
    "previous": 12,
    "stop": 13,
    "volume_up": 10,
    "volume_down": 9,
    "mute": 8,
}


def send_media_control(control: str) -> str:
    if sys.platform == "win32":
        try:
            _send_app_command_windows(control)
            return "windows_appcommand"
        except Exception as app_command_error:
            try:
                send_hotkey([WINDOWS_MEDIA_KEYS[control]])
                return "windows_keyboard"
            except Exception as keyboard_error:
                raise RuntimeError(
                    f"Windows media command failed ({app_command_error}); "
                    f"keyboard fallback failed ({keyboard_error})."
                ) from keyboard_error

    import pyautogui

    pyautogui.press(MEDIA_KEYS[control])
    return "pyautogui"


def _send_app_command_windows(control: str, user32=None) -> None:
    import ctypes
    from ctypes import wintypes

    try:
        command = WINDOWS_APP_COMMANDS[control]
    except KeyError as exc:
        raise ValueError(f"Unknown media control: {control}") from exc

    if user32 is None:
        user32 = ctypes.WinDLL("user32", use_last_error=True)

    get_foreground_window = user32.GetForegroundWindow
    get_foreground_window.argtypes = []
    get_foreground_window.restype = wintypes.HWND
    send_notify_message = user32.SendNotifyMessageW
    send_notify_message.argtypes = [
        wintypes.HWND,
        wintypes.UINT,
        wintypes.WPARAM,
        wintypes.LPARAM,
    ]
    send_notify_message.restype = wintypes.BOOL

    target_window = get_foreground_window()
    if not target_window:
        raise RuntimeError("Windows did not report a foreground window.")

    WM_APPCOMMAND = 0x0319
    app_command_lparam = command << 16
    if not send_notify_message(target_window, WM_APPCOMMAND, target_window, app_command_lparam):
        error_code = ctypes.get_last_error()
        detail = f"Windows error {error_code}" if error_code else "Windows rejected the message"
        raise RuntimeError(detail)


class MediaControlAction(BaseAction):
    type_name = "media_control"
    display_name = "Media Control"
    description = "Send a media key."
    config_fields = [{"name": "control", "label": "Control", "type": "choice", "choices": list(MEDIA_KEYS)}]
    blocking = True
    execution_lane = "interactive"

    def execute(self, context, config: dict) -> ActionResult:
        control = str(config.get("control") or "play_pause")
        key = MEDIA_KEYS.get(control)
        if not key:
            return ActionResult.fail("Unknown media control.")
        try:
            backend = send_media_control(control)
        except Exception as exc:
            return ActionResult.fail(f"Media control failed: {exc}")
        logger = getattr(context, "logger", None)
        if logger:
            logger.debug("Sent media control %s with %s backend.", control, backend)
        return ActionResult.ok(f"Sent media control {control}.")
