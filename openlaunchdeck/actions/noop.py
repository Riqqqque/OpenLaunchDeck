from __future__ import annotations

from .base import ActionResult, BaseAction


class NoopAction(BaseAction):
    type_name = "noop"
    display_name = "No Action"
    description = "Do nothing."

    def execute(self, context, config: dict) -> ActionResult:
        return ActionResult.ok("No action assigned.")
