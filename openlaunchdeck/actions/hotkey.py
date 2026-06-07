from __future__ import annotations

import sys
import time

from .base import ActionResult, BaseAction


FUNCTION_KEYS = [f"f{index}" for index in range(1, 25)]
EXTENDED_FUNCTION_KEYS = [f"f{index}" for index in range(13, 25)]

COMMON_HOTKEYS = [
    "ctrl+c",
    "ctrl+v",
    "ctrl+x",
    "ctrl+z",
    "ctrl+y",
    "ctrl+s",
    "ctrl+a",
    "alt+tab",
    "alt+f4",
    "win+shift+s",
    "win+l",
]

STREAMING_HOTKEY_PREFIXES = [
    "",
    "ctrl+",
    "shift+",
    "alt+",
    "ctrl+shift+",
    "ctrl+alt+",
    "alt+shift+",
    "ctrl+alt+shift+",
]

VK_CODES: dict[str, int] = {
    "backspace": 0x08,
    "tab": 0x09,
    "enter": 0x0D,
    "return": 0x0D,
    "shift": 0x10,
    "ctrl": 0x11,
    "control": 0x11,
    "alt": 0x12,
    "pause": 0x13,
    "capslock": 0x14,
    "caps_lock": 0x14,
    "escape": 0x1B,
    "esc": 0x1B,
    "space": 0x20,
    "pageup": 0x21,
    "page_up": 0x21,
    "pagedown": 0x22,
    "page_down": 0x22,
    "end": 0x23,
    "home": 0x24,
    "left": 0x25,
    "up": 0x26,
    "right": 0x27,
    "down": 0x28,
    "printscreen": 0x2C,
    "print_screen": 0x2C,
    "prtsc": 0x2C,
    "insert": 0x2D,
    "ins": 0x2D,
    "delete": 0x2E,
    "del": 0x2E,
    "win": 0x5B,
    "windows": 0x5B,
    "cmd": 0x5B,
    "lwin": 0x5B,
    "rwin": 0x5C,
    "apps": 0x5D,
    "menu": 0x5D,
    "numlock": 0x90,
    "num_lock": 0x90,
    "scrolllock": 0x91,
    "scroll_lock": 0x91,
    "volume_mute": 0xAD,
    "volume_down": 0xAE,
    "volume_up": 0xAF,
    "media_next": 0xB0,
    "media_previous": 0xB1,
    "media_prev": 0xB1,
    "media_stop": 0xB2,
    "media_play_pause": 0xB3,
}

for _index in range(1, 25):
    VK_CODES[f"f{_index}"] = 0x6F + _index
for _index in range(10):
    VK_CODES[str(_index)] = 0x30 + _index
for _index, _char in enumerate("abcdefghijklmnopqrstuvwxyz"):
    VK_CODES[_char] = 0x41 + _index

KEY_ALIASES = {
    "command": "win",
    "option": "alt",
    "plus": "+",
    "pgup": "pageup",
    "pgdn": "pagedown",
    "prior": "pageup",
    "next": "pagedown",
}


def build_hotkey_suggestions() -> list[str]:
    suggestions: list[str] = []
    seen: set[str] = set()

    def add(value: str) -> None:
        if value and value not in seen:
            seen.add(value)
            suggestions.append(value)

    for hotkey in COMMON_HOTKEYS:
        add(hotkey)
    for key in FUNCTION_KEYS:
        add(key)
    for prefix in STREAMING_HOTKEY_PREFIXES:
        for key in EXTENDED_FUNCTION_KEYS:
            add(f"{prefix}{key}")
    return suggestions


def parse_hotkey(hotkey: str) -> list[str]:
    keys = [normalize_key_name(key) for key in hotkey.replace("+", ",").split(",") if key.strip()]
    return [key for key in keys if key]


def normalize_key_name(key: str) -> str:
    value = key.strip().lower().replace(" ", "_")
    return KEY_ALIASES.get(value, value)


def send_hotkey(keys: list[str]) -> str:
    if sys.platform == "win32":
        try:
            _send_hotkey_windows(keys)
            return "windows"
        except ValueError:
            raise
        except Exception:
            pass
    _send_hotkey_pyautogui(keys)
    return "pyautogui"


