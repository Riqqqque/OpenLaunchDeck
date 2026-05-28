from __future__ import annotations

from .base import ActionResult, BaseAction


class MultiAction(BaseAction):
    type_name = "multi_action"
    display_name = "Multi-Action"
    description = "Run multiple actions in sequence."
    config_fields = [
        {"name": "steps", "label": "Steps", "type": "json"},
        {"name": "continue_on_error", "label": "Continue On Error", "type": "bool"},
    ]
    blocking = True

    def execute(self, context, config: dict) -> ActionResult:
        steps = config.get("steps")
        if not isinstance(steps, list):
            return ActionResult.fail("Multi-action steps must be a list.")
        if context.action_registry is None:
            return ActionResult.fail("Action registry is unavailable.")
        continue_on_error = bool(config.get("continue_on_error", False))
        results: list[str] = []
        for index, step in enumerate(steps, start=1):
            if not isinstance(step, dict):
                result = ActionResult.fail(f"Step {index} is not an action object.")
            else:
                action_type = str(step.get("type") or "noop")
                action_config = step.get("config") if isinstance(step.get("config"), dict) else {}
                result = context.action_registry.get(action_type).execute(context, action_config)
            results.append(f"{index}: {result.message}")
            if not result.success and not continue_on_error:
                return ActionResult.fail(f"Multi-action stopped at step {index}: {result.message}", results=results)
        return ActionResult.ok("Multi-action complete.", results=results)
