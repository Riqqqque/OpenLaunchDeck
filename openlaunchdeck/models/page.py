from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..constants import BUTTON_IDS
from .button import ButtonConfig


@dataclass(slots=True)
class Page:
    name: str
    id: str
    buttons: dict[str, ButtonConfig] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for button_id in BUTTON_IDS:
            self.buttons.setdefault(button_id, ButtonConfig.blank(button_id))

    @classmethod
    def blank(cls, name: str = "Main", page_id: str = "main") -> "Page":
        return cls(name=name, id=page_id)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "Page":
        if not isinstance(data, dict):
            return cls.blank()
        raw_buttons = data.get("buttons")
        buttons: dict[str, ButtonConfig] = {}
        if isinstance(raw_buttons, dict):
            for button_id in BUTTON_IDS:
                buttons[button_id] = ButtonConfig.from_dict(button_id, raw_buttons.get(button_id))
        return cls(
            name=str(data.get("name") or "Main"),
            id=str(data.get("id") or "main"),
            buttons=buttons,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "id": self.id,
            "buttons": {button_id: self.buttons[button_id].to_dict() for button_id in BUTTON_IDS},
        }

    def get_button(self, button_id: str) -> ButtonConfig:
        if button_id not in self.buttons:
            self.buttons[button_id] = ButtonConfig.blank(button_id)
        return self.buttons[button_id]
