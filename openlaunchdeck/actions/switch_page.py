from __future__ import annotations

from .base import ActionResult, BaseAction


class SwitchPageAction(BaseAction):
    type_name = "switch_page"
    display_name = "Switch Page"
    description = "Switch to another page in the current profile."
    config_fields = [
        {
            "name": "page_id",
            "label": "Page",
            "type": "choice",
            "choices": [],
            "help": "Choose a page from the current profile.",
        }
    ]

    def validate(self, config: dict) -> list[str]:
        return [] if config.get("page_id") else ["Page ID is required."]

    def execute(self, context, config: dict) -> ActionResult:
        page_id = str(config.get("page_id") or "")
        if not page_id:
            return ActionResult.fail("Choose a page to switch to.")
        if context.profile_service is None:
            return ActionResult.fail("Profile service is unavailable.")
        old_page_id = context.profile_service.current_page_id
        if not context.profile_service.set_current_page(page_id):
            return ActionResult.fail(f"Page not found: {page_id}")
        if context.audio_engine is not None and old_page_id != context.profile_service.current_page_id:
            context.audio_engine.stop_page(old_page_id, only_page_change=True)
        return ActionResult.ok(
            f"Switched to {page_id}.",
            should_update_lighting=True,
            page_changed=True,
            page_id=page_id,
        )
