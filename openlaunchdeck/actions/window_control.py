from __future__ import annotations

import ctypes
import os
import sys
from ctypes import wintypes

from .base import ActionResult, BaseAction
from .hotkey import send_hotkey

WINDOW_OPERATIONS = [
    ("Minimize Active Window", "minimize"),
    ("Maximize Active Window", "maximize"),
    ("Restore Active Window", "restore"),
    ("Close Active Window", "close"),
    ("Show Desktop", "show_desktop"),
]


class WindowControlAction(BaseAction):
    type_name = "window_control"
    display_name = "Window Control"
    description = "Minimize, maximize, restore, or close the active Windows app, or show the desktop."
    config_fields = [
        {
            "name": "operation",
            "label": "Operation",
            "type": "choice",
            "choices": WINDOW_OPERATIONS,
            "default": "minimize",
        }
    ]
    blocking = True
    execution_lane = "interactive"

    def validate(self, config: dict) -> list[str]:
        valid = {value for _label, value in WINDOW_OPERATIONS}
        return [] if str(config.get("operation") or "minimize") in valid else ["Choose a valid window operation."]

    def execute(self, context, config: dict) -> ActionResult:
        if sys.platform != "win32":
            return ActionResult.fail("Window control is available on Windows only.")
        operation = str(config.get("operation") or "minimize")
        if operation == "show_desktop":
            try:
                send_hotkey(["win", "d"])
            except Exception as exc:
                return ActionResult.fail(f"Could not show the desktop: {exc}")
            return ActionResult.ok("Desktop shown.")
        try:
            return _control_foreground_window(operation)
        except Exception as exc:
            return ActionResult.fail(f"Window control failed: {exc}")


def _control_foreground_window(operation: str, user32=None) -> ActionResult:
    if user32 is None:
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.GetForegroundWindow.argtypes = []
        user32.GetForegroundWindow.restype = wintypes.HWND
        user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        user32.PostMessageW.restype = wintypes.BOOL
        user32.ShowWindowAsync.argtypes = [wintypes.HWND, ctypes.c_int]
        user32.ShowWindowAsync.restype = wintypes.BOOL
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return ActionResult.fail("Windows did not report an active window.")

    if operation == "close":
        process_id = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
        if int(process_id.value) == os.getpid():
            return ActionResult.fail("OpenLaunchDeck cannot close itself through a pad action.")
        if not user32.PostMessageW(hwnd, 0x0010, 0, 0):
            return ActionResult.fail("Windows rejected the close request.")
        return ActionResult.ok("Close request sent to the active window.")

    show_commands = {"minimize": 6, "maximize": 3, "restore": 9}
    command = show_commands.get(operation)
    if command is None:
        return ActionResult.fail("Unknown window operation.")
    user32.ShowWindowAsync(hwnd, command)
    return ActionResult.ok(f"Active window {operation} request sent.")
