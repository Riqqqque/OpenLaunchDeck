from __future__ import annotations

import webbrowser
from pathlib import Path

from PySide6.QtCore import QObject, QThread, QTimer, Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from ..paths import UPDATES_DIR
from ..services.backup_service import BackupService
from ..services.update_installer import UpdateInstaller
from ..services.update_service import UpdateCheckResult, UpdateService
from ..version import APP_NAME, __version__


class UpdateCheckWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, service: UpdateService, manifest_url: str) -> None:
        super().__init__()
        self.service = service
        self.manifest_url = manifest_url

    @Slot()
    def run(self) -> None:
        try:
            manifest = self.service.fetch_manifest(self.manifest_url)
            self.finished.emit(self.service.check_manifest(manifest))
        except Exception as exc:
            self.failed.emit(str(exc))


class UpdateDownloadWorker(QObject):
    progress = Signal(int, int)
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, service: UpdateService, result: UpdateCheckResult) -> None:
        super().__init__()
        self.service = service
        self.result = result

    @Slot()
    def run(self) -> None:
        if not self.result.manifest:
            self.failed.emit("No update manifest is loaded.")
            return
        try:
            path = self.service.download(self.result.manifest, UPDATES_DIR, self.progress.emit)
            self.finished.emit(path)
        except Exception as exc:
            self.failed.emit(str(exc))


