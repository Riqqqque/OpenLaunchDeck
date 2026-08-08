from __future__ import annotations

from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ActionSequenceEditor(QWidget):
    changed = Signal()

    def __init__(self, registry, steps: Any = None, parent=None) -> None:
        super().__init__(parent)
        self.registry = registry
        self._steps: list[dict[str, Any]] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(7)
        self.list = QListWidget()
        self.list.setMinimumHeight(145)
        self.list.itemDoubleClicked.connect(lambda _item: self.edit_step())
        layout.addWidget(self.list)

        tools = QGridLayout()
        tools.setHorizontalSpacing(6)
        tools.setVerticalSpacing(6)
        self.add_button = QPushButton("Add Step")
        self.edit_button = QPushButton("Edit")
        self.up_button = QPushButton("Move Up")
        self.down_button = QPushButton("Move Down")
        self.remove_button = QPushButton("Remove")
        self.add_button.setObjectName("PrimaryButton")
        for button in (self.edit_button, self.up_button, self.down_button, self.remove_button):
            button.setObjectName("SecondaryButton")
        tools.addWidget(self.add_button, 0, 0, 1, 2)
        tools.addWidget(self.edit_button, 0, 2)
        tools.addWidget(self.remove_button, 0, 3)
        tools.addWidget(self.up_button, 1, 0, 1, 2)
        tools.addWidget(self.down_button, 1, 2, 1, 2)
        layout.addLayout(tools)

        self.add_button.clicked.connect(self.add_step)
        self.edit_button.clicked.connect(self.edit_step)
        self.up_button.clicked.connect(lambda: self.move_step(-1))
        self.down_button.clicked.connect(lambda: self.move_step(1))
        self.remove_button.clicked.connect(self.remove_step)
        self.list.currentRowChanged.connect(self._update_buttons)
        self.set_steps(steps)

    def set_steps(self, steps: Any) -> None:
        self._steps = []
        if isinstance(steps, list):
            for step in steps[:100]:
                if not isinstance(step, dict):
                    continue
                config = step.get("config")
                self._steps.append(
                    {
                        "type": str(step.get("type") or "noop"),
                        "config": dict(config) if isinstance(config, dict) else {},
                    }
                )
        if not self._steps:
            self._steps = [{"type": "noop", "config": {}}]
        self._refresh()

    def steps(self) -> list[dict[str, Any]]:
        return [{"type": step["type"], "config": dict(step["config"])} for step in self._steps]

    def add_step(self) -> None:
        result = self._edit_dialog("noop", {})
        if result is None:
            return
        self._steps.append(result)
        self._refresh(len(self._steps) - 1)
        self.changed.emit()

    def edit_step(self) -> None:
        row = self.list.currentRow()
        if row < 0 or row >= len(self._steps):
            return
        step = self._steps[row]
        result = self._edit_dialog(step["type"], step["config"])
        if result is None:
            return
        self._steps[row] = result
        self._refresh(row)
        self.changed.emit()

    def remove_step(self) -> None:
        row = self.list.currentRow()
        if row < 0 or row >= len(self._steps):
            return
        self._steps.pop(row)
        if not self._steps:
            self._steps.append({"type": "noop", "config": {}})
        self._refresh(min(row, len(self._steps) - 1))
        self.changed.emit()

    def move_step(self, offset: int) -> None:
        row = self.list.currentRow()
        target = row + offset
        if row < 0 or target < 0 or target >= len(self._steps):
            return
        self._steps[row], self._steps[target] = self._steps[target], self._steps[row]
        self._refresh(target)
        self.changed.emit()

    def _edit_dialog(self, action_type: str, config: dict[str, Any]) -> dict[str, Any] | None:
        from .action_editor import ActionEditor

        dialog = QDialog(self)
        dialog.setWindowTitle("Action Step")
        dialog.resize(560, 520)
        layout = QVBoxLayout(dialog)
        editor = ActionEditor(self.registry, allow_multi_action=False)
        editor.set_action(action_type, config)
        layout.addWidget(editor, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setObjectName("PrimaryButton")

        def save() -> None:
            errors = editor.validation_errors()
            if errors:
                QMessageBox.warning(dialog, "Invalid action step", "\n".join(errors[:5]))
                return
            dialog.accept()

        buttons.accepted.connect(save)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        selected_type, selected_config = editor.current_action()
        return {"type": selected_type, "config": selected_config}

    def _refresh(self, selected_row: int = 0) -> None:
        self.list.clear()
        for index, step in enumerate(self._steps, start=1):
            action = self.registry.get(step["type"])
            detail = self._step_detail(step["config"])
            self.list.addItem(f"{index}. {action.display_name}{'  -  ' + detail if detail else ''}")
        self.list.setCurrentRow(max(0, min(selected_row, len(self._steps) - 1)))
        self._update_buttons()

    @staticmethod
    def _step_detail(config: dict[str, Any]) -> str:
        for key in ("hotkey", "milliseconds", "operation", "url", "file_path", "text", "control", "page_id"):
            value = config.get(key)
            if value not in (None, "", False):
                text = str(value).replace("_", " ")
                return (text[:45] + "...") if len(text) > 48 else text
        return ""

    def _update_buttons(self, *_args) -> None:
        row = self.list.currentRow()
        valid = 0 <= row < len(self._steps)
        self.edit_button.setEnabled(valid)
        self.remove_button.setEnabled(valid)
        self.up_button.setEnabled(valid and row > 0)
        self.down_button.setEnabled(valid and row < len(self._steps) - 1)
