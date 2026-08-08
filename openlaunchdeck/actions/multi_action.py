from __future__ import annotations

from .base import ActionResult, BaseAction


class MultiAction(BaseAction):
    type_name = "multi_action"
    display_name = "Multi-Action"
    description = "Run several actions in order. Add Delay steps when timing between actions matters."
    config_fields = [
        {
            "name": "steps",
            "label": "Action Steps",
            "type": "action_list",
            "default": [{"type": "noop", "config": {}}],
            "help": "Add, edit, remove, and reorder each step. Every step uses the same guided action editor.",
        },
        {"name": "continue_on_error", "label": "Continue After A Failed Step", "type": "bool", "default": False},
    ]
    blocking = True

    def validate(self, config: dict) -> list[str]:
        steps = config.get("steps")
        if not isinstance(steps, list):
            return ["Multi-action steps must be a list."]
        if len(steps) > 100:
            return ["Multi-action is limited to 100 steps."]
        for index, step in enumerate(steps, start=1):
            if not isinstance(step, dict):
                return [f"Multi-action step {index} must be an object."]
            if not str(step.get("type") or "").strip():
                return [f"Multi-action step {index} needs an action type."]
            if "config" in step and not isinstance(step.get("config"), dict):
                return [f"Multi-action step {index} config must be an object."]
        return []

    def execute(self, context, config: dict) -> ActionResult:
        errors = self.validate(config)
        if errors:
            return ActionResult.fail(errors[0])
        steps = config.get("steps")
        if not isinstance(steps, list):
            return ActionResult.fail("Multi-action steps must be a list.")
        if context.action_registry is None:
            return ActionResult.fail("Action registry is unavailable.")
        continue_on_error = bool(config.get("continue_on_error", False))
        try:
            depth = max(0, int(config.get("_multi_depth", 0)))
        except (TypeError, ValueError):
            depth = 0
        if depth >= 8:
            return ActionResult.fail("Multi-action nesting is too deep.")
        results: list[str] = []
        details: dict = {}
        should_update_lighting = False
        for index, step in enumerate(steps, start=1):
            if not isinstance(step, dict):
                result = ActionResult.fail(f"Step {index} is not an action object.")
            else:
                action_type = str(step.get("type") or "noop")
                action_config = dict(step.get("config")) if isinstance(step.get("config"), dict) else {}
                if action_type == self.type_name:
                    action_config["_multi_depth"] = depth + 1
                if context.action_executor is not None:
                    result = context.action_executor(action_type, context, action_config)
                else:
                    result = context.action_registry.get(action_type).execute(context, action_config)
            results.append(f"{index}: {result.message}")
            should_update_lighting = should_update_lighting or result.should_update_lighting
            details.update(result.details)
            if not result.success and not continue_on_error:
                details["results"] = results
                return ActionResult(
                    False,
                    f"Multi-action stopped at step {index}: {result.message}",
                    details,
                    should_update_lighting,
                )
        details["results"] = results
        return ActionResult(True, "Multi-action complete.", details, should_update_lighting)