class UpdateDialog(QDialog):
    def __init__(self, settings_service, logger=None, parent=None, auto_check: bool = False) -> None:
        super().__init__(parent)
        self.settings_service = settings_service
        self.logger = logger
        self._check_thread: QThread | None = None
        self._check_worker: UpdateCheckWorker | None = None
        self._download_thread: QThread | None = None
        self._download_worker: UpdateDownloadWorker | None = None
        self._result: UpdateCheckResult | None = None
        self._installer_path: Path | None = None

        self.setWindowTitle("Check for Updates")
        self.resize(560, 380)

        layout = QVBoxLayout(self)
        self.label = QLabel("Ready to check for updates.")
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setVisible(False)

        button_row = QHBoxLayout()
        self.check_button = QPushButton("Check Now")
        self.download_button = QPushButton("Download Update")
        self.notes_button = QPushButton("View Release Notes")
        self.install_button = QPushButton("Install and Close")
        self.close_button = QPushButton("Close")
        button_row.addWidget(self.check_button)
        button_row.addWidget(self.download_button)
        button_row.addWidget(self.notes_button)
        button_row.addWidget(self.install_button)
        button_row.addWidget(self.close_button)

        layout.addWidget(self.label)
        layout.addWidget(self.output, 1)
        layout.addWidget(self.progress)
        layout.addLayout(button_row)

        self.check_button.clicked.connect(self.check)
        self.download_button.clicked.connect(self.download_update)
        self.notes_button.clicked.connect(self.open_release_notes)
        self.install_button.clicked.connect(self.install_update)
        self.close_button.clicked.connect(self.reject)
        self._update_buttons()
        if auto_check:
            QTimer.singleShot(0, self.check)

    def check(self) -> None:
        manifest_url = self.settings_service.settings.update_manifest_url.strip()
        service = UpdateService(__version__, self.logger)
        if not manifest_url:
            self.label.setText("No update manifest URL is configured.")
            self.output.setPlainText("Set an update manifest URL in Settings before checking from source or portable builds.")
            self._result = None
            self._installer_path = None
            self._update_buttons()
            return
        self._result = None
        self._installer_path = None
        self.check_button.setEnabled(False)
        self.label.setText("Checking for updates...")
        self.output.setPlainText("")
        self.progress.setVisible(False)
        self._check_thread = QThread(self)
        self._check_worker = UpdateCheckWorker(service, manifest_url)
        self._check_worker.moveToThread(self._check_thread)
        self._check_thread.started.connect(self._check_worker.run)
        self._check_worker.finished.connect(self._on_check_result)
        self._check_worker.failed.connect(self._on_check_error)
        self._check_worker.finished.connect(self._check_thread.quit)
        self._check_worker.failed.connect(self._check_thread.quit)
        self._check_thread.finished.connect(self._check_worker.deleteLater)
        self._check_thread.finished.connect(self._check_thread.deleteLater)
        self._check_thread.finished.connect(self._clear_check_worker)
        self._check_thread.start()

    def download_update(self) -> None:
        if not self._result or not self._result.manifest:
            return
        service = UpdateService(__version__, self.logger)
        self.download_button.setEnabled(False)
        self.install_button.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.label.setText("Downloading update...")
        self._download_thread = QThread(self)
        self._download_worker = UpdateDownloadWorker(service, self._result)
        self._download_worker.moveToThread(self._download_thread)
        self._download_thread.started.connect(self._download_worker.run)
        self._download_worker.progress.connect(self._on_download_progress)
        self._download_worker.finished.connect(self._on_download_finished)
        self._download_worker.failed.connect(self._on_download_error)
        self._download_worker.finished.connect(self._download_thread.quit)
        self._download_worker.failed.connect(self._download_thread.quit)
        self._download_thread.finished.connect(self._download_worker.deleteLater)
        self._download_thread.finished.connect(self._download_thread.deleteLater)
        self._download_thread.finished.connect(self._clear_download_worker)
        self._download_thread.start()

    def open_release_notes(self) -> None:
        if self._result and self._result.release_notes_url:
            webbrowser.open(self._result.release_notes_url)

    def install_update(self) -> None:
        if not self._installer_path:
            return
        answer = QMessageBox.question(
            self,
            "Install Update",
            f"Launch the verified installer now? {APP_NAME} will close after the installer starts.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        if self.settings_service.settings.backup_profiles_automatically:
            try:
                backup_path = BackupService().backup_profiles()
                self._append_output(f"Profiles backed up to: {backup_path}")
            except Exception as exc:
                if self.logger:
                    self.logger.exception("Profile backup before update failed.")
                QMessageBox.warning(self, APP_NAME, f"Profile backup failed:\n{exc}")
                return

        installer = UpdateInstaller(self.logger)
        try:
            launched = installer.launch(self._installer_path)
        except Exception as exc:
            if self.logger:
                self.logger.exception("Update installer launch failed.")
            QMessageBox.warning(self, APP_NAME, f"Could not launch installer:\n{exc}")
            return

        if not launched:
            QMessageBox.information(
                self,
                APP_NAME,
                "Automatic installer launch is not available for this run mode. Use the downloaded installer manually.",
            )
            return

        parent = self.parent()
        if hasattr(parent, "quit_app"):
            parent.quit_app()
        else:
            app = QApplication.instance()
            if app:
                app.quit()

    def _on_check_result(self, result: UpdateCheckResult) -> None:
        self._result = result
        self._installer_path = None
        self.label.setText(result.message)
        self.output.setPlainText(self._format_result(result))
        self.check_button.setEnabled(True)
        self._update_buttons()

    def _on_check_error(self, message: str) -> None:
        if self.logger:
            self.logger.warning("Update check failed: %s", message)
        self._result = None
        self._installer_path = None
        self.label.setText("Update check failed.")
        self.output.setPlainText(message)
        self.check_button.setEnabled(True)
        self._update_buttons()

    def _on_download_progress(self, downloaded: int, total: int) -> None:
        if total > 0:
            self.progress.setRange(0, 100)
            self.progress.setValue(min(100, int(downloaded * 100 / total)))
        else:
            self.progress.setRange(0, 0)

    def _on_download_finished(self, path: object) -> None:
        self._installer_path = Path(path)
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self.label.setText("Update downloaded and verified.")
        self._append_output(f"Installer: {self._installer_path}")
        self._update_buttons()

    def _on_download_error(self, message: str) -> None:
        if self.logger:
            self.logger.warning("Update download failed: %s", message)
        self._installer_path = None
        self.progress.setVisible(False)
        self.label.setText("Update download failed.")
        self._append_output(message)
        self._update_buttons()

    def _format_result(self, result: UpdateCheckResult) -> str:
        if not result.manifest:
            return result.message
        manifest = result.manifest
        install_mode = UpdateInstaller.install_mode()
        lines = [
            f"Current version: {result.current_version}",
            f"Latest version: {manifest.latest_version}",
            f"Minimum supported version: {manifest.minimum_supported_version}",
            f"Required: {result.required}",
            f"Unsupported current version: {result.unsupported}",
            f"Install mode: {install_mode}",
            f"Download: {manifest.download_url}",
            f"SHA256: {manifest.sha256}",
            f"Release notes: {manifest.release_notes_url}",
            f"Published: {manifest.published_at}",
        ]
        if install_mode != "installed":
            lines.append("Portable/source runs may need to run the verified installer manually.")
        return "\n".join(lines)

    def _append_output(self, text: str) -> None:
        current = self.output.toPlainText()
        self.output.setPlainText(f"{current}\n{text}".strip())

    def _update_buttons(self) -> None:
        has_result = self._result is not None and self._result.manifest is not None
        can_download = has_result and bool(self._result.available or self._result.unsupported)
        self.download_button.setEnabled(can_download and self._download_thread is None)
        self.notes_button.setEnabled(has_result and bool(self._result.release_notes_url))
        self.install_button.setEnabled(self._installer_path is not None)

    def _clear_check_worker(self) -> None:
        self._check_thread = None
        self._check_worker = None
        self.check_button.setEnabled(True)

    def _clear_download_worker(self) -> None:
        self._download_thread = None
        self._download_worker = None
        self._update_buttons()
