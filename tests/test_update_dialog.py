import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from openlaunchdeck.services.update_service import UpdateService
from openlaunchdeck.app import build_services
from openlaunchdeck.ui import main_window as main_window_module
from openlaunchdeck.ui.main_window import MainWindow
from openlaunchdeck.ui.update_dialog import UpdateCheckWorker, UpdateDialog


class FailingUpdateService(UpdateService):
    def __init__(self):
        super().__init__("0.1.0")

    def fetch_manifest(self, manifest_url: str):
        raise RuntimeError("manifest unavailable")


def test_update_worker_reports_failed_check_without_raising():
    QApplication.instance() or QApplication([])
    worker = UpdateCheckWorker(FailingUpdateService(), "https://example.invalid/update.json")
    failures = []
    worker.failed.connect(failures.append)

    worker.run()

    assert failures == ["manifest unavailable"]


def test_header_updates_button_opens_update_dialog(monkeypatch):
    app = QApplication.instance() or QApplication([])
    services = build_services()
    services.settings_service.settings.first_run_complete = True
    services.settings_service.settings.auto_connect = False
    opened = []

    class FakeUpdateDialog:
        def __init__(self, settings_service, logger=None, parent=None, auto_check=False):
            opened.append((settings_service, logger, parent, auto_check))

        def exec(self):
            opened.append("exec")
            return 0

    monkeypatch.setattr(main_window_module, "UpdateDialog", FakeUpdateDialog)

    window = MainWindow(services)
    window.header_update_button.click()
    app.processEvents()

    assert opened[-1] == "exec"
    assert opened[0][0] is services.settings_service
    assert opened[0][2] is window
    assert opened[0][3] is True

    window._force_quit = True
    window.close()
    services.action_runner.shutdown()
    services.device.close()


def test_update_dialog_auto_check_reports_missing_manifest_url():
    app = QApplication.instance() or QApplication([])
    services = build_services()
    services.settings_service.settings.update_manifest_url = ""

    dialog = UpdateDialog(services.settings_service, auto_check=True)
    app.processEvents()

    assert dialog.label.text() == "No update manifest URL is configured."
    assert "Set an update manifest URL" in dialog.output.toPlainText()

    dialog.close()
    services.action_runner.shutdown()
    services.device.close()
