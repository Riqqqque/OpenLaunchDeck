from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..constants import DEFAULT_BUTTON_COLOR
from .action_config import ActionConfig


def _bool_value(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off", ""}:
            return False
    return default


@dataclass(slots=True)
class ButtonConfig:
    id: str
    label: str = ""
    color: str = DEFAULT_BUTTON_COLOR
    enabled: bool = True
    dangerous: bool = False
    notes: str = ""
    icon_path: str = ""
    icon_name: str = ""
    action: ActionConfig | None = None
    press_behavior: str = "press"
    release_behavior: str = "none"
    active_color: str = "cyan"
    success_color: str = "green"
    error_color: str = "red"

    def __post_init__(self) -> None:
        if self.action is None:
            self.action = ActionConfig()

    @classmethod
    def blank(cls, button_id: str) -> "ButtonConfig":
        return cls(id=button_id, label="", color="dim", action=ActionConfig())

    @classmethod
    def from_dict(cls, button_id: str, data: dict[str, Any] | None) -> "ButtonConfig":
        if not isinstance(data, dict):
            return cls.blank(button_id)
        return cls(
            id=button_id,
            label=str(data.get("label") or ""),
            color=str(data.get("color") or DEFAULT_BUTTON_COLOR),
            enabled=_bool_value(data.get("enabled", True), True),
            dangerous=_bool_value(data.get("dangerous", False), False),
            notes=str(data.get("notes") or ""),
            icon_path=str(data.get("icon_path") or ""),
            icon_name=str(data.get("icon_name") or ""),
            action=ActionConfig.from_dict(data.get("action")),
            press_behavior=str(data.get("press_behavior") or "press"),
            release_behavior=str(data.get("release_behavior") or "none"),
            active_color=str(data.get("active_color") or "cyan"),
            success_color=str(data.get("success_color") or "green"),
            error_color=str(data.get("error_color") or "red"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "color": self.color,
            "enabled": self.enabled,
            "dangerous": self.dangerous,
            "notes": self.notes,
            "icon_path": self.icon_path,
            "icon_name": self.icon_name,
            "action": self.action.to_dict() if self.action else ActionConfig().to_dict(),
            "press_behavior": self.press_behavior,
            "release_behavior": self.release_behavior,
            "active_color": self.active_color,
            "success_color": self.success_color,
            "error_color": self.error_color,
        }
