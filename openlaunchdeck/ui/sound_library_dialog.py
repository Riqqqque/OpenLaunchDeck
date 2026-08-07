from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from PySide6.QtCore import QFile, QIODevice, QTimer, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStyle,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..models.sound_library import SoundLibraryItem, SoundSearchPage
from ..paths import SOUND_LIBRARY_DIR
from ..services.sound_library_service import (
    API_KEY_URL,
    MAX_DOWNLOAD_BYTES,
    PROVIDER_TERMS_URL,
    SoundLibraryError,
    SoundLibraryService,
)
from ..version import __version__


CATEGORIES = (
    ("Custom search", ""),
    ("Reaction / meme", "meme reaction funny"),
    ("Comedy", "comedy funny cartoon"),
    ("Gaming", "gaming arcade action"),
    ("Alerts", "alert notification stream"),
    ("Transitions", "transition whoosh impact"),
    ("Crowd", "crowd cheer applause"),
    ("Animals", "animal funny"),
)
SORTS = (
    ("Most downloaded", "downloads_desc"),
    ("Newest", "created_desc"),
    ("Top rated", "rating_desc"),
    ("Best match", "score"),
)
LICENSES = (
    ("CC0 only (recommended)", "cc0"),
    ("CC0 + Attribution", "attribution"),
    ("All provider licenses", "all"),
)
DURATIONS = (
    ("Up to 5 seconds", 5),
    ("Up to 15 seconds", 15),
    ("Up to 30 seconds", 30),
    ("Up to 60 seconds", 60),
)


