import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPlainTextEdit

from openlaunchdeck.actions.registry import create_default_registry
from openlaunchdeck.ui.action_editor import ActionEditor


def test_invalid_multi_action_json_keeps_last_valid_steps():
    QApplication.instance() or QApplication([])
    editor = ActionEditor(create_default_registry())
    steps = [{"type": "noop", "config": {}}]
    editor.set_action("multi_action", {"steps": steps, "continue_on_error": False})
    steps_editor = editor.field_widgets["steps"]
    assert isinstance(steps_editor, QPlainTextEdit)

    steps_editor.setPlainText('[{"type":')
    _, config = editor.current_action()

    assert config["steps"] == steps
    assert "invalid" in steps_editor.toolTip().lower()


def test_editor_preserves_action_fields_it_does_not_render():
    QApplication.instance() or QApplication([])
    editor = ActionEditor(create_default_registry())
    editor.set_action(
        "play_sound",
        {
            "file_path": "clip.wav",
            "volume": 80,
            "voice_chat_output_device_id": "saved-route-id",
        },
    )

    _, config = editor.current_action()

    assert config["voice_chat_output_device_id"] == "saved-route-id"
