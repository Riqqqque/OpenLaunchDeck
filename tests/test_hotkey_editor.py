import ctypes
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QComboBox, QPushButton, QSpinBox

from openlaunchdeck.actions.hotkey import (
    _is_extended_vk_code,
    _send_hotkey_windows,
    _should_send_virtual_key,
    _vk_code_for_key,
    build_hotkey_suggestions,
    parse_hotkey,
)
from openlaunchdeck.actions.registry import create_default_registry
from openlaunchdeck.ui.action_editor import ActionEditor, HotkeyPicker
from openlaunchdeck.ui.action_sequence_editor import ActionSequenceEditor


def test_hotkey_suggestions_include_extended_function_keys():
    suggestions = build_hotkey_suggestions()

    assert "f15" in suggestions
    assert "f24" in suggestions
    assert "ctrl+shift+f15" in suggestions
    assert "ctrl+alt+shift+f24" in suggestions


def test_hotkey_suggestions_include_arrow_and_regular_key_combinations():
    suggestions = build_hotkey_suggestions()

    assert "shift+left" in suggestions
    assert "shift+right" in suggestions
    assert "ctrl+alt+up" in suggestions
    assert "ctrl+shift+k" in suggestions
    assert "alt+slash" in suggestions


def test_hotkey_parser_normalizes_common_aliases():
    assert parse_hotkey("Ctrl + Shift + F14") == ["ctrl", "shift", "f14"]
    assert parse_hotkey("win+print screen") == ["win", "print_screen"]
    assert parse_hotkey("command+pgdn") == ["win", "pagedown"]
    assert parse_hotkey("control+esc") == ["ctrl", "escape"]
    assert parse_hotkey("windows+prtsc") == ["win", "printscreen"]
    assert parse_hotkey("Shift + Left Arrow") == ["shift", "left"]
    assert parse_hotkey("shift+arrow right") == ["shift", "right"]


def test_windows_vk_mapping_includes_extended_function_keys():
    assert _vk_code_for_key("f13") == 0x7C
    assert _vk_code_for_key("f14") == 0x7D
    assert _vk_code_for_key("f24") == 0x87


def test_windows_vk_mapping_includes_navigation_and_punctuation_keys():
    assert _vk_code_for_key("left arrow") == 0x25
    assert _vk_code_for_key("right") == 0x27
    assert _vk_code_for_key("slash") == 0xBF
    assert _vk_code_for_key("plus") == 0xBB


def test_navigation_keys_use_extended_windows_key_events():
    assert _is_extended_vk_code(_vk_code_for_key("left"))
    assert _is_extended_vk_code(_vk_code_for_key("right"))
    assert _is_extended_vk_code(_vk_code_for_key("up"))
    assert _is_extended_vk_code(_vk_code_for_key("down"))


def test_shift_left_builds_balanced_extended_windows_events(monkeypatch):
    events = []

    class User32Double:
        @staticmethod
        def MapVirtualKeyW(vk_code, _mode):
            return vk_code

        @staticmethod
        def SendInput(count, inputs, _input_size):
            for index in range(count):
                event = inputs[index].ki
                events.append((event.wVk, event.wScan, event.dwFlags))
            return count

    monkeypatch.setattr(ctypes, "WinDLL", lambda *_args, **_kwargs: User32Double())

    _send_hotkey_windows(["shift", "left"])

    assert events == [
        (0, 0x10, 0x0008),
        (0, 0x25, 0x0009),
        (0, 0x25, 0x000B),
        (0, 0x10, 0x000A),
    ]


def test_extended_function_keys_use_virtual_key_events():
    assert _should_send_virtual_key("f13", 100)
    assert _should_send_virtual_key("f24", 118)
    assert not _should_send_virtual_key("f12", 88)


def test_hotkey_editor_uses_modifier_picker_and_searchable_key_list():
    app = QApplication.instance() or QApplication([])
    editor = ActionEditor(create_default_registry())

    editor.set_action("hotkey", {"hotkey": "f15"})
    widget = editor.field_widgets["hotkey"]

    assert isinstance(widget, HotkeyPicker)
    assert widget.key_combo.isEditable()
    assert widget.key_combo.currentData() == "f15"
    assert widget.key_combo.findData("f24") >= 0
    assert widget.key_combo.findData("left") >= 0
    assert widget.preview.text() == "F15"

    widget.modifier_checks["ctrl"].setChecked(True)
    widget.modifier_checks["shift"].setChecked(True)
    widget.key_combo.setCurrentIndex(widget.key_combo.findData("f19"))

    action_type, config = editor.current_action()
    assert action_type == "hotkey"
    assert config["hotkey"] == "ctrl+shift+f19"

    editor.deleteLater()
    app.processEvents()


def test_hotkey_picker_handles_win_shortcuts_and_preserves_existing_custom_values():
    app = QApplication.instance() or QApplication([])
    editor = ActionEditor(create_default_registry())

    editor.set_action("hotkey", {"hotkey": "win+shift+s"})
    widget = editor.field_widgets["hotkey"]

    assert isinstance(widget, HotkeyPicker)
    assert widget.modifier_checks["win"].isChecked()
    assert widget.modifier_checks["shift"].isChecked()
    assert widget.key_combo.currentData() == "s"
    assert widget.value() == "win+shift+s"

    editor.set_action("hotkey", {"hotkey": "ctrl+a+b"})
    widget = editor.field_widgets["hotkey"]
    assert widget.value() == "ctrl+a+b"

    editor.deleteLater()
    app.processEvents()


