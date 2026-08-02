from __future__ import annotations

import json
from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QPlainTextEdit,
    QSizePolicy,
    QSpinBox,
    QWidget,
    QFileDialog,
)

from ..constants import NAMED_COLORS
from .hotkey_picker import HotkeyPicker


CHOICE_DISPLAY_LABELS = {
    "play_pause": "Play / Pause",
    "png": "PNG",
    "jpg": "JPG",
}


class ActionEditor(QWidget):
    changed = Signal()

    def __init__(self, registry) -> None:
        super().__init__()
        self.setObjectName("ActionEditor")
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.registry = registry
        self.action_type_combo = QComboBox()
        self.action_type_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.action_type_combo.setMinimumContentsLength(8)
        for action in sorted(registry.all(), key=lambda item: item.display_name):
            self.action_type_combo.addItem(action.display_name, action.type_name)
        self.form = QFormLayout(self)
        self.form.setContentsMargins(0, 0, 0, 0)
        self.form.setSpacing(10)
        self.form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.form.addRow("Action", self.action_type_combo)
        self.field_widgets: dict[str, Any] = {}
        self._config: dict[str, Any] = {}
        self._dynamic_choices: dict[tuple[str, str], list[tuple[str, Any]]] = {}
        self.action_type_combo.currentIndexChanged.connect(self._rebuild_fields)
        self.action_type_combo.currentIndexChanged.connect(lambda _index: self.changed.emit())

    def set_context_choices(self, action_type: str, field_name: str, choices: list[tuple[str, Any]]) -> None:
        self._dynamic_choices[(action_type, field_name)] = [(str(label), data) for label, data in choices]

    def set_action(self, action_type: str, config: dict[str, Any]) -> None:
        index = self.action_type_combo.findData(action_type)
        self.action_type_combo.setCurrentIndex(index if index >= 0 else self.action_type_combo.findData("noop"))
        self._config = dict(config)
        self._rebuild_fields()

    def current_action(self) -> tuple[str, dict[str, Any]]:
        action_type = self.action_type_combo.currentData()
        config: dict[str, Any] = dict(self._config)
        for name, widget in self.field_widgets.items():
            if isinstance(widget, HotkeyPicker):
                config[name] = widget.value()
            elif isinstance(widget, QLineEdit):
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
                    except json.JSONDecodeError as exc:
                        config[name] = self._config.get(name, [])
                        widget.setToolTip(f"JSON is incomplete or invalid: {exc.msg}")
                        self._set_invalid(widget, True)
                    else:
                        widget.setToolTip("")
                        self._set_invalid(widget, False)
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
        self._config = dict(config)
        return str(action_type or "noop"), config

    def _clear_dynamic_rows(self) -> None:
        while self.form.rowCount() > 1:
            self.form.removeRow(1)
        self.field_widgets.clear()

    def has_validation_errors(self) -> bool:
        return any(bool(widget.property("invalid")) for widget in self.field_widgets.values())

    @staticmethod
    def _set_invalid(widget: QWidget, invalid: bool) -> None:
        if bool(widget.property("invalid")) == invalid:
            return
        widget.setProperty("invalid", invalid)
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def _rebuild_fields(self) -> None:
        self._clear_dynamic_rows()
        action = self.registry.get(str(self.action_type_combo.currentData() or "noop"))
        for field in action.config_fields:
            field = dict(field)
            name = field["name"]
            dynamic_choices = self._dynamic_choices.get((action.type_name, name))
            if dynamic_choices is not None:
                field["choices"] = dynamic_choices
            widget = self._make_widget(field, self._config.get(name))
            help_text = str(field.get("help") or "").strip()
            if help_text:
                widget.setToolTip(help_text)
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
            minimum = int(field.get("min", 0))
            maximum = int(field.get("max", 999999))
            default = int(field.get("default", minimum))
            raw_value = default if value in (None, "") else value
            try:
                number = int(raw_value)
            except (TypeError, ValueError):
                number = default
            widget.setRange(minimum, maximum)
            widget.setValue(max(minimum, min(maximum, number)))
            return widget
        if field_type == "choice":
            widget = QComboBox()
            widget.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            widget.setMinimumContentsLength(8)
            widget.setMaxVisibleItems(18)
            for choice in field.get("choices", []):
                if isinstance(choice, (tuple, list)) and len(choice) == 2:
                    label, data = choice
                else:
                    data = choice
                    text = str(choice)
                    label = CHOICE_DISPLAY_LABELS.get(text, text if text.isupper() else text.replace("_", " ").title())
                widget.addItem(str(label), data)
            index = widget.findData(value)
            if index >= 0:
                widget.setCurrentIndex(index)
            elif value not in (None, ""):
                widget.addItem(f"Unavailable: {value}", value)
                widget.setCurrentIndex(widget.count() - 1)
            return widget
        if field_type == "hotkey":
            keys = [str(item) for item in field.get("keys", []) if str(item).strip()]
            return HotkeyPicker(keys, value)
        if field_type == "color":
            widget = QComboBox()
            widget.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            widget.setMinimumContentsLength(8)
            for color in NAMED_COLORS:
                widget.addItem(color.title(), color)
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
        if field_type in {"path", "file", "file_or_directory"}:
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            edit = QLineEdit(str(value or ""))
            edit.setMinimumWidth(0)
            edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            browse = QPushButton("File" if field_type == "file_or_directory" else "Browse")
            browse.setObjectName("SecondaryButton")
            browse.setMinimumWidth(64)
            layout.addWidget(edit, 1)
            layout.addWidget(browse)
            browse.clicked.connect(lambda: self._browse(edit, "file" if field_type == "file_or_directory" else field_type))
            if field_type == "file_or_directory":
                folder = QPushButton("Folder")
                folder.setObjectName("SecondaryButton")
                folder.setMinimumWidth(64)
                layout.addWidget(folder)
                folder.clicked.connect(lambda: self._browse(edit, "path"))
            container.value_widget = edit
            edit.editingFinished.connect(lambda: self.changed.emit())
            return container
        widget = QLineEdit(str(value or ""))
        if field_type == "password":
            widget.setEchoMode(QLineEdit.EchoMode.Password)
        return widget

    def _connect_widget_changed(self, widget: QWidget) -> None:
        if isinstance(widget, HotkeyPicker):
            widget.changed.connect(self.changed.emit)
        elif isinstance(widget, QLineEdit):
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
