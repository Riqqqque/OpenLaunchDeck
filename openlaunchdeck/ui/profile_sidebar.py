from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ProfileSidebar(QWidget):
    profile_changed = Signal(str)
    page_changed = Signal(str)
    add_page_requested = Signal()
    duplicate_page_requested = Signal()
    delete_page_requested = Signal()
    import_profile_requested = Signal()
    export_profile_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Profile"))
        self.profile_combo = QComboBox()
        layout.addWidget(self.profile_combo)
        layout.addWidget(QLabel("Page"))
        self.page_combo = QComboBox()
        layout.addWidget(self.page_combo)
        self.add_page_button = QPushButton("Add Page")
        self.duplicate_page_button = QPushButton("Duplicate Page")
        self.delete_page_button = QPushButton("Delete Page")
        self.import_button = QPushButton("Import Profile")
        self.export_button = QPushButton("Export Profile")
        for button in (
            self.add_page_button,
            self.duplicate_page_button,
            self.delete_page_button,
            self.import_button,
            self.export_button,
        ):
            layout.addWidget(button)
        layout.addStretch(1)
        self.profile_combo.currentIndexChanged.connect(lambda: self.profile_changed.emit(str(self.profile_combo.currentData() or "")))
        self.page_combo.currentIndexChanged.connect(lambda: self.page_changed.emit(str(self.page_combo.currentData() or "")))
        self.add_page_button.clicked.connect(self.add_page_requested.emit)
        self.duplicate_page_button.clicked.connect(self.duplicate_page_requested.emit)
        self.delete_page_button.clicked.connect(self.delete_page_requested.emit)
        self.import_button.clicked.connect(self.import_profile_requested.emit)
        self.export_button.clicked.connect(self.export_profile_requested.emit)

    def refresh(self, profile_service) -> None:
        self.profile_combo.blockSignals(True)
        self.page_combo.blockSignals(True)
        self.profile_combo.clear()
        for profile in profile_service.profiles.values():
            self.profile_combo.addItem(profile.name, profile.id)
        self.profile_combo.setCurrentIndex(max(0, self.profile_combo.findData(profile_service.current_profile_id)))
        self.page_combo.clear()
        for page in profile_service.current_profile.pages:
            self.page_combo.addItem(page.name, page.id)
        self.page_combo.setCurrentIndex(max(0, self.page_combo.findData(profile_service.current_page_id)))
        self.profile_combo.blockSignals(False)
        self.page_combo.blockSignals(False)
