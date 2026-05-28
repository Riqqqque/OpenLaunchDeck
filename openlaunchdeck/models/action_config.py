from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ActionConfig:
    type: str = "noop"
    config: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ActionConfig":
        if not isinstance(data, dict):
            return cls()
        action_type = str(data.get("type") or "noop")
        config = data.get("config")
        return cls(type=action_type, config=config if isinstance(config, dict) else {})

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type, "config": dict(self.config)}