class SoundLibraryDialog(QDialog):
    assign_requested = Signal(str, str)

    def __init__(self, settings_service, logger=None, selected_button_provider=None, parent=None) -> None:
        super().__init__(parent)
        self.settings_service = settings_service
        self.logger = logger
        self.selected_button_provider = selected_button_provider or (lambda: "")
        self.service = SoundLibraryService(settings_service, logger)
        self._online_items: list[SoundLibraryItem] = []
        self._local_items: list[SoundLibraryItem] = []
        self._search_page = 1
        self._search_result: SoundSearchPage | None = None
        self._active_reply: QNetworkReply | None = None
        self._network_operation = ""
        self._request_timed_out = False
        self._download_item: SoundLibraryItem | None = None
        self._download_file: QFile | None = None
        self._download_part_path: Path | None = None
        self._download_and_assign = False
        self._download_failure_message = ""
        self._initial_search_started = False

        self.setWindowTitle("Sound Library")
        self.setObjectName("SoundLibraryDialog")
        self.resize(1040, 720)
        self.setMinimumSize(760, 540)
        self._build_ui()

        self.network = QNetworkAccessManager(self)
        self.request_timer = QTimer(self)
        self.request_timer.setSingleShot(True)
        self.request_timer.timeout.connect(self._network_timeout)
        self.preview_output = QAudioOutput(self)
        self.preview_output.setVolume(0.35)
        self.preview_player = QMediaPlayer(self)
        self.preview_player.setAudioOutput(self.preview_output)
        self.preview_player.errorOccurred.connect(self._preview_error)
        self.preview_player.mediaStatusChanged.connect(self._preview_status_changed)
        self.refresh_local_items()
        self._refresh_key_state()
        self._update_selection_state()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(12)

        heading_row = QHBoxLayout()
        heading = QVBoxLayout()
        title = QLabel("Sound Library")
        title.setObjectName("PanelTitle")
        subtitle = QLabel("Find, preview, and organize reusable sound effects.")
        subtitle.setObjectName("PanelHint")
        heading.addWidget(title)
        heading.addWidget(subtitle)
        heading_row.addLayout(heading)
        heading_row.addStretch(1)
        self.target_label = QLabel()
        self.target_label.setObjectName("LibraryTarget")
        heading_row.addWidget(self.target_label)
        root.addLayout(heading_row)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("SoundLibraryTabs")
        self.online_page = QWidget()
        self.local_page = QWidget()
        self.tabs.addTab(self.online_page, "Online")
        self.tabs.addTab(self.local_page, "My Library")
        self.tabs.currentChanged.connect(lambda _index: self._update_selection_state())
        root.addWidget(self.tabs, 1)

        self._build_online_page()
        self._build_local_page()

        details_frame = QFrame()
        details_frame.setObjectName("LibraryDetails")
        details_layout = QVBoxLayout(details_frame)
        details_layout.setContentsMargins(12, 10, 12, 10)
        details_layout.setSpacing(4)
        self.detail_title = QLabel("Select a sound")
        self.detail_title.setObjectName("LibraryDetailTitle")
        self.detail_text = QLabel("")
        self.detail_text.setObjectName("MutedText")
        self.detail_text.setWordWrap(True)
        details_layout.addWidget(self.detail_title)
        details_layout.addWidget(self.detail_text)
        root.addWidget(details_frame)

        preview_row = QHBoxLayout()
        preview_row.setSpacing(8)
        self.preview_button = QPushButton("Preview")
        self.stop_preview_button = QPushButton("Stop")
        self.source_button = QPushButton("View Source")
        self.copy_credit_button = QPushButton("Copy Credit")
        self.download_button = QPushButton("Download")
        self.assign_button = QPushButton("Assign to Pad")
        self.download_assign_button = QPushButton("Download & Assign")
        self.preview_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.stop_preview_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop))
        self.source_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))
        self.download_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowDown))
        self.assign_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))
        self.download_assign_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))
        for button in (
            self.preview_button,
            self.stop_preview_button,
            self.source_button,
            self.copy_credit_button,
            self.download_button,
            self.assign_button,
        ):
            button.setObjectName("SecondaryButton")
        self.download_assign_button.setObjectName("PrimaryButton")
        preview_row.addWidget(self.preview_button)
        preview_row.addWidget(self.stop_preview_button)
        preview_row.addWidget(self.source_button)
        preview_row.addWidget(self.copy_credit_button)
        preview_row.addStretch(1)
        root.addLayout(preview_row)

        assignment_row = QHBoxLayout()
        assignment_row.setSpacing(8)
        assignment_row.addStretch(1)
        assignment_row.addWidget(self.download_button)
        assignment_row.addWidget(self.assign_button)
        assignment_row.addWidget(self.download_assign_button)
        root.addLayout(assignment_row)

        status_row = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("MutedText")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setMaximumWidth(240)
        self.progress.hide()
        status_row.addWidget(self.status_label, 1)
        status_row.addWidget(self.progress)
        root.addLayout(status_row)

        self.preview_button.clicked.connect(self.preview_selected)
        self.stop_preview_button.clicked.connect(self.stop_preview)
        self.source_button.clicked.connect(self.open_selected_source)
        self.copy_credit_button.clicked.connect(self.copy_selected_credit)
        self.download_button.clicked.connect(lambda: self.download_selected(False))
        self.assign_button.clicked.connect(self.assign_selected)
        self.download_assign_button.clicked.connect(lambda: self.download_selected(True))

    def _build_online_page(self) -> None:
        layout = QVBoxLayout(self.online_page)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(10)

        key_row = QHBoxLayout()
        self.key_status = QLabel()
        self.key_status.setObjectName("ProviderStatus")
        self.key_edit = QLineEdit()
        self.key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_edit.setPlaceholderText("Freesound API key")
        self.key_edit.returnPressed.connect(self.save_api_key)
        self.save_key_button = QPushButton("Save Key")
        self.get_key_button = QPushButton("Get Key")
        self.forget_key_button = QPushButton("Forget")
        for button in (self.save_key_button, self.get_key_button, self.forget_key_button):
            button.setObjectName("SecondaryButton")
        self.save_key_button.clicked.connect(self.save_api_key)
        self.get_key_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(API_KEY_URL)))
        self.forget_key_button.clicked.connect(self.forget_api_key)
        key_row.addWidget(self.key_status)
        key_row.addWidget(self.key_edit, 1)
        key_row.addWidget(self.save_key_button)
        key_row.addWidget(self.get_key_button)
        key_row.addWidget(self.forget_key_button)
        layout.addLayout(key_row)

        search_row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search reactions, alerts, transitions...")
        self.search_edit.returnPressed.connect(lambda: self.search(1))
        self.category_combo = _combo(CATEGORIES)
        self.category_combo.setCurrentIndex(1)
        self.search_edit.setText(str(self.category_combo.currentData() or ""))
        self.sort_combo = _combo(SORTS)
        self.license_combo = _combo(LICENSES)
        self.duration_combo = _combo(DURATIONS)
        self.duration_combo.setCurrentIndex(1)
        self.search_button = QPushButton("Search")
        self.search_button.setObjectName("PrimaryButton")
        self.search_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView))
        self.search_button.clicked.connect(lambda: self.search(1))
        self.category_combo.currentIndexChanged.connect(self._category_changed)
        search_row.addWidget(self.search_edit, 1)
        search_row.addWidget(self.search_button)
        layout.addLayout(search_row)

        filter_row = QGridLayout()
        filter_row.setHorizontalSpacing(8)
        filter_row.setVerticalSpacing(8)
        filter_row.addWidget(QLabel("Category"), 0, 0)
        filter_row.addWidget(self.category_combo, 0, 1)
        filter_row.addWidget(QLabel("Sort"), 0, 2)
        filter_row.addWidget(self.sort_combo, 0, 3)
        filter_row.addWidget(QLabel("License"), 1, 0)
        filter_row.addWidget(self.license_combo, 1, 1)
        filter_row.addWidget(QLabel("Length"), 1, 2)
        filter_row.addWidget(self.duration_combo, 1, 3)
        filter_row.setColumnStretch(1, 1)
        filter_row.setColumnStretch(3, 1)
        layout.addLayout(filter_row)

        self.online_table = self._create_table(("Sound", "Creator", "Length", "License", "Downloads", "Rating"))
        self.online_table.itemSelectionChanged.connect(self._update_selection_state)
        self.online_table.itemDoubleClicked.connect(lambda _item: self.preview_selected())
        layout.addWidget(self.online_table, 1)

        paging_row = QHBoxLayout()
        self.previous_button = QPushButton("Previous")
        self.next_button = QPushButton("Next")
        self.page_label = QLabel("Page 1")
        self.page_label.setObjectName("MutedText")
        self.terms_button = QPushButton("Provider Terms")
        for button in (self.previous_button, self.next_button, self.terms_button):
            button.setObjectName("SecondaryButton")
        self.previous_button.clicked.connect(lambda: self.search(max(1, self._search_page - 1)))
        self.next_button.clicked.connect(lambda: self.search(self._search_page + 1))
        self.terms_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(PROVIDER_TERMS_URL)))
        paging_row.addWidget(self.previous_button)
        paging_row.addWidget(self.next_button)
        paging_row.addWidget(self.page_label)
        paging_row.addStretch(1)
        paging_row.addWidget(QLabel("Results provided by Freesound"))
        paging_row.addWidget(self.terms_button)
        layout.addLayout(paging_row)

    def _build_local_page(self) -> None:
        layout = QVBoxLayout(self.local_page)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(10)
        toolbar = QHBoxLayout()
        self.import_button = QPushButton("Import Local Sound")
        self.refresh_local_button = QPushButton("Refresh")
        self.open_folder_button = QPushButton("Open Folder")
        self.import_button.setObjectName("PrimaryButton")
        self.refresh_local_button.setObjectName("SecondaryButton")
        self.open_folder_button.setObjectName("SecondaryButton")
        self.import_button.clicked.connect(self.import_local_sound)
        self.refresh_local_button.clicked.connect(self.refresh_local_items)
        self.open_folder_button.clicked.connect(lambda: _open_folder(SOUND_LIBRARY_DIR))
        toolbar.addWidget(self.import_button)
        toolbar.addWidget(self.refresh_local_button)
        toolbar.addStretch(1)
        toolbar.addWidget(self.open_folder_button)
        layout.addLayout(toolbar)
        self.local_table = self._create_table(("Sound", "Creator", "Source", "License"))
        self.local_table.itemSelectionChanged.connect(self._update_selection_state)
        self.local_table.itemDoubleClicked.connect(lambda _item: self.preview_selected())
        layout.addWidget(self.local_table, 1)

    def _create_table(self, headers: tuple[str, ...]) -> QTableWidget:
        table = QTableWidget(0, len(headers))
        table.setObjectName("SoundLibraryTable")
        table.setHorizontalHeaderLabels(headers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.verticalHeader().hide()
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        return table

    def showEvent(self, event) -> None:
        self.target_label.setText(f"Selected pad: {self.selected_button_provider() or 'none'}")
        self.refresh_local_items()
        self._refresh_key_state()
        super().showEvent(event)
        if self.service.api_key() and not self._online_items and not self._initial_search_started:
            self._initial_search_started = True
            QTimer.singleShot(0, lambda: self.search(1))

    def closeEvent(self, event) -> None:
        self.stop_preview()
        self._cancel_network_request()
        super().closeEvent(event)

    def shutdown(self) -> None:
        self.stop_preview()
        self._cancel_network_request()

    def save_api_key(self) -> None:
        try:
            self.service.save_api_key(self.key_edit.text())
        except SoundLibraryError as exc:
            QMessageBox.warning(self, "API key not saved", str(exc))
            return
        self.key_edit.clear()
        self._refresh_key_state()
        self.status_label.setText("API key saved securely for this Windows account.")
        if not self._online_items:
            self._initial_search_started = True
            QTimer.singleShot(0, lambda: self.search(1))

    def forget_api_key(self) -> None:
        try:
            self.service.forget_api_key()
        except SoundLibraryError as exc:
            QMessageBox.warning(self, "API key not removed", str(exc))
            return
        self.key_edit.clear()
        self._refresh_key_state()
        self.online_table.setRowCount(0)
        self._online_items.clear()
        self.status_label.setText("API key removed.")

    def _refresh_key_state(self) -> None:
        connected = bool(self.service.api_key())
        self.key_status.setText("API key saved" if connected else "API key required")
        self.key_status.setProperty("connected", connected)
        self.key_status.style().unpolish(self.key_status)
        self.key_status.style().polish(self.key_status)
        self.forget_key_button.setEnabled(connected)
        self.search_button.setEnabled(connected and self._active_reply is None)

    def _category_changed(self, _index: int) -> None:
        query = str(self.category_combo.currentData() or "")
        if query:
            self.search_edit.setText(query)

    def search(self, page: int) -> None:
        api_key = self.service.api_key()
        if not api_key:
            QMessageBox.information(self, "Freesound API key", "Add your Freesound API key before searching.")
            return
        if self._active_reply is not None:
            return
        query = self.search_edit.text().strip()
        url = self.service.build_search_url(
            query,
            sort=str(self.sort_combo.currentData()),
            license_filter=str(self.license_combo.currentData()),
            maximum_duration=int(self.duration_combo.currentData()),
            page=page,
        )
        request = self._request(url, api_key, 15_000)
        reply = self.network.get(request)
        self._begin_network(reply, "search", 15_000)
        reply.finished.connect(lambda reply=reply, page=page: self._finish_search(reply, page))
        self.status_label.setText("Searching...")

    def _finish_search(self, reply: QNetworkReply, page: int) -> None:
        if reply is not self._active_reply:
            reply.deleteLater()
            return
        payload = bytes(reply.readAll())
        error = self._reply_error(reply)
        self._end_network(reply)
        if error:
            self.status_label.setText(error)
            return
        try:
            result = self.service.parse_search_payload(payload, page)
        except SoundLibraryError as exc:
            self.status_label.setText(str(exc))
            return
        self._search_result = result
        self._search_page = result.page
        self._online_items = list(result.items)
        self._populate_online_table()
        self.page_label.setText(f"Page {result.page} - {result.total:,} results")
        self.previous_button.setEnabled(result.has_previous)
        self.next_button.setEnabled(result.has_next)
        self.status_label.setText(f"Loaded {len(result.items)} sounds.")

    def _populate_online_table(self) -> None:
        self.online_table.setRowCount(len(self._online_items))
        for row, item in enumerate(self._online_items):
            values = (
                item.name,
                item.creator,
                _duration_text(item.duration),
                _license_text(item.license_name),
                f"{item.downloads:,}",
                f"{item.rating:.1f}",
            )
            for column, value in enumerate(values):
                cell = QTableWidgetItem(value)
                if column == 0:
                    cell.setData(Qt.ItemDataRole.UserRole, row)
                self.online_table.setItem(row, column, cell)
        if self._online_items:
            self.online_table.selectRow(0)
        self._update_selection_state()

    def refresh_local_items(self) -> None:
        self._local_items = self.service.local_items()
        self.local_table.setRowCount(len(self._local_items))
        for row, item in enumerate(self._local_items):
            values = (item.name, item.creator, item.provider, _license_text(item.license_name))
            for column, value in enumerate(values):
                cell = QTableWidgetItem(value)
                if column == 0:
                    cell.setData(Qt.ItemDataRole.UserRole, row)
                self.local_table.setItem(row, column, cell)
        if self._local_items and self.local_table.currentRow() < 0:
            self.local_table.selectRow(0)
        self._update_selection_state()

    def selected_item(self) -> SoundLibraryItem | None:
        table = self.online_table if self.tabs.currentWidget() is self.online_page else self.local_table
        items = self._online_items if table is self.online_table else self._local_items
        row = table.currentRow()
        if row < 0:
            return None
        cell = table.item(row, 0)
        index = cell.data(Qt.ItemDataRole.UserRole) if cell is not None else None
        return items[index] if isinstance(index, int) and 0 <= index < len(items) else None

    def _update_selection_state(self) -> None:
        item = self.selected_item()
        online = self.tabs.currentWidget() is self.online_page
        local_path = Path(item.local_path) if item and item.local_path else None
        if item and online:
            local_path = self.service.existing_download(item)
        available_locally = bool(local_path and local_path.is_file())
        busy = self._active_reply is not None
        self.preview_button.setEnabled(item is not None and not busy)
        preview_player = getattr(self, "preview_player", None)
        self.stop_preview_button.setEnabled(
            bool(preview_player and preview_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState)
        )
        self.source_button.setEnabled(bool(item and item.source_url))
        self.copy_credit_button.setEnabled(item is not None)
        self.download_button.setVisible(online)
        self.download_assign_button.setVisible(online)
        self.assign_button.setVisible(not online or available_locally)
        self.download_button.setEnabled(bool(item and not available_locally and not busy))
        self.download_button.setText("Downloaded" if available_locally else "Download")
        self.download_assign_button.setEnabled(item is not None and not busy)
        self.assign_button.setEnabled(available_locally and not busy)
        if item is None:
            self.detail_title.setText("Select a sound")
            self.detail_text.clear()
            return
        self.detail_title.setText(item.name)
        details = [f"By {item.creator}", _license_text(item.license_name)]
        if item.duration:
            details.append(_duration_text(item.duration))
        if item.downloads:
            details.append(f"{item.downloads:,} downloads")
        if item.tags:
            details.append("Tags: " + ", ".join(item.tags[:8]))
        self.detail_text.setText("  |  ".join(details))

    def preview_selected(self) -> None:
        item = self.selected_item()
        if item is None:
            return
        existing_download = self.service.existing_download(item) if not item.local_path else None
        if item.local_path:
            source = QUrl.fromLocalFile(item.local_path)
        elif existing_download:
            source = QUrl.fromLocalFile(str(existing_download))
        else:
            source = QUrl(item.preview_url)
        if not source.isValid():
            self.status_label.setText("This sound does not have a usable preview.")
            return
        self.preview_player.stop()
        self.preview_player.setSource(source)
        self.preview_player.play()
        self.status_label.setText(f"Previewing {item.name}...")
        self._update_selection_state()

    def stop_preview(self) -> None:
        preview_player = getattr(self, "preview_player", None)
        if preview_player is not None:
            preview_player.stop()
        self._update_selection_state()

    def _preview_error(self, _error, error_text: str) -> None:
        self.status_label.setText(f"Preview failed: {error_text or 'unsupported audio stream'}")
        self._update_selection_state()

    def _preview_status_changed(self, status) -> None:
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.status_label.setText("Preview finished.")
        self._update_selection_state()

    def open_selected_source(self) -> None:
        item = self.selected_item()
        if item and item.source_url:
            QDesktopServices.openUrl(QUrl(item.source_url))

    def copy_selected_credit(self) -> None:
        item = self.selected_item()
        if item:
            QApplication.clipboard().setText(item.attribution)
            self.status_label.setText("Credit copied.")

    def download_selected(self, assign_after: bool) -> None:
        item = self.selected_item()
        if item is None or self.tabs.currentWidget() is not self.online_page:
            return
        existing = self.service.existing_download(item)
        if existing:
            if assign_after:
                self._emit_assignment(existing, item)
            else:
                self.status_label.setText("This sound is already in My Library.")
            return
        if self._active_reply is not None:
            return
        part_path = self.service.part_path(item)
        part_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            part_path.unlink(missing_ok=True)
        except OSError as exc:
            self.status_label.setText(f"Download could not start: {exc}")
            return
        output = QFile(str(part_path))
        if not output.open(QIODevice.OpenModeFlag.WriteOnly):
            self.status_label.setText("Download file could not be created.")
            return
        request = self._request(item.preview_url, "", 60_000)
        reply = self.network.get(request)
        self._download_item = item
        self._download_file = output
        self._download_part_path = part_path
        self._download_and_assign = assign_after
        self._download_failure_message = ""
        self._begin_network(reply, "download", 60_000)
        reply.readyRead.connect(lambda reply=reply: self._drain_download(reply))
        reply.downloadProgress.connect(self._download_progress)
        reply.finished.connect(lambda reply=reply: self._finish_download(reply))
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.show()
        self.status_label.setText(f"Downloading {item.name}...")

    def _drain_download(self, reply: QNetworkReply) -> None:
        if reply is not self._active_reply or self._download_file is None:
            return
        chunk = bytes(reply.readAll())
        if self._download_file.size() + len(chunk) > MAX_DOWNLOAD_BYTES:
            self._download_failure_message = "Download stopped because the file exceeded 25 MB."
            reply.abort()
            return
        if chunk and self._download_file.write(chunk) != len(chunk):
            self._download_failure_message = "Download stopped because the file could not be written."
            reply.abort()

    def _download_progress(self, received: int, total: int) -> None:
        if total > MAX_DOWNLOAD_BYTES:
            self._download_failure_message = "Download stopped because the file exceeded 25 MB."
            if self._active_reply is not None:
                self._active_reply.abort()
            return
        if total > 0:
            self.progress.setRange(0, 100)
            self.progress.setValue(max(0, min(100, int(received * 100 / total))))
        else:
            self.progress.setRange(0, 0)

    def _finish_download(self, reply: QNetworkReply) -> None:
        if reply is not self._active_reply:
            reply.deleteLater()
            return
        self._drain_download(reply)
        error = self._download_failure_message or self._reply_error(reply)
        content_type = str(reply.header(QNetworkRequest.KnownHeaders.ContentTypeHeader) or "").casefold()
        if not error and content_type and not content_type.startswith("audio/") and content_type != "application/octet-stream":
            error = "The sound provider did not return an audio file."
        output = self._download_file
        part_path = self._download_part_path
        item = self._download_item
        assign_after = self._download_and_assign
        if output is not None:
            output.close()
        self._end_network(reply)
        self._download_file = None
        self._download_part_path = None
        self._download_item = None
        self._download_and_assign = False
        self._download_failure_message = ""
        if error or item is None or part_path is None:
            if part_path is not None:
                part_path.unlink(missing_ok=True)
            self.status_label.setText(error or "Download did not complete.")
            return
        try:
            destination = self.service.finalize_download(item, part_path)
        except (OSError, SoundLibraryError) as exc:
            part_path.unlink(missing_ok=True)
            self.status_label.setText(f"Download could not be saved: {exc}")
            return
        self.refresh_local_items()
        self.status_label.setText(f"Saved {destination.name} to My Library.")
        if assign_after:
            self._emit_assignment(destination, item)

    def assign_selected(self) -> None:
        item = self.selected_item()
        if item is None:
            return
        path = Path(item.local_path) if item.local_path else self.service.existing_download(item)
        if path is None or not path.is_file():
            self.status_label.setText("Download the sound before assigning it.")
            return
        self._emit_assignment(path, item)

    def _emit_assignment(self, path: Path, item: SoundLibraryItem) -> None:
        button_id = self.selected_button_provider()
        if not button_id:
            self.status_label.setText("Select a Launchpad pad before assigning the sound.")
            return
        self.assign_requested.emit(str(path), item.name)
        self.target_label.setText(f"Selected pad: {button_id}")
        self.status_label.setText(f"Assigned {item.name} to {button_id}.")

    def import_local_sound(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Sound",
            "",
            "Audio files (*.wav *.mp3 *.ogg);;All files (*.*)",
        )
        if not path:
            return
        try:
            destination = self.service.import_local_file(Path(path))
        except (OSError, SoundLibraryError) as exc:
            QMessageBox.warning(self, "Sound not imported", str(exc))
            return
        self.refresh_local_items()
        self.status_label.setText(f"Imported {destination.name}.")

    def _request(self, url: str, api_key: str, timeout_ms: int) -> QNetworkRequest:
        request = QNetworkRequest(QUrl(url))
        request.setRawHeader(b"User-Agent", f"OpenLaunchDeck/{__version__}".encode("ascii"))
        request.setRawHeader(b"Accept", b"application/json, audio/mpeg;q=0.9, */*;q=0.5")
        if api_key:
            request.setRawHeader(b"Authorization", f"Token {api_key}".encode("utf-8"))
        if hasattr(request, "setTransferTimeout"):
            request.setTransferTimeout(timeout_ms)
        return request

    def _begin_network(self, reply: QNetworkReply, operation: str, timeout_ms: int) -> None:
        self._active_reply = reply
        self._network_operation = operation
        self._request_timed_out = False
        self.request_timer.start(timeout_ms)
        self._set_busy(True)

    def _end_network(self, reply: QNetworkReply) -> None:
        self.request_timer.stop()
        if self._active_reply is reply:
            self._active_reply = None
        self._network_operation = ""
        reply.deleteLater()
        self.progress.hide()
        self._set_busy(False)

    def _network_timeout(self) -> None:
        if self._active_reply is not None:
            self._request_timed_out = True
            self._active_reply.abort()

    def _cancel_network_request(self) -> None:
        reply = self._active_reply
        if reply is None:
            return
        reply.abort()
        if self._download_file is not None:
            self._download_file.close()
        if self._download_part_path is not None:
            self._download_part_path.unlink(missing_ok=True)
        self._download_file = None
        self._download_part_path = None
        self._download_item = None
        self._download_and_assign = False
        self._download_failure_message = ""
        self._end_network(reply)

    def _reply_error(self, reply: QNetworkReply) -> str:
        if self._request_timed_out:
            return "The sound provider took too long to respond."
        status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        if status == 401:
            return "The Freesound API key was not accepted."
        if status == 429:
            return "The Freesound request limit was reached. Try again later."
        if status and int(status) >= 400:
            return f"The sound provider returned HTTP {status}."
        if reply.error() != QNetworkReply.NetworkError.NoError:
            return f"Sound provider request failed: {reply.errorString()}"
        return ""

    def _set_busy(self, busy: bool) -> None:
        self.search_button.setEnabled(not busy and bool(self.service.api_key()))
        self.save_key_button.setEnabled(not busy)
        self.get_key_button.setEnabled(not busy)
        self.forget_key_button.setEnabled(not busy and bool(self.service.api_key()))
        self.previous_button.setEnabled(not busy and bool(self._search_result and self._search_result.has_previous))
        self.next_button.setEnabled(not busy and bool(self._search_result and self._search_result.has_next))
        self.import_button.setEnabled(not busy)
        self._update_selection_state()


def _combo(items: tuple[tuple[str, Any], ...]) -> QComboBox:
    combo = QComboBox()
    combo.setMaxVisibleItems(16)
    for label, value in items:
        combo.addItem(label, value)
    return combo


def _duration_text(duration: float) -> str:
    if duration <= 0:
        return "Unknown"
    if duration < 10:
        return f"{duration:.1f}s"
    return f"{duration:.0f}s"


def _license_text(license_name: str) -> str:
    normalized = license_name.casefold()
    if "creative commons 0" in normalized or normalized == "cc0":
        return "CC0"
    if "noncommercial" in normalized:
        return "Attribution-NonCommercial"
    if "attribution" in normalized:
        return "Attribution"
    return license_name


def _open_folder(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        os.startfile(str(path))  # type: ignore[attr-defined]
    else:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
