from __future__ import annotations

import time

from .base import ActionResult, BaseAction


class DelayAction(BaseAction):
    type_name = "delay"
    display_name = "Delay"
    description = "Wait for a configured number of milliseconds."
    config_fields = [{"name": "milliseconds", "label": "Milliseconds", "type": "number"}]
    blocking = True

    def execute(self, context, config: dict) -> ActionResult:
        milliseconds = max(0, int(config.get("milliseconds", 250) or 0))
        time.sleep(milliseconds / 1000)
        return ActionResult.ok(f"Waited {milliseconds} ms.")
