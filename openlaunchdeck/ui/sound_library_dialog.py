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
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStyle,
    QTabWidget,
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
    ("Reactions", "meme reaction funny"),
    ("Gaming", "gaming arcade action"),
    ("Stream alerts", "alert notification stream"),
    ("Transitions", "transition whoosh impact"),
    ("Crowd", "crowd cheer applause"),
    ("Comedy", "comedy funny cartoon"),
)
STARTER_CATEGORIES = ("All", "Alerts", "Gaming", "Reactions", "Stream Tools", "Transitions", "Utility")
SORTS = (
    ("Popular", "downloads_desc"),
    ("Newest", "created_desc"),
    ("Top rated", "rating_desc"),
    ("Best match", "score"),
)
LICENSES = (("CC0 only", "cc0"), ("CC0 or attribution", "attribution"), ("All licenses", "all"))
DURATIONS = (("Up to 5 seconds", 5), ("Up to 15 seconds", 15), ("Up to 30 seconds", 30), ("Up to 60 seconds", 60))
SOUND_CARD_HEIGHT = 206


class SoundCard(QFrame):
    selected = Signal(object)
    preview_requested = Signal(object)
    use_requested = Signal(object)

    def __init__(self, item: SoundLibraryItem, action_text: str, parent=None) -> None:
        super().__init__(parent)
        self.item = item
        self.setObjectName("SoundCard")
        self.setProperty("selected", False)
        self.setMinimumWidth(205)
        self.setMaximumWidth(360)
        self.setFixedHeight(SOUND_CARD_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(13, 12, 13, 12)
        layout.setSpacing(7)

        source = QLabel(item.provider)
        source.setObjectName("SoundMeta")
        title = QLabel(item.name)
        title.setObjectName("SoundTitle")
        title.setWordWrap(True)
        title.setMaximumHeight(46)
        meta_parts = []
        if item.duration:
            meta_parts.append(_duration_text(item.duration))
        if item.downloads:
            meta_parts.append(f"{item.downloads:,} uses")
        if item.rating:
            meta_parts.append(f"{item.rating:.1f} rating")
        meta = QLabel("  |  ".join(meta_parts) or "Ready to preview")
        meta.setObjectName("SoundMeta")
        license_label = QLabel(f"{item.creator}  |  {_license_text(item.license_name)}")
        license_label.setObjectName("SoundLicense")
        license_label.setWordWrap(True)
        layout.addWidget(source)
        layout.addWidget(title)
        layout.addWidget(meta)
        layout.addWidget(license_label)
        layout.addStretch(1)

        controls = QHBoxLayout()
        controls.setSpacing(6)
        self.preview_button = QPushButton("Preview")
        self.preview_button.setObjectName("SecondaryButton")
        self.preview_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.use_button = QPushButton(action_text)
        self.use_button.setObjectName("PrimaryButton")
        self.preview_button.clicked.connect(self._preview)
        self.use_button.clicked.connect(self._use)
        controls.addWidget(self.preview_button)
        controls.addWidget(self.use_button, 1)
        layout.addLayout(controls)

    def _preview(self) -> None:
        self.selected.emit(self.item)
        self.preview_requested.emit(self.item)

    def _use(self) -> None:
        self.selected.emit(self.item)
        self.use_requested.emit(self.item)

    def set_selected(self, selected: bool) -> None:
        if bool(self.property("selected")) == selected:
            return
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)


