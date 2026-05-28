from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ActionResult:
    success: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    should_update_lighting: bool = False

    @classmethod
    def ok(
        cls,
        message: str = "Done.",
        should_update_lighting: bool = False,
        **details: Any,
    ) -> "ActionResult":
        return cls(True, message, details, should_update_lighting)

    @classmethod
    def fail(
        cls,
        message: str,
        should_update_lighting: bool = False,
        **details: Any,
    ) -> "ActionResult":
        return cls(False, message, details, should_update_lighting)


class BaseAction:
    type_name = "noop"
    display_name = "No Action"
    description = "Does nothing."
    config_fields: list[dict[str, Any]] = []
    blocking = False

    def validate(self, config: dict[str, Any]) -> list[str]:
        return []

    def execute(self, context: Any, config: dict[str, Any]) -> ActionResult:
        raise NotImplementedError
