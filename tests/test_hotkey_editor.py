import ctypes
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QComboBox, QSpinBox

from openlaunchdeck.actions.hotkey import (
    _is_extended_vk_code,
    _send_hotkey_windows,
    _should_send_virtual_key,
    _vk_code_for_key,
    build_hotkey_suggestions,
    parse_hotkey,
)
from openlaunchdeck.actions.registry import create_default_registry
from openlaunchdeck.ui.action_editor import ActionEditor


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


def test_hotkey_editor_uses_editable_autocomplete_combo():
    app = QApplication.instance() or QApplication([])
    editor = ActionEditor(create_default_registry())

    editor.set_action("hotkey", {"hotkey": "f15"})
    widget = editor.field_widgets["hotkey"]

    assert isinstance(widget, QComboBox)
    assert widget.isEditable()
    assert widget.currentText() == "f15"
    assert widget.findText("f24") >= 0
    assert widget.findText("shift+left") >= 0
    assert "shift+left" in widget.toolTip()

    widget.setEditText("ctrl+shift+f19")

    action_type, config = editor.current_action()
    assert action_type == "hotkey"
    assert config["hotkey"] == "ctrl+shift+f19"

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