def _send_hotkey_pyautogui(keys: list[str]) -> None:
    try:
        import pyautogui
    except Exception as exc:
        raise RuntimeError("Keyboard automation dependency is not installed.") from exc
    pyautogui.hotkey(*keys)


def _send_hotkey_windows(keys: list[str]) -> None:
    import ctypes
    from ctypes import wintypes

    key_events = [(normalize_key_name(key), _vk_code_for_key(key)) for key in keys]
    if not key_events:
        raise ValueError("Hotkey is empty.")

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    INPUT_KEYBOARD = 1
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_SCANCODE = 0x0008
    KEYEVENTF_EXTENDEDKEY = 0x0001
    MAPVK_VK_TO_VSC = 0

    unsigned_pointer = wintypes.WPARAM

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [
            ("dx", wintypes.LONG),
            ("dy", wintypes.LONG),
            ("mouseData", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", unsigned_pointer),
        ]

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", unsigned_pointer),
        ]

    class HARDWAREINPUT(ctypes.Structure):
        _fields_ = [
            ("uMsg", wintypes.DWORD),
            ("wParamL", wintypes.WORD),
            ("wParamH", wintypes.WORD),
        ]

    class INPUT_UNION(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]

    class INPUT(ctypes.Structure):
        _anonymous_ = ("union",)
        _fields_ = [("type", wintypes.DWORD), ("union", INPUT_UNION)]

    def make_input(key: str, vk_code: int, key_up: bool = False) -> INPUT:
        scan_code = user32.MapVirtualKeyW(vk_code, MAPVK_VK_TO_VSC)
        if _should_send_virtual_key(key, scan_code):
            flags = 0
            if key_up:
                flags |= KEYEVENTF_KEYUP
            return INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(vk_code, 0, flags, 0, 0))

        flags = KEYEVENTF_SCANCODE
        if vk_code in {0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x2D, 0x2E, 0x5B, 0x5C, 0x5D}:
            flags |= KEYEVENTF_EXTENDEDKEY
        if key_up:
            flags |= KEYEVENTF_KEYUP
        return INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(0, scan_code, flags, 0, 0))

    inputs = [make_input(key, vk_code, False) for key, vk_code in key_events]
    inputs.extend(make_input(key, vk_code, True) for key, vk_code in reversed(key_events))
    array_type = INPUT * len(inputs)
    sent = user32.SendInput(len(inputs), array_type(*inputs), ctypes.sizeof(INPUT))
    if sent != len(inputs):
        raise RuntimeError(f"SendInput sent {sent} of {len(inputs)} keyboard events.")
    time.sleep(0.005)


def _vk_code_for_key(key: str) -> int:
    normalized = normalize_key_name(key)
    try:
        return VK_CODES[normalized]
    except KeyError as exc:
        raise ValueError(f"Unsupported hotkey key: {key}") from exc


def _should_send_virtual_key(key: str, scan_code: int) -> bool:
    normalized = normalize_key_name(key)
    return normalized in EXTENDED_FUNCTION_KEYS or scan_code == 0


class HotkeyAction(BaseAction):
    type_name = "hotkey"
    display_name = "Hotkey"
    description = "Send a keyboard shortcut."
    config_fields = [
        {
            "name": "hotkey",
            "label": "Hotkey",
            "type": "hotkey",
            "suggestions": build_hotkey_suggestions(),
        }
    ]
    blocking = True

    def execute(self, context, config: dict) -> ActionResult:
        hotkey = str(config.get("hotkey") or "").strip()
        if not hotkey:
            return ActionResult.fail("Hotkey is empty.")
        keys = parse_hotkey(hotkey)
        if not keys:
            return ActionResult.fail("Hotkey is empty.")
        try:
            backend = send_hotkey(keys)
        except ValueError as exc:
            return ActionResult.fail(str(exc))
        except Exception as exc:
            return ActionResult.fail(f"Hotkey failed: {exc}")
        if context.logger:
            context.logger.debug("Sent hotkey %s with %s backend.", hotkey, backend)
        return ActionResult.ok(f"Sent hotkey {hotkey}.")
