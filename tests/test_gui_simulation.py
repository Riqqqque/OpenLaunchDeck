import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from openlaunchdeck.app import build_services
from openlaunchdeck.models.button import ButtonConfig
from openlaunchdeck.ui.main_window import MainWindow


def test_gui_grid_and_simulation_use_action_runner():
    app = QApplication.instance() or QApplication([])
    services = build_services()
    services.settings_service.settings.first_run_complete = True
    services.settings_service.settings.auto_connect = False
    window = MainWindow(services)
    calls = []

    def fake_press(button_id, source="simulation"):
        calls.append((button_id, source))

    services.action_runner.handle_button_press = fake_press
    window.grid.button_clicked.emit("A1")
    window.hardware_button.emit("B2", True, None)
    app.processEvents()

    assert len(window.grid.cells) == 64
    assert ("A1", "simulation") in calls
    assert ("B2", "midi") in calls

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
