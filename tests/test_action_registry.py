import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QScrollArea

from openlaunchdeck.actions.registry import create_default_registry
from openlaunchdeck.ui.action_editor import ActionEditor


def test_default_registry_contains_default_actions():
    registry = create_default_registry()
    for action_type in [
        "noop",
        "switch_page",
        "switch_profile",
        "navigate_deck",
        "open_url",
        "open_path",
        "run_command",
        "powershell",
        "hotkey",
        "type_text",
        "clipboard",
        "window_control",
        "mouse_control",
        "media_control",
        "volume_control",
        "http_request",
        "play_sound",
        "random_sound",
        "stop_sound",
        "multi_action",
        "delay",
        "ssh_command",
        "obs_websocket",
    ]:
        assert registry.get(action_type).type_name == action_type


def test_unknown_action_falls_back_to_noop():
    registry = create_default_registry()
    assert registry.get("missing").type_name == "noop"


def test_every_registered_action_editor_fits_a_narrow_scroll_area():
    app = QApplication.instance() or QApplication([])
    registry = create_default_registry()
    editor = ActionEditor(registry)
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll.setWidget(editor)
    scroll.resize(560, 640)
    scroll.show()

    for action in registry.all():
        editor.set_action(action.type_name, {})
        app.processEvents()

        assert editor.current_action()[0] == action.type_name
        assert scroll.horizontalScrollBar().maximum() == 0, action.type_name
        for field_name, widget in editor.field_widgets.items():
            if not widget.isVisibleTo(editor):
                continue
            assert widget.width() > 0, f"{action.type_name}.{field_name}"
            assert widget.geometry().right() <= editor.contentsRect().right() + 1, (
                f"{action.type_name}.{field_name} extends past the editor"
            )

    scroll.close()
