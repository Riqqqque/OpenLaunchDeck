from __future__ import annotations

import json
from collections.abc import Collection
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QWidget,
)

from ..constants import NAMED_COLORS
from .action_sequence_editor import ActionSequenceEditor
from .hotkey_picker import HotkeyPicker


CHOICE_DISPLAY_LABELS = {
    "play_pause": "Play / Pause",
    "png": "PNG",
    "jpg": "JPG",
}

ACTION_CATEGORIES = {
    "noop": "Essentials",
    "switch_page": "Essentials",
    "switch_profile": "Essentials",
    "navigate_deck": "Essentials",
    "multi_action": "Essentials",
    "delay": "Essentials",
    "hotkey": "Windows",
    "type_text": "Windows",
    "clipboard": "Windows",
    "window_control": "Windows",
    "mouse_control": "Windows",
    "open_url": "Windows",
    "open_path": "Windows",
    "run_command": "Windows",
    "powershell": "Windows",
    "media_control": "Media",
    "volume_control": "Media",
    "play_sound": "Soundboard",
    "random_sound": "Soundboard",
    "stop_sound": "Soundboard",
    "obs_websocket": "Streaming",
    "http_request": "Network",
    "ssh_command": "Network",
}


class ActionEditor(QWidget):
    changed = Signal()

    def __init__(self, registry, allow_multi_action: bool = True) -> None:
        super().__init__()
        self.setObjectName("ActionEditor")
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.registry = registry
        self._loading = False
        self._rendered_action_type = ""
        self._config: dict[str, Any] = {}
        self._configs_by_type: dict[str, dict[str, Any]] = {}
        self._field_definitions: dict[str, dict[str, Any]] = {}
        self._help_labels: dict[str, QLabel] = {}
        self._dynamic_choices: dict[tuple[str, str], list[tuple[str, Any]]] = {}
        self._action_search_dirty = False

        self.action_type_combo = QComboBox()
        self.action_type_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.action_type_combo.setMinimumContentsLength(8)
        self.action_type_combo.setMaxVisibleItems(20)
        self.action_type_combo.setEditable(True)
        self.action_type_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.action_type_combo.completer().setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.action_type_combo.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        if self.action_type_combo.lineEdit() is not None:
            self.action_type_combo.lineEdit().setPlaceholderText("Search actions")
            self.action_type_combo.lineEdit().textEdited.connect(self._mark_action_search_dirty)
            self.action_type_combo.lineEdit().editingFinished.connect(self._commit_action_search)
        actions = [action for action in registry.all() if allow_multi_action or action.type_name != "multi_action"]
        for action in sorted(actions, key=lambda item: (ACTION_CATEGORIES.get(item.type_name, "Other"), item.display_name)):
            category = ACTION_CATEGORIES.get(action.type_name, "Other")
            self.action_type_combo.addItem(f"{category}  |  {action.display_name}", action.type_name)

        self.form = QFormLayout(self)
        self.form.setContentsMargins(0, 0, 0, 0)
        self.form.setSpacing(10)
        self.form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.form.addRow("Action", self.action_type_combo)
        self.description_label = QLabel()
        self.description_label.setObjectName("ActionDescription")
        self.description_label.setWordWrap(True)
        self.form.addRow(self.description_label)
        self.field_widgets: dict[str, QWidget] = {}

        self.action_type_combo.currentIndexChanged.connect(self._action_type_changed)

    def set_context_choices(self, action_type: str, field_name: str, choices: list[tuple[str, Any]]) -> None:
        self._dynamic_choices[(action_type, field_name)] = [(str(label), data) for label, data in choices]
        if self._rendered_action_type == action_type:
            self._store_current_config()
            self._rebuild_fields()

    def set_action(self, action_type: str, config: dict[str, Any]) -> None:
        target_type = action_type if self.action_type_combo.findData(action_type) >= 0 else "noop"
        self._loading = True
        self._configs_by_type = {target_type: dict(config)}
        self._config = dict(config)
        self.action_type_combo.blockSignals(True)
        self.action_type_combo.setCurrentIndex(max(0, self.action_type_combo.findData(target_type)))
        self.action_type_combo.blockSignals(False)
        self._rebuild_fields()
        self._loading = False

    def current_action(self) -> tuple[str, dict[str, Any]]:
        action_type = str(self.action_type_combo.currentData() or "noop")
        if self._rendered_action_type == action_type:
            self._store_current_config()
        return action_type, dict(self._config)

    def validation_errors(self) -> list[str]:
        action_type, config = self.current_action()
        errors = [
            str(widget.toolTip())
            for widget in self.field_widgets.values()
            if bool(widget.property("invalid")) and widget.toolTip()
        ]
        if errors:
            return errors
        try:
            return [str(message) for message in self.registry.get(action_type).validate(config) if str(message).strip()]
        except Exception:
            return ["These action settings could not be validated."]

    def has_validation_errors(self) -> bool:
        return bool(self.validation_errors())

    def _action_type_changed(self, _index: int) -> None:
        if self._loading:
            return
        if self._rendered_action_type:
            self._store_current_config()
            self._configs_by_type[self._rendered_action_type] = dict(self._config)
        action_type = str(self.action_type_combo.currentData() or "noop")
        self._config = dict(self._configs_by_type.get(action_type, {}))
        self._rebuild_fields()
        self._action_search_dirty = False
        self.changed.emit()

    def _mark_action_search_dirty(self, _text: str) -> None:
        self._action_search_dirty = True

    def _commit_action_search(self) -> None:
        if not self._action_search_dirty:
            return
        typed = self.action_type_combo.currentText().strip().casefold()
        matches = [
            index
            for index in range(self.action_type_combo.count())
            if typed and typed in self.action_type_combo.itemText(index).casefold()
        ]
        if len(matches) == 1:
            self.action_type_combo.setCurrentIndex(matches[0])
        elif self._rendered_action_type:
            self.action_type_combo.setCurrentIndex(max(0, self.action_type_combo.findData(self._rendered_action_type)))
        self._action_search_dirty = False

    def _clear_dynamic_rows(self) -> None:
        while self.form.rowCount() > 2:
            self.form.removeRow(2)
        self.field_widgets.clear()
        self._field_definitions.clear()
        self._help_labels.clear()

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
        self._rendered_action_type = action.type_name
        self.description_label.setText(action.description)
        for raw_field in action.config_fields:
            field = dict(raw_field)
            name = field["name"]
            dynamic_choices = self._dynamic_choices.get((action.type_name, name))
            if dynamic_choices is not None:
                field["choices"] = dynamic_choices
            widget = self._make_widget(field, self._config.get(name))
            help_text = str(field.get("help") or "").strip()
            if help_text:
                widget.setToolTip(help_text)
            self.field_widgets[name] = widget
            self._field_definitions[name] = field
            self.form.addRow(field.get("label", name), widget)
            if help_text:
                help_label = QLabel(help_text)
                help_label.setObjectName("MutedText")
                help_label.setWordWrap(True)
                self.form.addRow("", help_label)
                self._help_labels[name] = help_label
            self._connect_widget_changed(widget)
        self._apply_field_visibility()

    def _make_widget(self, field: dict[str, Any], value: Any) -> QWidget:
        field_type = field.get("type", "text")
        if field_type == "bool":
            widget = QCheckBox()
            widget.setChecked(bool(field.get("default", False) if value is None else value))
            return widget
        if field_type == "number":
            widget = QSpinBox()
            minimum = int(field.get("min", 0))
            maximum = int(field.get("max", 999999))
            default = int(field.get("default", minimum))
            try:
                number = default if value in (None, "") else int(value)
            except (TypeError, ValueError):
                number = default
            widget.setRange(minimum, maximum)
            widget.setValue(max(minimum, min(maximum, number)))
            widget.setSuffix(str(field.get("suffix") or ""))
            if field.get("special_value_text"):
                widget.setSpecialValueText(str(field["special_value_text"]))
            return widget
        if field_type == "decimal":
            widget = QDoubleSpinBox()
            minimum = float(field.get("min", 0.0))
            maximum = float(field.get("max", 999999.0))
            default = float(field.get("default", minimum))
            try:
                number = default if value in (None, "") else float(value)
            except (TypeError, ValueError):
                number = default
            widget.setRange(minimum, maximum)
            widget.setDecimals(int(field.get("decimals", 2)))
            widget.setSingleStep(float(field.get("step", 0.05)))
            widget.setValue(max(minimum, min(maximum, number)))
            widget.setSuffix(str(field.get("suffix") or ""))
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
            selected_value = field.get("default") if value in (None, "") else value
            index = widget.findData(selected_value)
            if index >= 0:
                widget.setCurrentIndex(index)
            elif value not in (None, ""):
                widget.addItem(f"Unavailable: {value}", value)
                widget.setCurrentIndex(widget.count() - 1)
            return widget
        if field_type == "hotkey":
            keys = [str(item) for item in field.get("keys", []) if str(item).strip()]
            return HotkeyPicker(keys, value)
        if field_type == "action_list":
            return ActionSequenceEditor(self.registry, value if value is not None else field.get("default", []))
        if field_type == "color":
            widget = QComboBox()
            widget.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            widget.setMinimumContentsLength(8)
            for color, color_value in NAMED_COLORS.items():
                swatch = QPixmap(14, 14)
                swatch.fill(QColor(color_value))
                widget.addItem(QIcon(swatch), color.title(), color)
            selected_value = field.get("default") if value in (None, "") else value
            index = widget.findData(selected_value)
            widget.setCurrentIndex(index if index >= 0 else 0)
            return widget
        if field_type in {"multiline", "json"}:
            widget = QPlainTextEdit()
            widget.setMaximumHeight(int(field.get("height", 100)))
            if field_type == "json":
                widget.setPlainText(json.dumps(value if value is not None else field.get("default", []), indent=2))
            else:
                widget.setPlainText(str(field.get("default", "") if value is None else value))
            widget.setPlaceholderText(str(field.get("placeholder") or ""))
            return widget
        if field_type in {"path", "file", "file_or_directory", "sound_file"}:
            container = QWidget()
            container.setMinimumWidth(0)
            container.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            edit = QLineEdit(str(value or ""))
            edit.setPlaceholderText(str(field.get("placeholder") or ""))
            edit.setMinimumWidth(0)
            edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            browse = QPushButton("File" if field_type == "file_or_directory" else "Browse")
            browse.setObjectName("SecondaryButton")
            browse.setMinimumWidth(64)
            layout.addWidget(edit, 1)
            layout.addWidget(browse)
            browse.clicked.connect(
                lambda _checked=False, target=edit, kind=field_type: self._browse(
                    target,
                    "file" if kind == "file_or_directory" else kind,
                )
            )
            if field_type == "file_or_directory":
                folder = QPushButton("Folder")
                folder.setObjectName("SecondaryButton")
                folder.setMinimumWidth(64)
                layout.addWidget(folder)
                folder.clicked.connect(lambda _checked=False, target=edit: self._browse(target, "path"))
            container.value_widget = edit
            return container
        widget = QLineEdit(str(field.get("default", "") if value is None else value))
        widget.setPlaceholderText(str(field.get("placeholder") or ""))
        if field_type == "password":
            widget.setEchoMode(QLineEdit.EchoMode.Password)
        return widget

    def _connect_widget_changed(self, widget: QWidget) -> None:
        if isinstance(widget, HotkeyPicker):
            widget.changed.connect(self._widget_changed)
        elif isinstance(widget, ActionSequenceEditor):
            widget.changed.connect(self._widget_changed)
        elif isinstance(widget, QLineEdit):
            widget.editingFinished.connect(self._widget_changed)
        elif isinstance(widget, QPlainTextEdit):
            widget.textChanged.connect(self._widget_changed)
        elif isinstance(widget, QCheckBox):
            widget.stateChanged.connect(lambda _state: self._widget_changed())
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            widget.valueChanged.connect(lambda _value: self._widget_changed())
        elif isinstance(widget, QComboBox):
            widget.currentIndexChanged.connect(lambda _index: self._widget_changed())
            if widget.isEditable():
                widget.editTextChanged.connect(lambda _text: self._widget_changed())
        elif hasattr(widget, "value_widget") and isinstance(widget.value_widget, QLineEdit):
            widget.value_widget.editingFinished.connect(self._widget_changed)

    def _widget_changed(self) -> None:
        if self._loading:
            return
        self._store_current_config()
        self._apply_field_visibility()
        self.changed.emit()

    def _store_current_config(self) -> None:
        config: dict[str, Any] = dict(self._config)
        for name, widget in self.field_widgets.items():
            field = self._field_definitions.get(name, {})
            if isinstance(widget, HotkeyPicker):
                config[name] = widget.value()
            elif isinstance(widget, ActionSequenceEditor):
                config[name] = widget.steps()
            elif isinstance(widget, QLineEdit):
                config[name] = widget.text()
            elif hasattr(widget, "value_widget") and isinstance(widget.value_widget, QLineEdit):
                config[name] = widget.value_widget.text()
            elif isinstance(widget, QPlainTextEdit):
                text = widget.toPlainText()
                if field.get("type") == "json":
                    try:
                        config[name] = json.loads(text) if text.strip() else field.get("default", [])
                    except json.JSONDecodeError as exc:
                        widget.setToolTip(f"JSON is incomplete or invalid: {exc.msg}")
                        self._set_invalid(widget, True)
                    else:
                        widget.setToolTip(str(field.get("help") or ""))
                        self._set_invalid(widget, False)
                else:
                    config[name] = text
            elif isinstance(widget, QCheckBox):
                config[name] = widget.isChecked()
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                config[name] = widget.value()
            elif isinstance(widget, QComboBox):
                config[name] = widget.currentText().strip() if widget.isEditable() else widget.currentData()
        self._config = config
        if self._rendered_action_type:
            self._configs_by_type[self._rendered_action_type] = dict(config)

    def _apply_field_visibility(self) -> None:
        for name, widget in self.field_widgets.items():
            visible = self._field_is_visible(self._field_definitions.get(name, {}))
            widget.setVisible(visible)
            label = self.form.labelForField(widget)
            if label is not None:
                label.setVisible(visible)
            help_label = self._help_labels.get(name)
            if help_label is not None:
                help_label.setVisible(visible)

    def _field_is_visible(self, field: dict[str, Any]) -> bool:
        conditions = field.get("visible_if")
        if not isinstance(conditions, dict):
            return True
        for controller_name, expected in conditions.items():
            actual = self._config.get(controller_name)
            if isinstance(expected, Collection) and not isinstance(expected, (str, bytes, dict)):
                if actual not in expected:
                    return False
            elif actual != expected:
                return False
        return True

    def _browse(self, edit: QLineEdit, field_type: str) -> None:
        if field_type == "sound_file":
            path, _ = QFileDialog.getOpenFileName(self, "Choose Sound", "", "Audio files (*.wav *.mp3 *.ogg)")
        elif field_type == "file":
            path, _ = QFileDialog.getOpenFileName(self, "Choose File")
        else:
            path = QFileDialog.getExistingDirectory(self, "Choose Folder")
        if path:
            edit.setText(path)
            self._widget_changed()