class SoundLibraryDialog(QDialog):
    assign_requested = Signal(str, str)

    def __init__(self, settings_service, logger=None, selected_button_provider=None, parent=None) -> None:
        super().__init__(parent)
        self.settings_service = settings_service
        self.logger = logger
        self.selected_button_provider = selected_button_provider or (lambda: "")
        self.service = SoundLibraryService(settings_service, logger)
        self._starter_items: list[SoundLibraryItem] = []
        self._online_items: list[SoundLibraryItem] = []
        self._local_items: list[SoundLibraryItem] = []
        self._selected_item: SoundLibraryItem | None = None
        self._selected_source = "starter"
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
        self._cards: dict[str, list[SoundCard]] = {"starter": [], "online": [], "local": []}
        self._reflow_timer = QTimer(self)
        self._reflow_timer.setSingleShot(True)
        self._reflow_timer.setInterval(90)
        self._reflow_timer.timeout.connect(self._reflow_current)

        self.setWindowTitle("Sound Library")
        self.setObjectName("SoundLibraryDialog")
        self.resize(1100, 760)
        self.setMinimumSize(720, 540)
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
        self._starter_items = self.service.ensure_starter_collection()
        self.refresh_local_items()
        self._refresh_key_state()
        self._populate_starter_cards()
        self._select_first_for_tab()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(11)

        heading_row = QHBoxLayout()
        heading = QVBoxLayout()
        title = QLabel("Sound Library")
        title.setObjectName("LibraryTitle")
        subtitle = QLabel("Preview a sound, then add it directly to the selected Launchpad pad.")
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
        self.tabs.setDocumentMode(True)
        self.starter_page = QWidget()
        self.online_page = QWidget()
        self.local_page = QWidget()
        self.tabs.addTab(self.starter_page, "Starter Sounds")
        self.tabs.addTab(self.online_page, "Online Search")
        self.tabs.addTab(self.local_page, "My Sounds")
        self.tabs.currentChanged.connect(self._tab_changed)
        root.addWidget(self.tabs, 1)

        self._build_starter_page()
        self._build_online_page()
        self._build_local_page()

        details = QFrame()
        details.setObjectName("LibraryDetails")
        details_layout = QVBoxLayout(details)
        details_layout.setContentsMargins(12, 9, 12, 9)
        details_layout.setSpacing(8)
        details_text = QVBoxLayout()
        details_text.setSpacing(2)
        self.detail_title = QLabel("Select a sound")
        self.detail_title.setObjectName("SoundTitle")
        self.detail_text = QLabel("")
        self.detail_text.setObjectName("MutedText")
        self.detail_text.setWordWrap(True)
        details_text.addWidget(self.detail_title)
        details_text.addWidget(self.detail_text)
        details_layout.addLayout(details_text)
        detail_controls = QHBoxLayout()
        detail_controls.setSpacing(7)
        self.preview_button = QPushButton("Preview")
        self.preview_button.setObjectName("SecondaryButton")
        self.preview_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.stop_preview_button = QPushButton("Stop")
        self.stop_preview_button.setObjectName("SecondaryButton")
        self.stop_preview_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop))
        self.source_button = QPushButton("Source")
        self.source_button.setObjectName("SecondaryButton")
        self.copy_credit_button = QPushButton("Copy Credit")
        self.copy_credit_button.setObjectName("SecondaryButton")
        self.assign_button = QPushButton("Use Selected")
        self.assign_button.setObjectName("PrimaryButton")
        for button in (self.preview_button, self.stop_preview_button, self.source_button, self.copy_credit_button, self.assign_button):
            detail_controls.addWidget(button)
        detail_controls.addStretch(1)
        details_layout.addLayout(detail_controls)
        root.addWidget(details)

        status_row = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("MutedText")
        self.progress = QProgressBar()
        self.progress.setMaximumWidth(240)
        self.progress.hide()
        status_row.addWidget(self.status_label, 1)
        status_row.addWidget(self.progress)
        root.addLayout(status_row)

        self.preview_button.clicked.connect(self.preview_selected)
        self.stop_preview_button.clicked.connect(self.stop_preview)
        self.source_button.clicked.connect(self.open_selected_source)
        self.copy_credit_button.clicked.connect(self.copy_selected_credit)
        self.assign_button.clicked.connect(self._use_selected)

    def _build_starter_page(self) -> None:
        layout = QVBoxLayout(self.starter_page)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(10)
        hero = QFrame()
        hero.setObjectName("LibraryHero")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(14, 10, 14, 10)
        hero_text = QVBoxLayout()
        hero_title = QLabel("OpenLaunchDeck Essentials")
        hero_title.setObjectName("SoundTitle")
        hero_note = QLabel("Original lightweight effects included with the app. No account or download is required.")
        hero_note.setObjectName("MutedText")
        hero_note.setWordWrap(True)
        hero_text.addWidget(hero_title)
        hero_text.addWidget(hero_note)
        hero_layout.addLayout(hero_text, 1)
        self.starter_category = QComboBox()
        for category in STARTER_CATEGORIES:
            self.starter_category.addItem(category, category)
        self.starter_category.currentIndexChanged.connect(self._populate_starter_cards)
        self.starter_search = QLineEdit()
        self.starter_search.setPlaceholderText("Filter sounds")
        self.starter_search.setClearButtonEnabled(True)
        self.starter_search.textChanged.connect(self._populate_starter_cards)
        hero_layout.addWidget(self.starter_category)
        hero_layout.addWidget(self.starter_search)
        layout.addWidget(hero)
        self.starter_scroll, self.starter_cards, self.starter_grid = self._make_gallery()
        layout.addWidget(self.starter_scroll, 1)

    def _build_online_page(self) -> None:
        layout = QVBoxLayout(self.online_page)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(10)

        provider = QFrame()
        provider.setObjectName("LibraryHero")
        provider_layout = QVBoxLayout(provider)
        provider_layout.setContentsMargins(14, 10, 14, 10)
        provider_header = QHBoxLayout()
        self.key_status = QLabel()
        self.key_status.setObjectName("ProviderStatus")
        provider_note = QLabel("Popular and new public sounds from Freesound. Licenses shown on every result.")
        provider_note.setObjectName("MutedText")
        provider_note.setWordWrap(True)
        self.provider_setup_button = QPushButton("Provider Setup")
        self.provider_setup_button.setObjectName("SecondaryButton")
        self.provider_setup_button.clicked.connect(self._toggle_provider_setup)
        provider_header.addWidget(self.key_status)
        provider_header.addWidget(provider_note, 1)
        provider_header.addWidget(self.provider_setup_button)
        provider_layout.addLayout(provider_header)
        self.provider_credentials = QWidget()
        credentials = QHBoxLayout(self.provider_credentials)
        credentials.setContentsMargins(0, 7, 0, 0)
        self.key_edit = QLineEdit()
        self.key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_edit.setPlaceholderText("Personal Freesound API key")
        self.key_edit.returnPressed.connect(self.save_api_key)
        self.save_key_button = QPushButton("Save Key")
        self.get_key_button = QPushButton("Get a Key")
        self.forget_key_button = QPushButton("Forget")
        for button in (self.save_key_button, self.get_key_button, self.forget_key_button):
            button.setObjectName("SecondaryButton")
        self.save_key_button.clicked.connect(self.save_api_key)
        self.get_key_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(API_KEY_URL)))
        self.forget_key_button.clicked.connect(self.forget_api_key)
        credentials.addWidget(self.key_edit, 1)
        credentials.addWidget(self.save_key_button)
        credentials.addWidget(self.get_key_button)
        credentials.addWidget(self.forget_key_button)
        provider_layout.addWidget(self.provider_credentials)
        layout.addWidget(provider)

        search_row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search reactions, alerts, transitions, game sounds...")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.returnPressed.connect(lambda: self.search(1))
        self.category_combo = _combo(CATEGORIES)
        self.category_combo.setCurrentIndex(1)
        self.search_edit.setText(str(self.category_combo.currentData() or ""))
        self.search_button = QPushButton("Search")
        self.search_button.setObjectName("PrimaryButton")
        self.search_button.clicked.connect(lambda: self.search(1))
        self.category_combo.currentIndexChanged.connect(self._category_changed)
        search_row.addWidget(self.search_edit, 1)
        search_row.addWidget(self.search_button)
        layout.addLayout(search_row)

        filters = QGridLayout()
        filters.setHorizontalSpacing(8)
        self.sort_combo = _combo(SORTS)
        self.license_combo = _combo(LICENSES)
        self.duration_combo = _combo(DURATIONS)
        self.duration_combo.setCurrentIndex(1)
        filters.addWidget(QLabel("Category"), 0, 0)
        filters.addWidget(self.category_combo, 0, 1)
        filters.addWidget(QLabel("Sort"), 0, 2)
        filters.addWidget(self.sort_combo, 0, 3)
        filters.addWidget(QLabel("License"), 1, 0)
        filters.addWidget(self.license_combo, 1, 1)
        filters.addWidget(QLabel("Length"), 1, 2)
        filters.addWidget(self.duration_combo, 1, 3)
        filters.setColumnStretch(1, 1)
        filters.setColumnStretch(3, 1)
        layout.addLayout(filters)

        self.online_scroll, self.online_cards, self.online_grid = self._make_gallery()
        layout.addWidget(self.online_scroll, 1)
        paging = QHBoxLayout()
        self.previous_button = QPushButton("Previous")
        self.next_button = QPushButton("Next")
        self.page_label = QLabel("Connect the provider to search")
        self.page_label.setObjectName("MutedText")
        self.terms_button = QPushButton("Provider Terms")
        for button in (self.previous_button, self.next_button, self.terms_button):
            button.setObjectName("SecondaryButton")
        self.previous_button.clicked.connect(lambda: self.search(max(1, self._search_page - 1)))
        self.next_button.clicked.connect(lambda: self.search(self._search_page + 1))
        self.terms_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(PROVIDER_TERMS_URL)))
        paging.addWidget(self.previous_button)
        paging.addWidget(self.next_button)
        paging.addWidget(self.page_label)
        paging.addStretch(1)
        paging.addWidget(self.terms_button)
        layout.addLayout(paging)

    def _build_local_page(self) -> None:
        layout = QVBoxLayout(self.local_page)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(10)
        toolbar = QHBoxLayout()
        self.import_button = QPushButton("Import Local Sound")
        self.import_button.setObjectName("PrimaryButton")
        self.local_search = QLineEdit()
        self.local_search.setPlaceholderText("Filter my sounds")
        self.local_search.setClearButtonEnabled(True)
        self.refresh_local_button = QPushButton("Refresh")
        self.open_folder_button = QPushButton("Open Folder")
        self.refresh_local_button.setObjectName("SecondaryButton")
        self.open_folder_button.setObjectName("SecondaryButton")
        self.import_button.clicked.connect(self.import_local_sound)
        self.local_search.textChanged.connect(self._populate_local_cards)
        self.refresh_local_button.clicked.connect(self.refresh_local_items)
        self.open_folder_button.clicked.connect(lambda: _open_folder(SOUND_LIBRARY_DIR))
        toolbar.addWidget(self.import_button)
        toolbar.addWidget(self.local_search, 1)
        toolbar.addWidget(self.refresh_local_button)
        toolbar.addWidget(self.open_folder_button)
        layout.addLayout(toolbar)
        self.local_scroll, self.local_cards, self.local_grid = self._make_gallery()
        layout.addWidget(self.local_scroll, 1)

    @staticmethod
    def _make_gallery() -> tuple[QScrollArea, QWidget, QGridLayout]:
        scroll = QScrollArea()
        scroll.setObjectName("SoundCardScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        container = QWidget()
        grid = QGridLayout(container)
        grid.setContentsMargins(2, 2, 8, 8)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        grid.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scroll.setWidget(container)
        return scroll, container, grid

    def showEvent(self, event) -> None:
        self.target_label.setText(f"Selected pad: {self.selected_button_provider() or 'none'}")
        self.refresh_local_items()
        self._refresh_key_state()
        self._populate_starter_cards()
        super().showEvent(event)
        QTimer.singleShot(0, self._reflow_current)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "starter_grid"):
            self._reflow_timer.start()

    def closeEvent(self, event) -> None:
        self.stop_preview()
        self._cancel_network_request()
        super().closeEvent(event)

    def shutdown(self) -> None:
        self.stop_preview()
        self._cancel_network_request()

    def _tab_changed(self, _index: int) -> None:
        source = self._current_source()
        items = self._items_for_source(source)
        if items:
            self._select_item(items[0], source)
        else:
            self._selected_item = None
            self._selected_source = source
            self._update_selection_state()
        if source == "online" and self.service.api_key() and not self._online_items and not self._initial_search_started:
            self._initial_search_started = True
            QTimer.singleShot(0, lambda: self.search(1))
        QTimer.singleShot(0, self._reflow_current)

    def _current_source(self) -> str:
        current = self.tabs.currentWidget()
        return "online" if current is self.online_page else "local" if current is self.local_page else "starter"

    def _items_for_source(self, source: str) -> list[SoundLibraryItem]:
        return self._online_items if source == "online" else self._local_items if source == "local" else self._starter_items

    def _select_first_for_tab(self) -> None:
        source = self._current_source()
        items = self._items_for_source(source)
        if items:
            self._select_item(items[0], source)

    def save_api_key(self) -> None:
        try:
            self.service.save_api_key(self.key_edit.text())
        except SoundLibraryError as exc:
            QMessageBox.warning(self, "API key not saved", str(exc))
            return
        self.key_edit.clear()
        self.provider_credentials.hide()
        self._refresh_key_state()
        self.status_label.setText("Online search is connected for this Windows account.")
        self._initial_search_started = True
        QTimer.singleShot(0, lambda: self.search(1))

    def forget_api_key(self) -> None:
        try:
            self.service.forget_api_key()
        except SoundLibraryError as exc:
            QMessageBox.warning(self, "API key not removed", str(exc))
            return
        self.key_edit.clear()
        self._online_items.clear()
        self._populate_online_table()
        self.provider_credentials.show()
        self._refresh_key_state()
        self.status_label.setText("Online search disconnected. Starter and local sounds are still available.")

    def _toggle_provider_setup(self) -> None:
        self.provider_credentials.setVisible(not self.provider_credentials.isVisible())

    def _refresh_key_state(self) -> None:
        connected = bool(self.service.api_key())
        self.key_status.setText("Online search connected" if connected else "Online search needs setup")
        self.key_status.setProperty("connected", connected)
        self.key_status.style().unpolish(self.key_status)
        self.key_status.style().polish(self.key_status)
        self.provider_setup_button.setText("Manage Provider" if connected else "Connect Provider")
        self.provider_credentials.setVisible(not connected)
        self.forget_key_button.setEnabled(connected)
        self.search_button.setEnabled(connected and self._active_reply is None)
        self.previous_button.setEnabled(bool(connected and self._search_result and self._search_result.has_previous))
        self.next_button.setEnabled(bool(connected and self._search_result and self._search_result.has_next))

    def _category_changed(self, _index: int) -> None:
        query = str(self.category_combo.currentData() or "")
        if query:
            self.search_edit.setText(query)

    def search(self, page: int) -> None:
        api_key = self.service.api_key()
        if not api_key:
            self.provider_credentials.show()
            self.status_label.setText("Connect online search first, or use the included Starter Sounds tab.")
            return
        if self._active_reply is not None:
            return
        url = self.service.build_search_url(
            self.search_edit.text(),
            sort=str(self.sort_combo.currentData()),
            license_filter=str(self.license_combo.currentData()),
            maximum_duration=int(self.duration_combo.currentData()),
            page=page,
        )
        reply = self.network.get(self._request(url, api_key, 15_000))
        self._begin_network(reply, "search", 15_000)
        reply.finished.connect(lambda reply=reply, page=page: self._finish_search(reply, page))
        self.status_label.setText("Searching public sounds...")

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
        self.page_label.setText(f"Page {result.page}  |  {result.total:,} results")
        self.previous_button.setEnabled(result.has_previous)
        self.next_button.setEnabled(result.has_next)
        self.status_label.setText(f"Loaded {len(result.items)} sounds.")

    def _populate_starter_cards(self, *_args) -> None:
        category = str(self.starter_category.currentData() or "All") if hasattr(self, "starter_category") else "All"
        query = self.starter_search.text().strip().casefold() if hasattr(self, "starter_search") else ""
        items = []
        for item in self._starter_items:
            haystack = " ".join((item.name, *item.tags)).casefold()
            if category != "All" and category.casefold() not in item.tags:
                continue
            if query and query not in haystack:
                continue
            items.append(item)
        self._render_cards("starter", items)

    def _populate_online_table(self) -> None:
        self._render_cards("online", self._online_items)
        if self._online_items and self.tabs.currentWidget() is self.online_page:
            self._select_item(self._online_items[0], "online")

    def _populate_local_cards(self, *_args) -> None:
        query = self.local_search.text().strip().casefold() if hasattr(self, "local_search") else ""
        items = [item for item in self._local_items if not query or query in " ".join((item.name, item.creator, item.provider, *item.tags)).casefold()]
        self._render_cards("local", items)

    def refresh_local_items(self) -> None:
        self._local_items = self.service.local_items()
        self._starter_items = [item for item in self._local_items if item.provider == "OpenLaunchDeck Essentials"]
        if hasattr(self, "local_grid"):
            self._populate_local_cards()
        if hasattr(self, "starter_grid"):
            self._populate_starter_cards()
        self._update_selection_state()

    def _render_cards(self, source: str, items: list[SoundLibraryItem]) -> None:
        grid = {"starter": self.starter_grid, "online": self.online_grid, "local": self.local_grid}[source]
        scroll = {"starter": self.starter_scroll, "online": self.online_scroll, "local": self.local_scroll}[source]
        while grid.count():
            child = grid.takeAt(0)
            widget = child.widget()
            if widget is not None:
                widget.hide()
                widget.deleteLater()
        cards: list[SoundCard] = []
        columns = self._gallery_columns(scroll)
        target = self.selected_button_provider() or "pad"
        for column in range(4):
            grid.setColumnStretch(column, 0)
        for index, item in enumerate(items):
            available = bool(item.local_path and Path(item.local_path).is_file()) or bool(source == "online" and self.service.existing_download(item))
            action = f"Use {target}" if available else "Get + Use"
            card = SoundCard(item, action)
            card.use_button.setToolTip(
                f"Assign {item.name} to {target}."
                if available
                else f"Download {item.name} to AppData, then assign it to {target}."
            )
            card.selected.connect(lambda selected, source=source: self._select_item(selected, source))
            card.preview_requested.connect(lambda selected, source=source: self._preview_item(selected, source))
            card.use_requested.connect(lambda selected, source=source: self._use_item(selected, source))
            grid.addWidget(card, index // columns, index % columns)
            cards.append(card)
        self._cards[source] = cards
        if not items:
            empty = QLabel(self._empty_message(source))
            empty.setObjectName("MutedText")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setWordWrap(True)
            grid.addWidget(empty, 0, 0, 1, columns)
        for column in range(columns):
            grid.setColumnStretch(column, 1)
        rows = max(1, (len(items) + columns - 1) // columns)
        margins = grid.contentsMargins()
        content_height = rows * SOUND_CARD_HEIGHT + max(0, rows - 1) * grid.verticalSpacing()
        scroll.widget().setMinimumHeight(content_height + margins.top() + margins.bottom())
        self._sync_card_selection()

    @staticmethod
    def _gallery_columns(scroll: QScrollArea) -> int:
        width = max(220, scroll.viewport().width() - 8)
        return max(1, min(4, width // 235))

    @staticmethod
    def _empty_message(source: str) -> str:
        if source == "online":
            return "Connect online search, then search for reactions, alerts, transitions, and other public sounds."
        if source == "local":
            return "Import a WAV, MP3, or OGG file to keep it in your sound library."
        return "The included starter collection could not be loaded. Reinstall OpenLaunchDeck to restore it."

    def _reflow_current(self) -> None:
        source = self._current_source()
        if source == "online":
            self._populate_online_table()
        elif source == "local":
            self._populate_local_cards()
        else:
            self._populate_starter_cards()

    def selected_item(self) -> SoundLibraryItem | None:
        return self._selected_item

    def _select_item(self, item: SoundLibraryItem, source: str) -> None:
        self._selected_item = item
        self._selected_source = source
        self._sync_card_selection()
        self._update_selection_state()

    def _sync_card_selection(self) -> None:
        for cards in self._cards.values():
            for card in cards:
                card.set_selected(card.item == self._selected_item)

    def _update_selection_state(self) -> None:
        item = self._selected_item
        busy = self._active_reply is not None
        available = self._local_path(item)
        preview_player = getattr(self, "preview_player", None)
        self.preview_button.setEnabled(item is not None and not busy)
        self.stop_preview_button.setEnabled(bool(preview_player and preview_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState))
        self.source_button.setEnabled(bool(item and item.source_url))
        self.copy_credit_button.setEnabled(item is not None)
        self.assign_button.setEnabled(bool(item and not busy))
        target = self.selected_button_provider() or "Pad"
        if item and self._selected_source == "online" and available is None:
            self.assign_button.setText(f"Get + Use on {target}")
        else:
            self.assign_button.setText(f"Use on {target}")
        if item is None:
            self.detail_title.setText("Select a sound")
            self.detail_text.setText("Preview and assignment controls appear here.")
            return
        self.detail_title.setText(item.name)
        details = [f"By {item.creator}", _license_text(item.license_name)]
        if item.duration:
            details.append(_duration_text(item.duration))
        if item.downloads:
            details.append(f"{item.downloads:,} downloads")
        self.detail_text.setText("  |  ".join(details))

    def _local_path(self, item: SoundLibraryItem | None) -> Path | None:
        if item is None:
            return None
        if item.local_path:
            path = Path(item.local_path)
            return path if path.is_file() else None
        return self.service.existing_download(item)

    def _preview_item(self, item: SoundLibraryItem, source: str) -> None:
        self._select_item(item, source)
        self.preview_selected()

    def preview_selected(self) -> None:
        item = self._selected_item
        if item is None:
            return
        local_path = self._local_path(item)
        source = QUrl.fromLocalFile(str(local_path)) if local_path else QUrl(item.preview_url)
        if not source.isValid() or (not local_path and not item.preview_url):
            self.status_label.setText("This sound does not have a usable preview.")
            return
        self.preview_player.stop()
        self.preview_player.setSource(source)
        self.preview_player.play()
        self.status_label.setText(f"Previewing {item.name}...")
        self._update_selection_state()

    def stop_preview(self) -> None:
        player = getattr(self, "preview_player", None)
        if player is not None:
            player.stop()
        if hasattr(self, "preview_button"):
            self._update_selection_state()

    def _preview_error(self, _error, error_text: str) -> None:
        self.status_label.setText(f"Preview failed: {error_text or 'unsupported audio format'}")
        self._update_selection_state()

    def _preview_status_changed(self, status) -> None:
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.status_label.setText("Preview finished.")
        self._update_selection_state()

    def open_selected_source(self) -> None:
        if self._selected_item and self._selected_item.source_url:
            QDesktopServices.openUrl(QUrl(self._selected_item.source_url))

    def copy_selected_credit(self) -> None:
        if self._selected_item:
            QApplication.clipboard().setText(self._selected_item.attribution)
            self.status_label.setText("Credit copied.")

    def _use_selected(self) -> None:
        if self._selected_item:
            self._use_item(self._selected_item, self._selected_source)

    def _use_item(self, item: SoundLibraryItem, source: str) -> None:
        self._select_item(item, source)
        if source == "online" and self._local_path(item) is None:
            self.download_selected(True)
        else:
            self.assign_selected()

    def download_selected(self, assign_after: bool) -> None:
        item = self._selected_item
        if item is None or self._selected_source != "online":
            return
        existing = self.service.existing_download(item)
        if existing:
            if assign_after:
                self._emit_assignment(existing, item)
            else:
                self.status_label.setText("This sound is already in My Sounds.")
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
        reply = self.network.get(self._request(item.preview_url, "", 60_000))
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
        self._populate_online_table()
        self._select_item(item, "online")
        self.status_label.setText(f"Saved {item.name} to My Sounds.")
        if assign_after:
            self._emit_assignment(destination, item)

    def assign_selected(self) -> None:
        item = self._selected_item
        if item is None:
            return
        path = self._local_path(item)
        if path is None:
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
        path, _ = QFileDialog.getOpenFileName(self, "Import Sound", "", "Audio files (*.wav *.mp3 *.ogg);;All files (*.*)")
        if not path:
            return
        try:
            destination = self.service.import_local_file(Path(path))
        except (OSError, SoundLibraryError) as exc:
            QMessageBox.warning(self, "Sound not imported", str(exc))
            return
        self.refresh_local_items()
        self.tabs.setCurrentWidget(self.local_page)
        imported = next((item for item in self._local_items if item.local_path == str(destination)), None)
        if imported:
            self._select_item(imported, "local")
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
        connected = bool(self.service.api_key())
        self.search_button.setEnabled(not busy and connected)
        self.save_key_button.setEnabled(not busy)
        self.get_key_button.setEnabled(not busy)
        self.forget_key_button.setEnabled(not busy and connected)
        self.previous_button.setEnabled(not busy and bool(self._search_result and self._search_result.has_previous))
        self.next_button.setEnabled(not busy and bool(self._search_result and self._search_result.has_next))
        self.import_button.setEnabled(not busy)
        for cards in self._cards.values():
            for card in cards:
                card.setEnabled(not busy)
        self._update_selection_state()


def _combo(items: tuple[tuple[str, Any], ...]) -> QComboBox:
    combo = QComboBox()
    combo.setMaxVisibleItems(16)
    for label, value in items:
        combo.addItem(label, value)
    return combo


def _duration_text(duration: float) -> str:
    if duration <= 0:
        return "Unknown length"
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
