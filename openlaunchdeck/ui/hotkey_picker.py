from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QCompleter, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ..actions.hotkey import normalize_key_name, parse_hotkey


HOTKEY_MODIFIERS = ("ctrl", "alt", "win", "shift")
HOTKEY_MODIFIER_LABELS = {
    "ctrl": "Ctrl",
    "alt": "Alt",
    "shift": "Shift",
    "win": "Win",
}
HOTKEY_KEY_LABELS = {
    "backspace": "Backspace",
    "tab": "Tab",
    "enter": "Enter",
    "escape": "Escape",
    "space": "Space",
    "capslock": "Caps Lock",
    "pageup": "Page Up",
    "pagedown": "Page Down",
    "end": "End",
    "home": "Home",
    "left": "Left Arrow",
    "up": "Up Arrow",
    "right": "Right Arrow",
    "down": "Down Arrow",
    "printscreen": "Print Screen",
    "insert": "Insert",
    "delete": "Delete",
    "pause": "Pause / Break",
    "apps": "Menu Key",
    "numlock": "Num Lock",
    "scrolllock": "Scroll Lock",
    "semicolon": "; Semicolon",
    "equals": "= / +",
    "comma": ", Comma",
    "minus": "- Minus",
    "period": ". Period",
    "slash": "/ Slash",
    "backtick": "` Backtick",
    "left_bracket": "[ Left Bracket",
    "backslash": "\\ Backslash",
    "right_bracket": "] Right Bracket",
    "quote": "' Quote",
    "volume_mute": "Volume Mute",
    "volume_down": "Volume Down",
    "volume_up": "Volume Up",
    "media_previous": "Previous Track",
    "media_play_pause": "Play / Pause",
    "media_next": "Next Track",
    "media_stop": "Stop Media",
}


def _key_label(key: str) -> str:
    if key in HOTKEY_KEY_LABELS:
        return HOTKEY_KEY_LABELS[key]
    if len(key) == 1 or (key.startswith("f") and key[1:].isdigit()):
        return key.upper()
    return key.replace("_", " ").title()


class HotkeyPicker(QWidget):
    changed = Signal()

    def __init__(self, keys: list[str], value: Any = None) -> None:
        super().__init__()
        self.setObjectName("HotkeyPicker")
        self._loading = False
        self._custom_full_value = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(7)

        modifier_row = QHBoxLayout()
        modifier_row.setContentsMargins(0, 0, 0, 0)
        modifier_row.setSpacing(8)
        self.modifier_checks: dict[str, QCheckBox] = {}
        for modifier in ("ctrl", "alt", "shift", "win"):
            check = QCheckBox(HOTKEY_MODIFIER_LABELS[modifier])
            check.setObjectName("HotkeyModifier")
            check.toggled.connect(self._emit_changed)
            self.modifier_checks[modifier] = check
            modifier_row.addWidget(check)
        modifier_row.addStretch(1)
        layout.addLayout(modifier_row)

        self.key_combo = QComboBox()
        self.key_combo.setEditable(True)
        self.key_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.key_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.key_combo.setMinimumContentsLength(12)
        self.key_combo.setMaxVisibleItems(18)
        self.key_combo.addItem("Choose a key...", "")
        self._label_to_key: dict[str, str] = {}
        seen: set[str] = set()
        for raw_key in keys:
            key = normalize_key_name(str(raw_key))
            if not key or key in HOTKEY_MODIFIERS or key in seen:
                continue
            seen.add(key)
            label = _key_label(key)
            self._label_to_key[label.casefold()] = key
            self.key_combo.addItem(label, key)
        labels = [self.key_combo.itemText(index) for index in range(1, self.key_combo.count())]
        completer = QCompleter(labels, self.key_combo)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.key_combo.setCompleter(completer)
        if self.key_combo.lineEdit() is not None:
            self.key_combo.lineEdit().setPlaceholderText("Choose or search keys")
        self.key_combo.currentIndexChanged.connect(self._emit_changed)
        self.key_combo.editTextChanged.connect(self._emit_changed)
        layout.addWidget(self.key_combo)

        self.preview = QLabel()
        self.preview.setObjectName("HotkeyPreview")
        layout.addWidget(self.preview)
        self.set_value(value)

    def set_value(self, value: Any) -> None:
        self._loading = True
        self._custom_full_value = ""
        raw_value = str(value or "").strip()
        keys = parse_hotkey(raw_value)
        for modifier, check in self.modifier_checks.items():
            check.setChecked(modifier in keys)
        primary_keys = [key for key in keys if key not in HOTKEY_MODIFIERS]
        if len(primary_keys) == 1:
            primary = primary_keys[0]
            index = self.key_combo.findData(primary)
            if index < 0:
                self.key_combo.addItem(f"Custom: {primary}", primary)
                index = self.key_combo.count() - 1
            self.key_combo.setCurrentIndex(index)
        elif raw_value:
            self._custom_full_value = raw_value
            self.key_combo.addItem(f"Existing custom: {raw_value}", raw_value)
            self.key_combo.setCurrentIndex(self.key_combo.count() - 1)
        else:
            self.key_combo.setCurrentIndex(0)
        self._loading = False
        self._update_preview()

    def value(self) -> str:
        current_text = self.key_combo.currentText().strip()
        current_index = self.key_combo.currentIndex()
        selected = ""
        if current_index >= 0 and current_text.casefold() == self.key_combo.itemText(current_index).casefold():
            selected = str(self.key_combo.itemData(current_index) or "").strip()
        if self._custom_full_value and selected == self._custom_full_value:
            return self._custom_full_value
        if not selected:
            selected = self._label_to_key.get(current_text.casefold(), normalize_key_name(current_text))
        if not selected or selected == "choose_a_key...":
            return ""
        modifiers = [modifier for modifier in HOTKEY_MODIFIERS if self.modifier_checks[modifier].isChecked()]
        return "+".join([*modifiers, selected])

    def _emit_changed(self, *_args: Any) -> None:
        if self._loading:
            return
        self._custom_full_value = ""
        self._update_preview()
        self.changed.emit()

    def _update_preview(self) -> None:
        value = self.value()
        if not value:
            self.preview.setText("No hotkey selected")
            return
        display = [HOTKEY_MODIFIER_LABELS.get(key, _key_label(key)) for key in parse_hotkey(value)]
        self.preview.setText(" + ".join(display))
