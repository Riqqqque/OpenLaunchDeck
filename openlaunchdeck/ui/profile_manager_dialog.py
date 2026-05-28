from __future__ import annotations

from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout


class ProfileManagerDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Profile Manager")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Profile import, export, add, duplicate, and delete controls are available in the sidebar."))
