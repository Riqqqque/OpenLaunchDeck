from __future__ import annotations

from .base import ActionResult, BaseAction


class HotkeyAction(BaseAction):
    type_name = "hotkey"
    display_name = "Hotkey"
    description = "Send a keyboard shortcut."
    config_fields = [{"name": "hotkey", "label": "Hotkey", "type": "text"}]
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
