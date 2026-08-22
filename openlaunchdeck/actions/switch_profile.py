from __future__ import annotations

from .base import ActionResult, BaseAction


class SwitchProfileAction(BaseAction):
    type_name = "switch_profile"
    display_name = "Switch Profile"
    description = "Open a specific profile and its default page."
    config_fields = [
        {
            "name": "profile_id",
            "label": "Profile",
            "type": "choice",
            "choices": [],
            "help": "Choose one of the profiles stored in your OpenLaunchDeck library.",
        }
    ]

    def validate(self, config: dict) -> list[str]:
        return [] if config.get("profile_id") else ["Choose a profile."]

    def execute(self, context, config: dict) -> ActionResult:
        service = context.profile_service
        profile_id = str(config.get("profile_id") or "")
        if service is None:
            return ActionResult.fail("Profile service is unavailable.")
        old_profile_id = service.current_profile_id
        old_page_id = service.current_page_id
        if not service.set_current_profile(profile_id):
            return ActionResult.fail(f"Profile not found: {profile_id}")
        if context.settings_service is not None:
            context.settings_service.update(default_profile=profile_id)
        if context.audio_engine is not None and (
            old_profile_id != service.current_profile_id or old_page_id != service.current_page_id
        ):
            context.audio_engine.stop_page(old_page_id, only_page_change=True)
        return ActionResult.ok(
            f"Opened profile {service.current_profile.name}.",
            should_update_lighting=True,
            page_changed=True,
            profile_changed=True,
            profile_id=profile_id,
            page_id=service.current_page_id,
        )
