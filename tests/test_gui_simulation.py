import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QSystemTrayIcon

from openlaunchdeck.actions.base import ActionResult
from openlaunchdeck.app import build_services, show_initial_window_state
from openlaunchdeck.audio.mic_bridge import MicBridgeState
from openlaunchdeck.models.action_config import ActionConfig
from openlaunchdeck.models.button import ButtonConfig
from openlaunchdeck.models.page import Page
from openlaunchdeck.ui.main_window import MainWindow


class RouteGuardBridge:
    def __init__(self) -> None:
        self.state = MicBridgeState()
        self.started_with = []
        self.stopped = False

    def start(self, input_device_id: str, output_device_id: str, volume: int = 100):
        self.started_with.append((input_device_id, output_device_id, volume))
        self.state = MicBridgeState(
            running=True,
            input_id=input_device_id,
            input_name="Mic",
            output_id=output_device_id,
            output_name="Voice route",
            message="Microphone route is on.",
        )
        return ActionResult.ok("Microphone route is on.")

    def stop(self) -> None:
        self.stopped = True
        self.state = MicBridgeState()

    def set_volume(self, volume: int) -> None:
        pass


class StartupWindowDouble:
    def __init__(self, keep_running: bool) -> None:
        self.keep_running = keep_running
        self.calls: list[str] = []

    def should_keep_running_in_background(self) -> bool:
        return self.keep_running

    def show(self) -> None:
        self.calls.append("show")

    def hide(self) -> None:
        self.calls.append("hide")

    def showMinimized(self) -> None:
        self.calls.append("showMinimized")


def test_initial_window_state_skips_full_show_when_starting_in_background():
    window = StartupWindowDouble(keep_running=True)

    show_initial_window_state(window, start_minimized=True)

    assert window.calls == ["hide"]


def test_initial_window_state_minimizes_when_no_background_route():
    window = StartupWindowDouble(keep_running=False)

    show_initial_window_state(window, start_minimized=True)

    assert window.calls == ["showMinimized"]


def test_initial_window_state_shows_normally_when_not_minimized():
    window = StartupWindowDouble(keep_running=True)

    show_initial_window_state(window, start_minimized=False)

    assert window.calls == ["show"]


def test_grid_click_selects_without_running_action():
    app = QApplication.instance() or QApplication([])
    services = build_services()
    services.settings_service.settings.first_run_complete = True
    services.settings_service.settings.auto_connect = False
    window = MainWindow(services)
    calls = []

    def record_press(button_id, source="simulation"):
        calls.append((button_id, source))

    services.action_runner.handle_button_press = record_press
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


def test_loading_editor_state_does_not_autosave_profile():
    QApplication.instance() or QApplication([])
    services = build_services()
    services.settings_service.settings.first_run_complete = True
    services.settings_service.settings.auto_connect = False
    saves = []
    services.profile_service.save_current = lambda: saves.append(True)

    window = MainWindow(services)
    QTest.qWait(900)

    assert saves == []
    window._force_quit = True
    window.close()
    services.action_runner.shutdown()
    services.device.close()


