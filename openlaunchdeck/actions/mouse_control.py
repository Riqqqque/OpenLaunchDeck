from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

from .base import ActionResult, BaseAction

MOUSE_OPERATIONS = [
    ("Left Click", "left_click"),
    ("Double Click", "double_click"),
    ("Right Click", "right_click"),
    ("Middle Click", "middle_click"),
    ("Scroll Up", "scroll_up"),
    ("Scroll Down", "scroll_down"),
]

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
WHEEL_DELTA = 120


class _MouseInput(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),
    ]


class _InputUnion(ctypes.Union):
    _fields_ = [("mi", _MouseInput)]


class _Input(ctypes.Structure):
    _anonymous_ = ("value",)
    _fields_ = [("type", wintypes.DWORD), ("value", _InputUnion)]


class MouseControlAction(BaseAction):
    type_name = "mouse_control"
    display_name = "Mouse Control"
    description = "Click or scroll at the current pointer position."
    config_fields = [
        {
            "name": "operation",
            "label": "Operation",
            "type": "choice",
            "choices": MOUSE_OPERATIONS,
            "default": "left_click",
        },
        {
            "name": "scroll_amount",
            "label": "Scroll Steps",
            "type": "number",
            "min": 1,
            "max": 100,
            "default": 3,
            "visible_if": {"operation": ["scroll_up", "scroll_down"]},
        },
    ]
    blocking = True
    execution_lane = "interactive"

    def validate(self, config: dict) -> list[str]:
        valid = {value for _label, value in MOUSE_OPERATIONS}
        return [] if str(config.get("operation") or "left_click") in valid else ["Choose a valid mouse operation."]

    def execute(self, context, config: dict) -> ActionResult:
        operation = str(config.get("operation") or "left_click")
        try:
            amount = max(1, min(100, int(config.get("scroll_amount") or 3)))
            backend = send_mouse_control(operation, amount)
        except Exception as exc:
            return ActionResult.fail(f"Mouse control failed: {exc}")
        if context.logger:
            context.logger.debug("Sent mouse control %s with %s backend.", operation, backend)
        return ActionResult.ok(operation.replace("_", " ").title() + ".")


def send_mouse_control(operation: str, scroll_amount: int = 3) -> str:
    if operation not in {value for _label, value in MOUSE_OPERATIONS}:
        raise ValueError("Unknown mouse operation.")
    if sys.platform == "win32":
        _send_mouse_windows(operation, scroll_amount)
        return "windows"

    import pyautogui

    if operation == "left_click":
        pyautogui.click(button="left", _pause=False)
    elif operation == "double_click":
        pyautogui.click(button="left", clicks=2, interval=0.08, _pause=False)
    elif operation == "right_click":
        pyautogui.click(button="right", _pause=False)
    elif operation == "middle_click":
        pyautogui.click(button="middle", _pause=False)
    else:
        pyautogui.scroll(scroll_amount if operation == "scroll_up" else -scroll_amount, _pause=False)
    return "pyautogui"


def _send_mouse_windows(operation: str, scroll_amount: int, user32=None) -> None:
    events = _mouse_events(operation, scroll_amount)
    inputs = (_Input * len(events))(
        *[
            _Input(
                type=0,
                value=_InputUnion(
                    mi=_MouseInput(
                        dx=0,
                        dy=0,
                        mouseData=ctypes.c_ulong(data).value,
                        dwFlags=flags,
                        time=0,
                        dwExtraInfo=None,
                    )
                ),
            )
            for flags, data in events
        ]
    )
    api = user32 or ctypes.WinDLL("user32", use_last_error=True)
    send_input = api.SendInput
    send_input.argtypes = [wintypes.UINT, ctypes.POINTER(_Input), ctypes.c_int]
    send_input.restype = wintypes.UINT
    sent = int(send_input(len(inputs), inputs, ctypes.sizeof(_Input)))
    if sent != len(inputs):
        error_code = ctypes.get_last_error()
        detail = f"Windows error {error_code}" if error_code else "Windows rejected the input"
        raise RuntimeError(detail)


def _mouse_events(operation: str, scroll_amount: int) -> list[tuple[int, int]]:
    click_events = {
        "left_click": [(MOUSEEVENTF_LEFTDOWN, 0), (MOUSEEVENTF_LEFTUP, 0)],
        "double_click": [
            (MOUSEEVENTF_LEFTDOWN, 0),
            (MOUSEEVENTF_LEFTUP, 0),
            (MOUSEEVENTF_LEFTDOWN, 0),
            (MOUSEEVENTF_LEFTUP, 0),
        ],
        "right_click": [(MOUSEEVENTF_RIGHTDOWN, 0), (MOUSEEVENTF_RIGHTUP, 0)],
        "middle_click": [(MOUSEEVENTF_MIDDLEDOWN, 0), (MOUSEEVENTF_MIDDLEUP, 0)],
    }
    if operation in click_events:
        return click_events[operation]
    amount = max(1, min(100, int(scroll_amount))) * WHEEL_DELTA
    if operation == "scroll_up":
        return [(MOUSEEVENTF_WHEEL, amount)]
    if operation == "scroll_down":
        return [(MOUSEEVENTF_WHEEL, -amount)]
    raise ValueError("Unknown mouse operation.")
