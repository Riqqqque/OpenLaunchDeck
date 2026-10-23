import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from openlaunchdeck.models.update_manifest import UpdateManifest
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


class GitHubFallbackUpdateService(UpdateService):
    def __init__(self):
        super().__init__("0.1.0")

    def fetch_release_manifest(self, channel: str = "stable"):
        assert channel == "stable"
        return UpdateManifest.from_dict(
            {
                "latest_version": "0.2.0",
                "minimum_supported_version": "0.1.0",
                "required": False,
                "download_url": "https://example.com/OpenLaunchDeckSetup-0.2.0.exe",
                "sha256": "a" * 64,
                "release_notes_url": "https://example.com/releases/v0.2.0",
                "published_at": "2026-01-01T00:00:00Z",
            }
        )


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


def test_update_worker_uses_github_release_when_manifest_url_is_empty():
    QApplication.instance() or QApplication([])
    worker = UpdateCheckWorker(GitHubFallbackUpdateService(), "", "stable")
    results = []
    worker.finished.connect(results.append)

    worker.run()

    assert len(results) == 1
    assert results[0].available is True
    assert results[0].latest_version == "0.2.0"


def test_update_dialog_cannot_close_while_worker_is_active():
    app = QApplication.instance() or QApplication([])
    services = build_services()
    dialog = UpdateDialog(services.settings_service)
    dialog._check_thread = object()
    dialog.show()

    dialog.reject()
    app.processEvents()

    assert dialog.isVisible()
    assert "Please wait" in dialog.label.text()
    dialog._check_thread = None
    dialog.close()
    services.action_runner.shutdown()
    services.device.close()


def test_update_now_downloads_then_installs_silently_in_one_click(monkeypatch, tmp_path):
    from openlaunchdeck.services.update_service import UpdateCheckResult
    from openlaunchdeck.ui import update_dialog as dialog_module

    app = QApplication.instance() or QApplication([])
    services = build_services()
    services.settings_service.settings.backup_profiles_automatically = False
    installer = tmp_path / "OpenLaunchDeckSetup-0.2.0.exe"
    installer.write_bytes(b"MZ")
    launched = []

    class FakeDownloadWorker(dialog_module.UpdateDownloadWorker):
        def run(self):
            self.finished.emit(installer)

    monkeypatch.setattr(dialog_module, "UpdateDownloadWorker", FakeDownloadWorker)
    monkeypatch.setattr(dialog_module.UpdateInstaller, "install_mode", staticmethod(lambda: "installed"))
    monkeypatch.setattr(
        dialog_module.UpdateInstaller, "launch", lambda self, path, silent=False: launched.append((path, silent)) or True
    )

    class Parent(dialog_module.QDialog):
        quit_requested = False

        def quit_app(self):
            Parent.quit_requested = True

    parent = Parent()
    dialog = UpdateDialog(services.settings_service, parent=parent)
    manifest = GitHubFallbackUpdateService().fetch_release_manifest()
    dialog._on_check_result(
        UpdateCheckResult(True, "Update available", manifest, current_version="0.1.0", latest_version="0.2.0")
    )

    assert not dialog.update_button.isHidden()
    assert dialog.update_button.isEnabled()
    assert "0.2.0 is available" in dialog.label.text()
    dialog.update_button.click()
    deadline = __import__("time").monotonic() + 3
    while not launched and __import__("time").monotonic() < deadline:
        app.processEvents()

    assert launched == [(installer, True)]
    assert Parent.quit_requested
    services.action_runner.shutdown()
    services.device.close()


def test_silent_update_launch_relaunches_and_detaches(monkeypatch, tmp_path):
    from openlaunchdeck.services import update_installer

    installer = tmp_path / "OpenLaunchDeckSetup-9.9.9.exe"
    installer.write_bytes(b"MZ")
    calls = []
    monkeypatch.setattr(update_installer.sys, "platform", "win32")
    monkeypatch.setattr(update_installer.subprocess, "Popen", lambda command, **kwargs: calls.append((command, kwargs)))

    assert update_installer.UpdateInstaller().launch(installer, silent=True)

    command, kwargs = calls[0]
    assert command[0] == str(installer)
    assert {"/VERYSILENT", "/SUPPRESSMSGBOXES", "/CLOSEAPPLICATIONS", "/RELAUNCH=1"} <= set(command)
    assert kwargs["creationflags"] & update_installer.CREATE_BREAKAWAY_FROM_JOB


def test_installer_reopens_the_app_after_a_silent_update():
    from pathlib import Path

    script = Path("installer/openlaunchdeck.iss").read_text(encoding="utf-8")
    workflow = Path(".github/workflows/release.yml").read_text(encoding="utf-8")

    assert "Check: RelaunchAfterSilentUpdate" in script
    assert "runasoriginaluser" in script
    assert "{param:RELAUNCH|0}" in script
    assert r'"dist\installer\OpenLaunchDeckSetup.exe"' in workflow
