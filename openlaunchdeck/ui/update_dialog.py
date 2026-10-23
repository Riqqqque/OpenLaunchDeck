from __future__ import annotations

import webbrowser
from pathlib import Path

from PySide6.QtCore import QObject, QThread, QTimer, Qt, Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
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

    def __init__(self, service: UpdateService, manifest_url: str = "", channel: str = "stable") -> None:
        super().__init__()
        self.service = service
        self.manifest_url = manifest_url
        self.channel = channel

    @Slot()
    def run(self) -> None:
        try:
            manifest = (
                self.service.fetch_manifest(self.manifest_url)
                if self.manifest_url
                else self.service.fetch_release_manifest(self.channel)
            )
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
    """One-click updates: check, then a single Update now button does the rest."""

    idle = Signal()

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

        self.setObjectName("UpdateDialog")
        self.setWindowTitle("Updates")
        self.resize(500, 230)
        self.setMinimumWidth(440)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(10)
        self.label = QLabel("Ready to check for updates.")
        self.label.setObjectName("SettingsTitle")
        self.label.setWordWrap(True)
        self.detail = QLabel(f"You're on {APP_NAME} {__version__}.")
        self.detail.setObjectName("SettingsDescription")
        self.detail.setWordWrap(True)
        self.detail.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setVisible(False)
        layout.addWidget(self.label)
        layout.addWidget(self.detail)
        layout.addStretch(1)
        layout.addWidget(self.progress)

        button_row = QHBoxLayout()
        button_row.setSpacing(8)
        self.notes_button = QPushButton("What's new")
        self.notes_button.setObjectName("SecondaryButton")
        self.check_button = QPushButton("Check again")
        self.check_button.setObjectName("SecondaryButton")
        self.close_button = QPushButton("Close")
        self.close_button.setObjectName("SecondaryButton")
        self.update_button = QPushButton("Update now")
        self.update_button.setObjectName("PrimaryButton")
        self.update_button.setDefault(True)
        button_row.addWidget(self.notes_button)
        button_row.addStretch(1)
        button_row.addWidget(self.check_button)
        button_row.addWidget(self.close_button)
        button_row.addWidget(self.update_button)
        layout.addLayout(button_row)

        self.check_button.clicked.connect(self.check)
        self.notes_button.clicked.connect(self.open_release_notes)
        self.update_button.clicked.connect(self.update_now)
        self.close_button.clicked.connect(self.reject)
        self._update_buttons()
        if auto_check:
            QTimer.singleShot(0, self.check)

    # Checking

    def check(self) -> None:
        if self._check_thread is not None or self._download_thread is not None:
            return
        manifest_url = self.settings_service.settings.update_manifest_url.strip()
        service = UpdateService(__version__, self.logger)
        self._result = None
        self._installer_path = None
        self.label.setText("Checking for updates…")
        self.detail.setText(f"You're on {APP_NAME} {__version__}.")
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self._check_thread = QThread(self)
        self._check_worker = UpdateCheckWorker(service, manifest_url, self.settings_service.settings.update_channel)
        self._check_worker.moveToThread(self._check_thread)
        self._check_thread.started.connect(self._check_worker.run)
        self._check_worker.finished.connect(self._on_check_result)
        self._check_worker.failed.connect(self._on_check_error)
        self._check_worker.finished.connect(self._check_thread.quit)
        self._check_worker.failed.connect(self._check_thread.quit)
        self._check_thread.finished.connect(self._check_worker.deleteLater)
        self._check_thread.finished.connect(self._check_thread.deleteLater)
        self._check_thread.finished.connect(self._clear_check_worker)
        self._update_buttons()
        self._check_thread.start()

    def _on_check_result(self, result: UpdateCheckResult) -> None:
        self._result = result
        self._installer_path = None
        self.progress.setVisible(False)
        if result.available or result.unsupported:
            self.label.setText(f"{APP_NAME} {result.latest_version} is available")
            notes = [f"You're on {result.current_version}."]
            if result.unsupported or result.required:
                notes.append("This update is required to keep using OpenLaunchDeck.")
            notes.append("Your profiles and settings stay as they are, and the app reopens by itself when it's done.")
            if UpdateInstaller.install_mode() != "installed":
                notes.append("You're running from source, so Update now opens the installer instead of updating in place.")
            self.detail.setText(" ".join(notes))
        else:
            self.label.setText("You're up to date")
            self.detail.setText(f"{APP_NAME} {result.current_version} is the latest version.")
        self._update_buttons()

    def _on_check_error(self, message: str) -> None:
        if self.logger:
            self.logger.warning("Update check failed: %s", message)
        self._result = None
        self.progress.setVisible(False)
        self.label.setText("Couldn't check for updates")
        self.detail.setText(f"{message}\nCheck your internet connection and try again.")
        self._update_buttons()

    # Updating

    def update_now(self) -> None:
        if self._download_thread is not None or not self._result or not self._result.manifest:
            return
        if self._installer_path is not None:
            self._install(self._installer_path)
            return
        service = UpdateService(__version__, self.logger)
        self.label.setText(f"Downloading {APP_NAME} {self._result.latest_version}…")
        self.detail.setText("The download is checked against its published checksum before anything installs.")
        self.progress.setVisible(True)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
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
        self._update_buttons()
        self._download_thread.start()

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
        # Install as soon as the worker thread has wound down.
        QTimer.singleShot(0, lambda: self._install(self._installer_path))

    def _on_download_error(self, message: str) -> None:
        if self.logger:
            self.logger.warning("Update download failed: %s", message)
        self._installer_path = None
        self.progress.setVisible(False)
        self.label.setText("The update couldn't be downloaded")
        self.detail.setText(f"{message}\nNothing was changed. Try again in a moment.")
        self._update_buttons()

    def _install(self, installer_path: Path | None) -> None:
        if installer_path is None:
            return
        if self._download_thread is not None:
            QTimer.singleShot(50, lambda: self._install(installer_path))
            return
        self.label.setText("Installing the update…")
        self.detail.setText(f"{APP_NAME} closes now and reopens by itself in a few seconds.")
        self.progress.setRange(0, 0)
        self._update_buttons(installing=True)
        QApplication.processEvents()
        if self.settings_service.settings.backup_profiles_automatically:
            try:
                BackupService().backup_profiles()
            except Exception as exc:
                if self.logger:
                    self.logger.exception("Profile backup before update failed.")
                self._installation_failed(f"Your profiles couldn't be backed up first, so nothing was installed.\n{exc}")
                return
        installer = UpdateInstaller(self.logger)
        silent = UpdateInstaller.install_mode() == "installed"
        try:
            launched = installer.launch(installer_path, silent=silent)
        except Exception as exc:
            if self.logger:
                self.logger.exception("Update installer launch failed.")
            self._installation_failed(f"The installer couldn't start.\n{exc}")
            return
        if not launched:
            self._installation_failed(f"Run the downloaded installer yourself:\n{installer_path}")
            return
        parent = self.parent()
        if hasattr(parent, "quit_app"):
            parent.quit_app()
        else:
            app = QApplication.instance()
            if app:
                app.quit()

    def _installation_failed(self, message: str) -> None:
        self.progress.setVisible(False)
        self.label.setText("The update didn't install")
        self.detail.setText(message)
        self._update_buttons()

    def open_release_notes(self) -> None:
        if self._result and self._result.release_notes_url:
            webbrowser.open(self._result.release_notes_url)

    # State

    def _update_buttons(self, installing: bool = False) -> None:
        busy = installing or self._has_active_worker()
        has_result = self._result is not None and self._result.manifest is not None
        can_update = has_result and bool(self._result.available or self._result.unsupported)
        self.update_button.setVisible(can_update)
        self.update_button.setEnabled(can_update and not busy)
        self.notes_button.setVisible(has_result and bool(self._result.release_notes_url))
        self.check_button.setVisible(not can_update and not busy)
        self.close_button.setEnabled(not busy)
        self.close_button.setText("Later" if can_update else "Close")

    def _clear_check_worker(self) -> None:
        self._check_thread = None
        self._check_worker = None
        self._update_buttons()
        if not self._has_active_worker():
            self.idle.emit()

    def _clear_download_worker(self) -> None:
        self._download_thread = None
        self._download_worker = None
        self._update_buttons()
        if not self._has_active_worker():
            self.idle.emit()

    def reject(self) -> None:
        if self._has_active_worker():
            self.label.setText("Please wait for the current update step to finish.")
            return
        super().reject()

    def closeEvent(self, event) -> None:
        if self._has_active_worker():
            self.label.setText("Please wait for the current update step to finish.")
            event.ignore()
            return
        super().closeEvent(event)

    def _has_active_worker(self) -> bool:
        return self._check_thread is not None or self._download_thread is not None

    def has_active_worker(self) -> bool:
        return self._has_active_worker()
