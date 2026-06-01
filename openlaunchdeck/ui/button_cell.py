from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QPushButton

from ..constants import NAMED_COLORS
from ..models.button import ButtonConfig


class ButtonCell(QPushButton):
    def __init__(self, button_id: str) -> None:
        super().__init__()
        self.button_id = button_id
        self.setMinimumSize(QSize(82, 72))
        self.setCheckable(True)
        self.setToolTip(button_id)
        self._selected = False
        self._armed = False
        self._playing = False
        self._state_key: tuple | None = None

    def set_state(self, button: ButtonConfig, selected: bool = False, armed: bool = False, playing: bool = False) -> None:
        action_type = button.action.type if button.action else "noop"
        label = button.label or "Empty"
        color = button.active_color if playing else button.color
        if armed:
            color = "yellow"
        if not button.enabled:
            color = "off"
        state_key = (
            button.id,
            label,
            action_type,
            button.enabled,
            color,
            selected,
            armed,
            playing,
        )
        if state_key == self._state_key:
            return
        self._state_key = state_key
        self._selected = selected
        self._armed = armed
        self._playing = playing
        self.setText(f"{button.id}\n{label}\n{action_type}")
        self.setEnabled(True)
        background = NAMED_COLORS.get(color, color if color.startswith("#") else NAMED_COLORS["dim"])
        border = "#f5f7fb" if selected else ("#facc15" if armed else "#303846")
        text_color = "#f5f7fb" if color not in {"white", "yellow"} else "#111827"
        if not button.enabled:
            background = "#12151b"
            text_color = "#7b8494"
        self.setStyleSheet(
            f"""
            QPushButton {{
                background: {background};
                border: 2px solid {border};
                border-radius: 8px;
                color: {text_color};
                font-weight: 700;
                padding: 6px;
                text-align: center;
            }}
            QPushButton:pressed {{
                border-color: #ffffff;
            }}
            """
        )
