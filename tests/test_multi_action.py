import logging

from openlaunchdeck.actions.context import ActionContext
from openlaunchdeck.actions.registry import create_default_registry
from openlaunchdeck.models.button import ButtonConfig
from openlaunchdeck.models.profile import Profile


def test_multi_action_runs_steps():
    registry = create_default_registry()
    profile = Profile.blank()
    page = profile.get_page("main")
    context = ActionContext(
        logger=logging.getLogger("test"),
        current_profile=profile,
        current_page=page,
        button_id="A1",
        button_config=ButtonConfig.blank("A1"),
        action_registry=registry,
    )

    result = registry.get("multi_action").execute(
        context,
        {
            "continue_on_error": False,
            "steps": [
                {"type": "noop", "config": {}},
                {"type": "delay", "config": {"milliseconds": 0}},
            ],
        },
    )

    assert result.success is True