def test_entire_grid_cell_is_clickable_for_editing():
    app = QApplication.instance() or QApplication([])
    services = build_services()
    services.settings_service.settings.first_run_complete = True
    services.settings_service.settings.auto_connect = False
    window = MainWindow(services)
    page = services.profile_service.current_page
    page.buttons["B2"] = ButtonConfig(
        id="B2",
        label="Vol Up",
        color="yellow",
        action=ActionConfig("volume_control", {"mode": "volume_up"}),
    )
    window.refresh_all()
    window.show()
    app.processEvents()

    cell = window.grid.cells["B2"]
    points = [
        QPoint(cell.width() // 2, 5),
        QPoint(cell.width() // 2, cell.height() // 2),
        QPoint(cell.width() // 2, cell.height() - 6),
        QPoint(6, cell.height() // 2),
        QPoint(cell.width() - 7, cell.height() // 2),
    ]
    for point in points:
        window.grid.select("A1")
        window.grid.update_buttons(page, {"A1", "B2"}, services.action_runner.dangerous_service, services.audio_engine)
        QTest.mouseClick(cell, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point)
        app.processEvents()
        assert window.grid.selected_button_id == "B2"

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
    QApplication.instance() or QApplication([])
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


def test_button_editor_remains_accessible_in_narrow_window():
    app = QApplication.instance() or QApplication([])
    services = build_services()
    services.settings_service.settings.first_run_complete = True
    services.settings_service.settings.auto_connect = False
    window = MainWindow(services)
    page = services.profile_service.current_page
    page.buttons["A1"] = ButtonConfig(
        id="A1",
        label="Long Sound",
        color="purple",
        action=ActionConfig(
            "play_sound",
            {
                "file_path": r"C:\Users\Example\Music\soundboard\very-long-folder-name\very-long-file-name.mp3",
                "volume": 80,
            },
        ),
    )
    window.resize(980, 640)
    window.refresh_all()
    window.show()
    app.processEvents()

    window.select_button("A1")
    app.processEvents()

    for width in (980, 1180):
        window.resize(width, 640)
        app.processEvents()

        assert window.editor_scroll.isVisible()
        assert window.workspace_splitter.orientation() == Qt.Orientation.Horizontal
        assert window.editor_scroll.viewport().width() > 0
        assert window.editor_scroll.height() >= 400
        assert window.editor_scroll.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAsNeeded
        assert window.editor_scroll.geometry().right() <= window.workspace_splitter.contentsRect().right()
        assert window.editor.action_editor.width() <= window.editor_scroll.viewport().width() + 2
        file_widget = window.editor.action_editor.field_widgets["file_path"]
        assert file_widget.width() <= window.editor.action_editor.width()

    window._force_quit = True
    window.close()
    services.action_runner.shutdown()
    services.device.close()


def test_profile_autosave_batches_editor_changes(monkeypatch):
    QApplication.instance() or QApplication([])
    services = build_services()
    services.settings_service.settings.first_run_complete = True
    services.settings_service.settings.auto_connect = False
    window = MainWindow(services)
    save_calls = []
    monkeypatch.setattr(services.profile_service, "save_current", lambda: save_calls.append("save"))

    window.save_button_changes()
    window.save_button_changes()

    assert window._profile_autosave_timer.isActive()
    assert save_calls == []

    window._flush_profile_autosave()

    assert save_calls == ["save"]

    window._force_quit = True
    window.close()
    services.action_runner.shutdown()
    services.device.close()


def test_soundboard_panel_reuses_instance_and_pauses_hidden_refresh():
    app = QApplication.instance() or QApplication([])
    services = build_services()
    services.settings_service.settings.first_run_complete = True
    services.settings_service.settings.auto_connect = False
    window = MainWindow(services)

    window.show_soundboard_panel()
    app.processEvents()
    first_panel = window.soundboard_panel

    assert first_panel is not None
    assert first_panel.isVisible()
    assert first_panel.timer.isActive()

    first_panel.hide()
    app.processEvents()

    assert not first_panel.timer.isActive()

    window.show_soundboard_panel()
    app.processEvents()

    assert window.soundboard_panel is first_panel
    assert first_panel.timer.isActive()

    first_panel.hide()
    window._force_quit = True
    window.close()
    services.action_runner.shutdown()
    services.device.close()


def test_restore_from_tray_shows_hidden_window():
    app = QApplication.instance() or QApplication([])
    services = build_services()
    services.settings_service.settings.first_run_complete = True
    services.settings_service.settings.auto_connect = False
    window = MainWindow(services)
    window.show()
    app.processEvents()

    window.hide()
    app.processEvents()

    assert not window.isVisible()

    window.tray.on_activated(QSystemTrayIcon.ActivationReason.Trigger)
    app.processEvents()

    assert window.isVisible()
    assert not window.isMinimized()

    window._force_quit = True
    window.close()
    services.action_runner.shutdown()
    services.device.close()


def test_voice_route_close_hides_instead_of_quitting(monkeypatch):
    app = QApplication.instance() or QApplication([])
    services = build_services()
    services.settings_service.settings.first_run_complete = True
    services.settings_service.settings.auto_connect = False
    services.settings_service.settings.minimize_to_tray = False
    services.audio_engine.voice_route_microphone_enabled = True
    window = MainWindow(services)
    window.show()
    app.processEvents()
    monkeypatch.setattr(window, "should_keep_running_in_background", lambda: True)
    stop_calls = []
    monkeypatch.setattr(services.audio_engine, "stop_all", lambda: stop_calls.append("stop"))

    closed = window.close()
    app.processEvents()

    assert closed is False
    assert not window.isVisible()
    assert stop_calls == []

    window._force_quit = True
    window.close()
    services.action_runner.shutdown()
    services.device.close()


def test_voice_route_guard_restarts_stopped_route():
    QApplication.instance() or QApplication([])
    services = build_services()
    services.settings_service.settings.first_run_complete = True
    services.settings_service.settings.auto_connect = False
    services.audio_engine.voice_chat_output_device_id = "voice-route"
    services.audio_engine.voice_route_microphone_device_id = "mic-1"
    services.audio_engine.voice_route_microphone_volume = 70
    services.audio_engine.voice_route_microphone_enabled = True
    bridge = RouteGuardBridge()
    services.audio_engine.mic_bridge = bridge
    window = MainWindow(services)

    window.update_voice_route_guard()
    window.ensure_voice_route_running()

    assert window.voice_route_guard_timer.isActive()
    assert window.voice_route_guard_timer.interval() == 60_000
    assert bridge.started_with == [("mic-1", "voice-route", 70)]
    assert services.audio_engine.voice_route_microphone_state().running is True

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


def test_stale_midi_health_result_cannot_disconnect_new_connection(monkeypatch):
    QApplication.instance() or QApplication([])
    services = build_services()
    services.settings_service.settings.first_run_complete = True
    services.settings_service.settings.auto_connect = False
    window = MainWindow(services)
    disconnects = []
    monkeypatch.setattr(services.device, "mark_disconnected", disconnects.append)
    services.device.connected = True
    services.settings_service.settings.auto_connect = True
    window._midi_connection_epoch = 4

    window.on_device_health_result(False, "old probe failed", 3)
    window.on_device_health_result(False, "current probe failed", 4)

    assert disconnects == ["current probe failed"]

    services.settings_service.settings.auto_connect = False
    services.device.connected = False
    window._force_quit = True
    window.close()
    services.action_runner.shutdown()
    services.device.close()


def test_midi_health_result_is_ignored_after_auto_connect_is_disabled(monkeypatch):
    QApplication.instance() or QApplication([])
    services = build_services()
    services.settings_service.settings.first_run_complete = True
    services.settings_service.settings.auto_connect = False
    window = MainWindow(services)
    disconnects = []
    monkeypatch.setattr(services.device, "mark_disconnected", disconnects.append)
    services.device.connected = True

    window.on_device_health_result(False, "probe failed", window._midi_connection_epoch)

    assert disconnects == []

    services.device.connected = False
    window._force_quit = True
    window.close()
    services.action_runner.shutdown()
    services.device.close()


def test_connected_device_guard_stays_active_for_health_checks():
    QApplication.instance() or QApplication([])
    services = build_services()
    services.settings_service.settings.first_run_complete = True
    services.settings_service.settings.auto_connect = True
    services.device.connected = True
    window = MainWindow(services)

    window._schedule_device_reconnect()

    assert window.device_reconnect_timer.isActive()
    assert window.device_reconnect_timer.interval() == 10_000

    services.settings_service.settings.auto_connect = False
    services.device.connected = False
    window._force_quit = True
    window.close()
    services.action_runner.shutdown()
    services.device.close()

