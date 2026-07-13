from __future__ import annotations

import sys
import time

from .base import ActionResult, BaseAction


def _utf16_code_units(text: str) -> list[int]:
    encoded = text.encode("utf-16-le")
    return [int.from_bytes(encoded[index : index + 2], "little") for index in range(0, len(encoded), 2)]


def _send_text_windows(text: str, interval: float = 0.0) -> None:
    import ctypes
    from ctypes import wintypes

    INPUT_KEYBOARD = 1
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_UNICODE = 0x0004
    unsigned_pointer = wintypes.WPARAM

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", unsigned_pointer),
        ]

    class INPUT_UNION(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT)]

    class INPUT(ctypes.Structure):
        _anonymous_ = ("union",)
        _fields_ = [("type", wintypes.DWORD), ("union", INPUT_UNION)]

    user32 = ctypes.WinDLL("user32", use_last_error=True)

    def send_units(units: list[int]) -> None:
        inputs: list[INPUT] = []
        for unit in units:
            inputs.append(INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(0, unit, KEYEVENTF_UNICODE, 0, 0)))
            inputs.append(INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(0, unit, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, 0)))
        array_type = INPUT * len(inputs)
        sent = user32.SendInput(len(inputs), array_type(*inputs), ctypes.sizeof(INPUT))
        if sent != len(inputs):
            raise RuntimeError(f"SendInput sent {sent} of {len(inputs)} text events.")

    code_units = _utf16_code_units(text)
    if interval > 0:
        for unit in code_units:
            send_units([unit])
            time.sleep(interval)
        return
    for index in range(0, len(code_units), 128):
        send_units(code_units[index : index + 128])


class TypeTextAction(BaseAction):
    type_name = "type_text"
    display_name = "Type Text"
    description = "Type configured text."
    config_fields = [
        {"name": "text", "label": "Text", "type": "multiline"},
        {"name": "interval", "label": "Interval", "type": "number"},
    ]
    blocking = True

    def execute(self, context, config: dict) -> ActionResult:
        text = str(config.get("text") or "")
        if not text:
            return ActionResult.fail("Text is empty.")
        try:
            interval = max(0.0, float(config.get("interval", 0.0) or 0.0))
        except (TypeError, ValueError):
            return ActionResult.fail("Text interval must be a number.")
        try:
            if sys.platform == "win32":
                _send_text_windows(text, interval)
            else:
                import pyautogui

                pyautogui.write(text, interval=interval)
        except Exception as exc:
            return ActionResult.fail(f"Text entry failed: {exc}")
        return ActionResult.ok("Text typed.")
