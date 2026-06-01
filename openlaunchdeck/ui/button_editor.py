from __future__ import annotations

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..constants import NAMED_COLORS
from ..models.action_config import ActionConfig
from ..models.button import ButtonConfig
from .action_editor import ActionEditor


class ButtonEditor(QWidget):
    changed = Signal()
    test_requested = Signal()
    clear_requested = Signal()
    copy_requested = Signal()
    paste_requested = Signal()

    def __init__(self, registry) -> None:
        super().__init__()
        self.button: ButtonConfig | None = None
        self._loading = False
        self._notes_timer = QTimer(self)
        self._notes_timer.setSingleShot(True)
        self._notes_timer.timeout.connect(self.apply_changes)

        layout = QVBoxLayout(self)
        self.setObjectName("InspectorPanel")
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        self.title = QLabel("A1")
        self.title.setObjectName("PanelTitle")
        layout.addWidget(self.title)
        self.subtitle = QLabel("Selected pad settings")
        self.subtitle.setObjectName("PanelHint")
        layout.addWidget(self.subtitle)

        identity_title = QLabel("Identity")
        identity_title.setObjectName("SectionTitle")
        layout.addWidget(identity_title)
        form = QFormLayout()
        form.setSpacing(10)
        self.label_edit = QLineEdit()
        self.color_combo = QComboBox()
        for color in NAMED_COLORS:
            self.color_combo.addItem(color, color)
        self.enabled_check = QCheckBox()
        self.dangerous_check = QCheckBox()
        self.notes_edit = QPlainTextEdit()
        self.notes_edit.setMaximumHeight(90)
        form.addRow("Label", self.label_edit)
        form.addRow("Color", self.color_combo)
        form.addRow("Enabled", self.enabled_check)
        form.addRow("Dangerous", self.dangerous_check)
        form.addRow("Notes", self.notes_edit)
        layout.addLayout(form)

        action_title = QLabel("Action")
        action_title.setObjectName("SectionTitle")
        layout.addWidget(action_title)
        self.action_editor = ActionEditor(registry)
        layout.addWidget(self.action_editor)

        buttons = QHBoxLayout()
        self.test_button = QPushButton("Test")
        self.clear_button = QPushButton("Clear")
        self.copy_button = QPushButton("Copy")
        self.paste_button = QPushButton("Paste")
        for button in (self.test_button, self.clear_button, self.copy_button, self.paste_button):
            button.setObjectName("SecondaryButton")
            buttons.addWidget(button)
        self.test_button.setObjectName("PrimaryButton")
        layout.addLayout(buttons)
        layout.addStretch(1)

        self.label_edit.editingFinished.connect(self.apply_changes)
        self.color_combo.currentIndexChanged.connect(lambda _index: self.apply_changes())
        self.enabled_check.stateChanged.connect(lambda _state: self.apply_changes())
        self.dangerous_check.stateChanged.connect(lambda _state: self.apply_changes())
        self.notes_edit.textChanged.connect(lambda: self._notes_timer.start(350))
        self.action_editor.action_type_combo.currentIndexChanged.connect(lambda _index: self.apply_changes())
        self.action_editor.changed.connect(self.apply_changes)
        self.test_button.clicked.connect(self._test)
        self.clear_button.clicked.connect(self.clear_requested.emit)
        self.copy_button.clicked.connect(self.copy_requested.emit)
        self.paste_button.clicked.connect(self.paste_requested.emit)

    def set_button(self, button: ButtonConfig) -> None:
        self._loading = True
        self.button = button
        self.title.setText(f"Button {button.id}")
        self.subtitle.setText(button.label or "Empty pad")
        self.label_edit.setText(button.label)
        self.color_combo.setCurrentIndex(max(0, self.color_combo.findData(button.color)))
        self.enabled_check.setChecked(button.enabled)
        self.dangerous_check.setChecked(button.dangerous)
        self.notes_edit.setPlainText(button.notes)
        action = button.action or ActionConfig()
        self.action_editor.set_action(action.type, action.config)
        self._loading = False

    def apply_changes(self) -> None:
        if self._loading or self.button is None:
            return
        self.button.label = self.label_edit.text()
        self.button.color = str(self.color_combo.currentData() or "dim")
        self.button.enabled = self.enabled_check.isChecked()
        self.button.dangerous = self.dangerous_check.isChecked()
        self.button.notes = self.notes_edit.toPlainText()
        action_type, config = self.action_editor.current_action()
        self.button.action = ActionConfig(action_type, config)
        self.changed.emit()

    def _test(self) -> None:
        self.apply_changes()
        self.test_requested.emit()
