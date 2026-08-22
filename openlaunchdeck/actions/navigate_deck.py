from __future__ import annotations

from .base import ActionResult, BaseAction

NAVIGATION_OPERATIONS = [
    ("Previous Page", "previous_page"),
    ("Next Page", "next_page"),
    ("First Page", "first_page"),
    ("Last Page", "last_page"),
    ("Default Page", "default_page"),
    ("Previous Profile", "previous_profile"),
    ("Next Profile", "next_profile"),
]


class NavigateDeckAction(BaseAction):
    type_name = "navigate_deck"
    display_name = "Navigate Deck"
    description = "Move between pages or profiles without hard-coding a destination."
    config_fields = [
        {
            "name": "operation",
            "label": "Move To",
            "type": "choice",
            "choices": NAVIGATION_OPERATIONS,
            "default": "next_page",
        },
        {
            "name": "wrap",
            "label": "Wrap At The End",
            "type": "bool",
            "default": True,
        },
    ]

    def validate(self, config: dict) -> list[str]:
        valid = {value for _label, value in NAVIGATION_OPERATIONS}
        return [] if str(config.get("operation") or "next_page") in valid else ["Choose a valid deck navigation operation."]

    def execute(self, context, config: dict) -> ActionResult:
        service = context.profile_service
        if service is None:
            return ActionResult.fail("Profile service is unavailable.")
        operation = str(config.get("operation") or "next_page")
        wrap = bool(config.get("wrap", True))
        old_profile_id = service.current_profile_id
        old_page_id = service.current_page_id

        if operation in {"previous_page", "next_page", "first_page", "last_page", "default_page"}:
            pages = service.current_profile.pages
            page_ids = [page.id for page in pages]
            if not page_ids:
                return ActionResult.fail("The current profile has no pages.")
            if operation == "default_page":
                target_id = service.current_profile.default_page
            elif operation == "first_page":
                target_id = page_ids[0]
            elif operation == "last_page":
                target_id = page_ids[-1]
            else:
                offset = -1 if operation == "previous_page" else 1
                current_index = page_ids.index(service.current_page_id) if service.current_page_id in page_ids else 0
                target_index = current_index + offset
                if not wrap and not 0 <= target_index < len(page_ids):
                    return ActionResult.fail("Already at the first page." if offset < 0 else "Already at the last page.")
                target_id = page_ids[target_index % len(page_ids)]
            if not service.set_current_page(target_id):
                return ActionResult.fail("The target page is unavailable.")
            if old_page_id != service.current_page_id:
                self._stop_old_page(context, old_page_id)
            return ActionResult.ok(
                f"Opened page {service.current_page.name}.",
                should_update_lighting=True,
                page_changed=True,
                page_id=target_id,
            )

        profile_ids = list(service.profiles)
        if not profile_ids:
            return ActionResult.fail("No profiles are available.")
        offset = -1 if operation == "previous_profile" else 1
        current_index = profile_ids.index(service.current_profile_id) if service.current_profile_id in profile_ids else 0
        target_index = current_index + offset
        if not wrap and not 0 <= target_index < len(profile_ids):
            return ActionResult.fail("Already at the first profile." if offset < 0 else "Already at the last profile.")
        target_id = profile_ids[target_index % len(profile_ids)]
        if not service.set_current_profile(target_id):
            return ActionResult.fail("The target profile is unavailable.")
        if context.settings_service is not None:
            context.settings_service.update(default_profile=target_id)
        if old_profile_id != service.current_profile_id or old_page_id != service.current_page_id:
            self._stop_old_page(context, old_page_id)
        return ActionResult.ok(
            f"Opened profile {service.current_profile.name}.",
            should_update_lighting=True,
            page_changed=True,
            profile_changed=True,
            profile_id=target_id,
            page_id=service.current_page_id,
        )

    @staticmethod
    def _stop_old_page(context, page_id: str) -> None:
        if context.audio_engine is not None:
            context.audio_engine.stop_page(page_id, only_page_change=True)
