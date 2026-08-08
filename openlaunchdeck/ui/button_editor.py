from __future__ import annotations

from PySide6.QtCore import QSize, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QPlainTextEdit,
    QMessageBox,
    QSizePolicy,
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
    library_requested = Signal()
    back_requested = Signal()

    def __init__(self, registry) -> None:
        super().__init__()
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)
        self.button: ButtonConfig | None = None
        self._loading = False
        self._notes_timer = QTimer(self)
        self._notes_timer.setSingleShot(True)
        self._notes_timer.timeout.connect(self.apply_changes)
        self._action_timer = QTimer(self)
        self._action_timer.setSingleShot(True)
        self._action_timer.setInterval(180)
        self._action_timer.timeout.connect(self.apply_changes)

        layout = QVBoxLayout(self)
        self.setObjectName("InspectorPanel")
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        heading = QGridLayout()
        heading.setColumnStretch(0, 1)
        self.title = QLabel("A1")
        self.title.setObjectName("PanelTitle")
        self.back_button = QPushButton("Back to Grid")
        self.back_button.setObjectName("HeaderButton")
        self.back_button.setVisible(False)
        self.back_button.setToolTip("Return to the Launchpad grid.")
        heading.addWidget(self.title, 0, 0)
        heading.addWidget(self.back_button, 0, 1)
        layout.addLayout(heading)
        self.subtitle = QLabel("Selected pad settings")
        self.subtitle.setObjectName("PanelHint")
        layout.addWidget(self.subtitle)

        identity_title = QLabel("Identity")
        identity_title.setObjectName("SectionTitle")
        layout.addWidget(identity_title)
        form = QFormLayout()
        form.setSpacing(10)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.label_edit = QLineEdit()
        self.color_combo = QComboBox()
        for color, value in NAMED_COLORS.items():
            swatch = QPixmap(QSize(14, 14))
            swatch.fill(QColor(value))
            self.color_combo.addItem(QIcon(swatch), color.title(), color)
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

        buttons = QGridLayout()
        buttons.setHorizontalSpacing(8)
        buttons.setVerticalSpacing(8)
        self.test_button = QPushButton("Test Action")
        self.clear_button = QPushButton("Clear Pad")
        self.copy_button = QPushButton("Copy")
        self.paste_button = QPushButton("Paste")
        for index, button in enumerate((self.test_button, self.clear_button, self.copy_button, self.paste_button)):
            button.setObjectName("SecondaryButton")
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            buttons.addWidget(button, index // 2, index % 2)
        self.test_button.setObjectName("PrimaryButton")
        self.test_button.setToolTip("Run this pad through the same action path used by the Launchpad.")
        self.clear_button.setToolTip("Reset this pad to an empty button.")
        self.copy_button.setToolTip("Copy the complete pad configuration.")
        self.paste_button.setToolTip("Paste a copied pad configuration here.")
        layout.addLayout(buttons)
        layout.addStretch(1)

        self.label_edit.editingFinished.connect(self.apply_changes)
        self.color_combo.currentIndexChanged.connect(lambda _index: self.apply_changes())
        self.enabled_check.stateChanged.connect(lambda _state: self.apply_changes())
        self.dangerous_check.stateChanged.connect(lambda _state: self.apply_changes())
        self.notes_edit.textChanged.connect(self._queue_notes_change)
        self.action_editor.changed.connect(self._queue_action_change)
        self.action_editor.library_requested.connect(self.library_requested.emit)
        self.test_button.clicked.connect(self._test)
        self.clear_button.clicked.connect(self.clear_requested.emit)
        self.copy_button.clicked.connect(self.copy_requested.emit)
        self.paste_button.clicked.connect(self.paste_requested.emit)
        self.back_button.clicked.connect(self.back_requested.emit)

    def set_compact_navigation(self, enabled: bool) -> None:
        self.back_button.setVisible(enabled)

    def set_button(self, button: ButtonConfig) -> None:
        self._notes_timer.stop()
        self._action_timer.stop()
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

    def set_page_choices(self, pages: list[tuple[str, str]]) -> None:
        self.action_editor.set_context_choices("switch_page", "page_id", pages)

    def _queue_notes_change(self) -> None:
        if not self._loading:
            self._notes_timer.start(350)

    def _queue_action_change(self) -> None:
        if not self._loading:
            self._action_timer.start()

    def flush_pending_changes(self) -> None:
        if self._notes_timer.isActive() or self._action_timer.isActive():
            self._notes_timer.stop()
            self._action_timer.stop()
            self.apply_changes()

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
        self._notes_timer.stop()
        self._action_timer.stop()
        self.apply_changes()
        errors = self.action_editor.validation_errors()
        if errors:
            QMessageBox.warning(self, "Invalid action settings", "\n".join(errors[:5]))
            return
        self.test_requested.emit()
