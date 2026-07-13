from __future__ import annotations

import time

from .base import ActionResult, BaseAction


class DelayAction(BaseAction):
    type_name = "delay"
    display_name = "Delay"
    description = "Wait for a configured number of milliseconds."
    config_fields = [{"name": "milliseconds", "label": "Milliseconds", "type": "number", "min": 0, "max": 60000}]
    blocking = True

    def execute(self, context, config: dict) -> ActionResult:
        try:
            milliseconds = max(0, min(60000, int(config.get("milliseconds", 250) or 0)))
        except (TypeError, ValueError):
            return ActionResult.fail("Delay must be a whole number of milliseconds.")
        time.sleep(milliseconds / 1000)
        return ActionResult.ok(f"Waited {milliseconds} ms.")
