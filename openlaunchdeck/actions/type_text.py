from __future__ import annotations

from .base import ActionResult, BaseAction


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
            import pyautogui
        except Exception:
            return ActionResult.fail("Keyboard automation dependency is not installed.")
        interval = float(config.get("interval", 0.0) or 0.0)
        try:
            pyautogui.write(text, interval=interval)
        except Exception as exc:
            return ActionResult.fail(f"Text entry failed: {exc}")
        return ActionResult.ok("Text typed.")
