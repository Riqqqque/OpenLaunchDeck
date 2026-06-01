import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from openlaunchdeck.app import build_services
from openlaunchdeck.models.action_config import ActionConfig
from openlaunchdeck.models.button import ButtonConfig
from openlaunchdeck.models.page import Page
from openlaunchdeck.ui.main_window import MainWindow


def test_grid_click_selects_without_running_action():
    app = QApplication.instance() or QApplication([])
    services = build_services()
    services.settings_service.settings.first_run_complete = True
    services.settings_service.settings.auto_connect = False
    window = MainWindow(services)
    calls = []

    def fake_press(button_id, source="simulation"):
        calls.append((button_id, source))

    services.action_runner.handle_button_press = fake_press
    window.grid.button_clicked.emit("B2")
    app.processEvents()

    assert calls == []

    window.hardware_button.emit("B2", True, None)
    window.editor.test_requested.emit()
    app.processEvents()

    assert len(window.grid.cells) == 64
    assert window.grid.selected_button_id == "B2"
    assert calls.count(("B2", "simulation")) == 1
    assert ("B2", "midi") in calls

    window._force_quit = True
    window.close()
    services.action_runner.shutdown()
    services.device.close()


def test_switch_page_action_refreshes_grid_and_status():
    app = QApplication.instance() or QApplication([])
    services = build_services()
    services.settings_service.settings.first_run_complete = True
    services.settings_service.settings.auto_connect = False
    window = MainWindow(services)
    profile = services.profile_service.current_profile
    main_page = services.profile_service.current_page
    second_page = Page.blank("Second", "second")
    second_page.buttons["A1"].label = "Second A1"
    profile.pages.append(second_page)
    main_page.buttons["A1"] = ButtonConfig(
        id="A1",
        label="Next",
        color="green",
        action=ActionConfig("switch_page", {"page_id": "second"}),
    )
    window.refresh_all()

    window.editor.test_requested.emit()
    app.processEvents()

    assert services.profile_service.current_page_id == "second"
    assert window.page_status.text() == "Page: Second"
    assert "Second A1" in window.grid.cells["A1"].text()

    window._force_quit = True
    window.close()
    services.action_runner.shutdown()
    services.device.close()


def test_disabled_grid_button_stays_selectable_for_editing():
    app = QApplication.instance() or QApplication([])
    services = build_services()
    services.settings_service.settings.first_run_complete = True
    services.settings_service.settings.auto_connect = False
    window = MainWindow(services)
    page = services.profile_service.current_page
    page.buttons["A1"] = ButtonConfig.blank("A1")
    page.buttons["A1"].enabled = False

    window.grid.update_button(page, "A1", services.action_runner.dangerous_service, services.audio_engine)

    assert window.grid.cells["A1"].isEnabled()

    window._force_quit = True
    window.close()
    services.action_runner.shutdown()
    services.device.close()


def test_simulation_tooltip_and_grid_focus_mode():
    app = QApplication.instance() or QApplication([])
    services = build_services()
    services.settings_service.settings.first_run_complete = True
    services.settings_service.settings.auto_connect = False
    window = MainWindow(services)
    window.show()
    app.processEvents()

    assert "no Launchpad Mini MK3 MIDI connection is active" in window.header_mode.toolTip()
    assert window.mode_status.toolTip() == window.header_mode.toolTip()

    window.set_grid_focus_mode(True)
    app.processEvents()

    assert window.grid_focus_action.isChecked()
    assert window.grid_focus_button.text() == "Edit Layout"
    assert not window.app_header.isVisible()
    assert not window.editor_scroll.isVisible()
    assert not window.sidebar_scroll.isVisible()

    window.set_grid_focus_mode(False)
    app.processEvents()

    assert not window.grid_focus_action.isChecked()
    assert window.grid_focus_button.text() == "Focus Grid"
    assert window.app_header.isVisible()
    assert window.editor_scroll.isVisible()

    window._force_quit = True
    window.close()
    services.action_runner.shutdown()
    services.device.close()


def test_midi_debug_callbacks_only_run_when_debug_window_is_open():
    app = QApplication.instance() or QApplication([])
    services = build_services()
    services.settings_service.settings.first_run_complete = True
    services.settings_service.settings.auto_connect = False
    window = MainWindow(services)

    assert services.device.midi_in_callback is None
    assert services.device.midi_out_callback is None

    window.show_midi_debug()
    app.processEvents()

    assert services.device.midi_in_callback is not None
    assert services.device.midi_out_callback is not None

    window.midi_debug_window.close()
    app.processEvents()

    assert services.device.midi_in_callback is None
    assert services.device.midi_out_callback is None

    window._force_quit = True
    window.close()
    services.action_runner.shutdown()
    services.device.close()
