import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QComboBox

from openlaunchdeck.actions.hotkey import build_hotkey_suggestions
from openlaunchdeck.actions.registry import create_default_registry
from openlaunchdeck.ui.action_editor import ActionEditor


def test_hotkey_suggestions_include_extended_function_keys():
    suggestions = build_hotkey_suggestions()

    assert "f15" in suggestions
    assert "f24" in suggestions
    assert "ctrl+shift+f15" in suggestions
    assert "ctrl+alt+shift+f24" in suggestions


def test_hotkey_editor_uses_editable_autocomplete_combo():
    app = QApplication.instance() or QApplication([])
    editor = ActionEditor(create_default_registry())

    editor.set_action("hotkey", {"hotkey": "f15"})
    widget = editor.field_widgets["hotkey"]

    assert isinstance(widget, QComboBox)
    assert widget.isEditable()
    assert widget.currentText() == "f15"
    assert widget.findText("f24") >= 0

    widget.setEditText("ctrl+shift+f19")

    action_type, config = editor.current_action()
    assert action_type == "hotkey"
    assert config["hotkey"] == "ctrl+shift+f19"

    editor.deleteLater()
    app.processEvents()
