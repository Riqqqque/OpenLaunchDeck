from __future__ import annotations

from PySide6.QtWidgets import QApplication

from .base import ActionResult, BaseAction

CLIPBOARD_OPERATIONS = [
    ("Copy Configured Text", "copy_text"),
    ("Clear Clipboard", "clear"),
]


class ClipboardAction(BaseAction):
    type_name = "clipboard"
    display_name = "Clipboard"
    description = "Copy reusable text to the Windows clipboard or clear it."
    config_fields = [
        {
            "name": "operation",
            "label": "Operation",
            "type": "choice",
            "choices": CLIPBOARD_OPERATIONS,
            "default": "copy_text",
        },
        {
            "name": "text",
            "label": "Text",
            "type": "multiline",
            "height": 90,
            "placeholder": "Text to copy",
            "visible_if": {"operation": "copy_text"},
        },
    ]

    def validate(self, config: dict) -> list[str]:
        operation = str(config.get("operation") or "copy_text")
        if operation not in {value for _label, value in CLIPBOARD_OPERATIONS}:
            return ["Choose a valid clipboard operation."]
        if operation == "copy_text" and not str(config.get("text") or ""):
            return ["Enter text to copy."]
        return []

    def execute(self, context, config: dict) -> ActionResult:
        app = QApplication.instance()
        if app is None:
            return ActionResult.fail("The Windows clipboard is unavailable.")
        operation = str(config.get("operation") or "copy_text")
        if operation == "clear":
            app.clipboard().clear()
            return ActionResult.ok("Clipboard cleared.")
        text = str(config.get("text") or "")
        if not text:
            return ActionResult.fail("Enter text to copy.")
        app.clipboard().setText(text)
        return ActionResult.ok("Text copied to the clipboard.")
