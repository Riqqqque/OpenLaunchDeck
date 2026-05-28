from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QLabel, QVBoxLayout


class SetupWizard(QDialog):
    def __init__(self, profile_service, settings_service, parent=None) -> None:
        super().__init__(parent)
        self.profile_service = profile_service
        self.settings_service = settings_service
        self.setWindowTitle("First Setup")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("OpenLaunchDeck is ready. You can use simulation mode until your Launchpad is connected."))
        layout.addWidget(QLabel("Choose a starter profile:"))
        self.profile_combo = QComboBox()
        for profile in profile_service.profiles.values():
            self.profile_combo.addItem(profile.name, profile.id)
        layout.addWidget(self.profile_combo)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def accept(self) -> None:
        profile_id = str(self.profile_combo.currentData() or "")
        if profile_id:
            self.profile_service.set_current_profile(profile_id)
        self.settings_service.update(first_run_complete=True, default_profile=profile_id or self.settings_service.settings.default_profile)
        super().accept()
