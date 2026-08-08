import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from openlaunchdeck.actions.registry import create_default_registry
from openlaunchdeck.ui.action_editor import ActionEditor
from openlaunchdeck.ui.action_sequence_editor import ActionSequenceEditor


def test_multi_action_sequence_editor_reorders_and_preserves_steps():
    QApplication.instance() or QApplication([])
    editor = ActionEditor(create_default_registry())
    steps = [
        {"type": "noop", "config": {}},
        {"type": "delay", "config": {"milliseconds": 250}},
    ]
    editor.set_action("multi_action", {"steps": steps, "continue_on_error": False})
    steps_editor = editor.field_widgets["steps"]
    assert isinstance(steps_editor, ActionSequenceEditor)

    steps_editor.list.setCurrentRow(1)
    steps_editor.move_step(-1)
    _, config = editor.current_action()

    assert config["steps"] == [steps[1], steps[0]]
    assert config["continue_on_error"] is False


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
