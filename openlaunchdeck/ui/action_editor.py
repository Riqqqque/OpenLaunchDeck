from __future__ import annotations

import json
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QCompleter,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QPlainTextEdit,
    QSpinBox,
    QWidget,
    QFileDialog,
)

from ..constants import NAMED_COLORS


class ActionEditor(QWidget):
    changed = Signal()

    def __init__(self, registry) -> None:
        super().__init__()
        self.setObjectName("ActionEditor")
        self.registry = registry
        self.action_type_combo = QComboBox()
        for action in sorted(registry.all(), key=lambda item: item.display_name):
            self.action_type_combo.addItem(action.display_name, action.type_name)
        self.form = QFormLayout(self)
        self.form.setContentsMargins(0, 0, 0, 0)
        self.form.setSpacing(10)
        self.form.addRow("Action", self.action_type_combo)
        self.field_widgets: dict[str, Any] = {}
        self._config: dict[str, Any] = {}
        self.action_type_combo.currentIndexChanged.connect(self._rebuild_fields)
        self.action_type_combo.currentIndexChanged.connect(lambda _index: self.changed.emit())

    def set_action(self, action_type: str, config: dict[str, Any]) -> None:
        index = self.action_type_combo.findData(action_type)
        self.action_type_combo.setCurrentIndex(index if index >= 0 else self.action_type_combo.findData("noop"))
        self._config = dict(config)
        self._rebuild_fields()

    def current_action(self) -> tuple[str, dict[str, Any]]:
        action_type = self.action_type_combo.currentData()
        config: dict[str, Any] = {}
        for name, widget in self.field_widgets.items():
            if isinstance(widget, QLineEdit):
                config[name] = widget.text()
            elif hasattr(widget, "value_widget") and isinstance(widget.value_widget, QLineEdit):
                config[name] = widget.value_widget.text()
            elif isinstance(widget, QPlainTextEdit):
                text = widget.toPlainText()
                action = self.registry.get(action_type)
                field = next((item for item in action.config_fields if item["name"] == name), {})
                if field.get("type") == "json":
                    try:
                        config[name] = json.loads(text) if text.strip() else []
                    except json.JSONDecodeError:
                        config[name] = []
                else:
                    config[name] = text
            elif isinstance(widget, QCheckBox):
                config[name] = widget.isChecked()
            elif isinstance(widget, QSpinBox):
                config[name] = widget.value()
            elif isinstance(widget, QComboBox):
                if widget.isEditable():
                    config[name] = widget.currentText().strip()
                else:
                    config[name] = widget.currentData()
        return str(action_type or "noop"), config

    def _clear_dynamic_rows(self) -> None:
        while self.form.rowCount() > 1:
            self.form.removeRow(1)
        self.field_widgets.clear()

    def _rebuild_fields(self) -> None:
        self._clear_dynamic_rows()
        action = self.registry.get(str(self.action_type_combo.currentData() or "noop"))
        for field in action.config_fields:
            name = field["name"]
            widget = self._make_widget(field, self._config.get(name))
            self.field_widgets[name] = widget
            self.form.addRow(field.get("label", name), widget)
            self._connect_widget_changed(widget)

    def _make_widget(self, field: dict[str, Any], value: Any) -> QWidget:
        field_type = field.get("type", "text")
        if field_type == "bool":
            widget = QCheckBox()
            widget.setChecked(bool(value))
            return widget
        if field_type == "number":
            widget = QSpinBox()
            widget.setRange(0, 999999)
            widget.setValue(int(value or 0))
            return widget
        if field_type == "choice":
            widget = QComboBox()
            for choice in field.get("choices", []):
                widget.addItem(str(choice), choice)
            index = widget.findData(value)
            if index >= 0:
                widget.setCurrentIndex(index)
            return widget
        if field_type == "hotkey":
            widget = QComboBox()
            widget.setEditable(True)
            widget.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
            widget.addItem("", "")
            suggestions = [str(item) for item in field.get("suggestions", []) if str(item).strip()]
            for suggestion in suggestions:
                widget.addItem(suggestion, suggestion)
            if widget.lineEdit():
                widget.lineEdit().setPlaceholderText(str(field.get("placeholder") or "Choose or type a hotkey"))
            completer = QCompleter(suggestions, widget)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            widget.setCompleter(completer)
            if value:
                text = str(value)
                index = widget.findText(text, Qt.MatchFlag.MatchFixedString)
                if index >= 0:
                    widget.setCurrentIndex(index)
                else:
                    widget.setEditText(text)
            else:
                widget.setCurrentIndex(0)
            return widget
        if field_type == "color":
            widget = QComboBox()
            for color in NAMED_COLORS:
                widget.addItem(color, color)
            index = widget.findData(value)
            if index >= 0:
                widget.setCurrentIndex(index)
            return widget
        if field_type in {"multiline", "json"}:
            widget = QPlainTextEdit()
            widget.setMaximumHeight(100)
            if field_type == "json":
                widget.setPlainText(json.dumps(value if value is not None else [], indent=2))
            else:
                widget.setPlainText(str(value or ""))
            return widget
        if field_type in {"path", "file"}:
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            edit = QLineEdit(str(value or ""))
            browse = QPushButton("Browse")
            browse.setObjectName("SecondaryButton")
            layout.addWidget(edit)
            layout.addWidget(browse)
            browse.clicked.connect(lambda: self._browse(edit, field_type))
            container.value_widget = edit
            edit.editingFinished.connect(lambda: self.changed.emit())
            return container
        return QLineEdit(str(value or ""))

    def _connect_widget_changed(self, widget: QWidget) -> None:
        if isinstance(widget, QLineEdit):
            widget.editingFinished.connect(lambda: self.changed.emit())
        elif isinstance(widget, QPlainTextEdit):
            widget.textChanged.connect(lambda: self.changed.emit())
        elif isinstance(widget, QCheckBox):
            widget.stateChanged.connect(lambda _state: self.changed.emit())
        elif isinstance(widget, QSpinBox):
            widget.valueChanged.connect(lambda _value: self.changed.emit())
        elif isinstance(widget, QComboBox):
            widget.currentIndexChanged.connect(lambda _index: self.changed.emit())
            if widget.isEditable():
                widget.editTextChanged.connect(lambda _text: self.changed.emit())

    def _browse(self, edit: QLineEdit, field_type: str) -> None:
        if field_type == "file":
            path, _ = QFileDialog.getOpenFileName(self, "Choose File")
        else:
            path = QFileDialog.getExistingDirectory(self, "Choose Folder")
        if path:
            edit.setText(path)