def test_hotkey_picker_maps_search_result_labels_to_key_values():
    app = QApplication.instance() or QApplication([])
    editor = ActionEditor(create_default_registry())

    editor.set_action("hotkey", {})
    widget = editor.field_widgets["hotkey"]
    widget.key_combo.setEditText("Play / Pause")

    assert widget.value() == "media_play_pause"
    assert editor.current_action()[1]["hotkey"] == "media_play_pause"

    editor.deleteLater()
    app.processEvents()


def test_choice_fields_use_friendly_labels_without_changing_saved_values():
    app = QApplication.instance() or QApplication([])
    editor = ActionEditor(create_default_registry())

    editor.set_action("media_control", {"control": "play_pause"})
    widget = editor.field_widgets["control"]

    assert isinstance(widget, QComboBox)
    assert widget.currentText() == "Play / Pause"
    assert widget.currentData() == "play_pause"
    assert editor.current_action()[1]["control"] == "play_pause"

    editor.deleteLater()
    app.processEvents()


def test_every_bounded_action_field_uses_a_selector():
    app = QApplication.instance() or QApplication([])
    editor = ActionEditor(create_default_registry())
    editor.set_context_choices("switch_page", "page_id", [("Main", "main")])

    for action in editor.registry.all():
        editor.set_action(action.type_name, {})
        for field in action.config_fields:
            widget = editor.field_widgets[field["name"]]
            if field["type"] in {"choice", "color"}:
                assert isinstance(widget, QComboBox), (action.type_name, field["name"])
            elif field["type"] == "hotkey":
                assert isinstance(widget, HotkeyPicker), (action.type_name, field["name"])

    editor.deleteLater()
    app.processEvents()


def test_switch_page_uses_current_profile_page_choices():
    app = QApplication.instance() or QApplication([])
    editor = ActionEditor(create_default_registry())
    editor.set_context_choices("switch_page", "page_id", [("Main", "main"), ("Streaming", "streaming")])

    editor.set_action("switch_page", {"page_id": "streaming"})
    widget = editor.field_widgets["page_id"]

    assert isinstance(widget, QComboBox)
    assert widget.currentText() == "Streaming"
    assert widget.currentData() == "streaming"
    assert editor.current_action()[1]["page_id"] == "streaming"

    editor.deleteLater()
    app.processEvents()


def test_play_sound_volume_editor_uses_soundboard_bounds():
    app = QApplication.instance() or QApplication([])
    editor = ActionEditor(create_default_registry())

    editor.set_action("play_sound", {})
    widget = editor.field_widgets["volume"]

    assert isinstance(widget, QSpinBox)
    assert widget.minimum() == 0
    assert widget.maximum() == 100
    assert widget.value() == 80

    editor.set_action("play_sound", {"volume": 150})
    widget = editor.field_widgets["volume"]
    assert widget.value() == 100

    editor.deleteLater()
    app.processEvents()


def test_action_editor_hides_irrelevant_fields_and_exposes_sound_library():
    app = QApplication.instance() or QApplication([])
    editor = ActionEditor(create_default_registry())
    editor.set_action("obs_websocket", {"operation": "switch_scene"})

    assert editor.field_widgets["scene_name"].isHidden() is False
    assert editor.field_widgets["source_name"].isHidden() is True
    assert editor.field_widgets["input_name"].isHidden() is True
    operation = editor.field_widgets["operation"]
    operation.setCurrentIndex(operation.findData("toggle_input_mute"))

    assert editor.field_widgets["scene_name"].isHidden() is True
    assert editor.field_widgets["input_name"].isHidden() is False

    editor.set_action("play_sound", {})
    sound_field = editor.field_widgets["file_path"]
    library_buttons = [button for button in sound_field.findChildren(QPushButton) if button.text() == "Library"]
    assert len(library_buttons) == 1
    assert "selected soundboard output" in editor.description_label.text()

    editor.deleteLater()
    app.processEvents()


def test_multi_action_uses_visual_sequence_editor_and_preserves_steps():
    app = QApplication.instance() or QApplication([])
    editor = ActionEditor(create_default_registry())
    editor.set_action(
        "multi_action",
        {
            "steps": [
                {"type": "hotkey", "config": {"hotkey": "f15"}},
                {"type": "delay", "config": {"milliseconds": 250}},
            ]
        },
    )
    sequence = editor.field_widgets["steps"]
    assert isinstance(sequence, ActionSequenceEditor)
    assert sequence.list.count() == 2

    sequence.list.setCurrentRow(1)
    sequence.move_step(-1)
    _action_type, config = editor.current_action()

    assert [step["type"] for step in config["steps"]] == ["delay", "hotkey"]
    assert "250" in sequence.list.item(0).text()
    editor.deleteLater()
    app.processEvents()
