from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from ..version import APP_NAME


class ProfileManagerDialog(QDialog):
    def __init__(self, profile_service, parent=None) -> None:
        super().__init__(parent)
        self.profile_service = profile_service
        self.setWindowTitle("Profile Manager")
        self.resize(520, 430)

        layout = QVBoxLayout(self)
        title = QLabel("Profiles")
        title.setObjectName("PanelTitle")
        layout.addWidget(title)
        hint = QLabel("Create separate decks for different games, apps, or streaming setups.")
        hint.setObjectName("MutedText")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.profile_list = QListWidget()
        self.profile_list.itemDoubleClicked.connect(lambda _item: self.rename_selected())
        layout.addWidget(self.profile_list, 1)

        tools = QHBoxLayout()
        self.create_button = QPushButton("Create")
        self.duplicate_button = QPushButton("Duplicate")
        self.rename_button = QPushButton("Rename")
        self.delete_button = QPushButton("Delete")
        for button in (self.create_button, self.duplicate_button, self.rename_button, self.delete_button):
            button.setObjectName("SecondaryButton")
            tools.addWidget(button)
        layout.addLayout(tools)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.create_button.clicked.connect(self.create_profile)
        self.duplicate_button.clicked.connect(self.duplicate_selected)
        self.rename_button.clicked.connect(self.rename_selected)
        self.delete_button.clicked.connect(self.delete_selected)
        self.profile_list.currentItemChanged.connect(lambda *_: self._update_buttons())
        self.refresh()

    def refresh(self, selected_id: str = "") -> None:
        selected_id = selected_id or self.profile_service.current_profile_id
        self.profile_list.clear()
        for profile in self.profile_service.profiles.values():
            item = QListWidgetItem(profile.name)
            item.setData(Qt.ItemDataRole.UserRole, profile.id)
            item.setToolTip(f"Profile ID: {profile.id}")
            self.profile_list.addItem(item)
            if profile.id == selected_id:
                self.profile_list.setCurrentItem(item)
        if self.profile_list.currentItem() is None and self.profile_list.count():
            self.profile_list.setCurrentRow(0)
        self._update_buttons()

    def create_profile(self) -> None:
        name, accepted = QInputDialog.getText(self, "Create Profile", "Profile name:")
        if not accepted or not name.strip():
            return
        try:
            profile = self.profile_service.create_profile(name.strip())
        except Exception as exc:
            QMessageBox.warning(self, APP_NAME, f"Profile could not be created:\n{exc}")
            return
        self.profile_service.set_current_profile(profile.id)
        self.refresh(profile.id)

    def duplicate_selected(self) -> None:
        profile_id = self._selected_id()
        if not profile_id:
            return
        try:
            profile = self.profile_service.duplicate_profile(profile_id)
        except Exception as exc:
            QMessageBox.warning(self, APP_NAME, f"Profile could not be duplicated:\n{exc}")
            return
        self.profile_service.set_current_profile(profile.id)
        self.refresh(profile.id)

    def rename_selected(self) -> None:
        profile_id = self._selected_id()
        if not profile_id:
            return
        profile = self.profile_service.profiles[profile_id]
        name, accepted = QInputDialog.getText(self, "Rename Profile", "Profile name:", text=profile.name)
        if not accepted or not name.strip() or name.strip() == profile.name:
            return
        profile.name = name.strip()
        try:
            self.profile_service.save_profile(profile)
        except Exception as exc:
            QMessageBox.warning(self, APP_NAME, f"Profile could not be renamed:\n{exc}")
            return
        self.refresh(profile.id)

    def delete_selected(self) -> None:
        profile_id = self._selected_id()
        if not profile_id:
            return
        profile = self.profile_service.profiles[profile_id]
        if len(self.profile_service.profiles) <= 1:
            QMessageBox.information(self, APP_NAME, "At least one profile must remain.")
            return
        answer = QMessageBox.question(self, APP_NAME, f"Delete profile '{profile.name}'? A backup will be kept.")
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.profile_service.delete_profile(profile_id)
        except Exception as exc:
            QMessageBox.warning(self, APP_NAME, f"Profile could not be deleted:\n{exc}")
            return
        self.refresh()

    def _selected_id(self) -> str:
        item = self.profile_list.currentItem()
        return str(item.data(Qt.ItemDataRole.UserRole) or "") if item else ""

    def _update_buttons(self) -> None:
        has_selection = bool(self._selected_id())
        self.duplicate_button.setEnabled(has_selection)
        self.rename_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection and len(self.profile_service.profiles) > 1)
