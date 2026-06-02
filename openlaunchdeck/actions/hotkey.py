from __future__ import annotations

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
            "placeholder": "Choose or type a hotkey, such as f15 or ctrl+shift+f13",
        }
    ]
    blocking = True

    def execute(self, context, config: dict) -> ActionResult:
        hotkey = str(config.get("hotkey") or "").strip()
        if not hotkey:
            return ActionResult.fail("Hotkey is empty.")
        try:
            import pyautogui
        except Exception:
            return ActionResult.fail("Keyboard automation dependency is not installed.")
        keys = [key.strip().lower() for key in hotkey.replace("+", ",").split(",") if key.strip()]
        if not keys:
            return ActionResult.fail("Hotkey is empty.")
        try:
            pyautogui.hotkey(*keys)
        except Exception as exc:
            return ActionResult.fail(f"Hotkey failed: {exc}")
        return ActionResult.ok(f"Sent hotkey {hotkey}.")
