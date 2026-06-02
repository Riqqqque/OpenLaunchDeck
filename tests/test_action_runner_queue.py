import threading

from openlaunchdeck.actions.base import ActionResult, BaseAction
from openlaunchdeck.actions.registry import ActionRegistry
from openlaunchdeck.actions.noop import NoopAction
from openlaunchdeck.models.action_config import ActionConfig
from openlaunchdeck.models.button import ButtonConfig
from openlaunchdeck.models.page import Page
from openlaunchdeck.models.profile import Profile
from openlaunchdeck.services.action_runner import ActionRunner
from openlaunchdeck.services.dangerous_confirm import DangerousConfirmService


class SlowAction(BaseAction):
    type_name = "slow"
    blocking = True

    def __init__(self, started: threading.Event, release: threading.Event) -> None:
        self.started = started
        self.release = release

    def execute(self, context, config):
        self.started.set()
        self.release.wait(timeout=2)
        return ActionResult.ok("Slow action finished.")


class FakeProfileService:
    def __init__(self) -> None:
        page = Page.blank()
        page.buttons["A1"] = ButtonConfig(id="A1", action=ActionConfig("slow", {}))
        self.current_page = page
        self.current_profile = Profile("Test", "test", [page], page.id)


def test_action_runner_rejects_when_background_queue_is_full():
    started = threading.Event()
    release = threading.Event()
    registry = ActionRegistry()
    registry.register(NoopAction())
    registry.register(SlowAction(started, release))
    runner = ActionRunner(
        registry=registry,
        profile_service=FakeProfileService(),
        dangerous_service=DangerousConfirmService(),
        max_workers=1,
        max_pending=1,
    )

    try:
        first = runner.handle_button_press("A1")
        assert first.success
        assert started.wait(timeout=1)

        second = runner.handle_button_press("A1")

        assert not second.success
        assert "busy" in second.message.lower()
    finally:
        release.set()
        runner.shutdown()


def test_blocking_action_completion_waits_for_actual_result():
    started = threading.Event()
    release = threading.Event()
    completions = []
    registry = ActionRegistry()
    registry.register(NoopAction())
    registry.register(SlowAction(started, release))
    runner = ActionRunner(
        registry=registry,
        profile_service=FakeProfileService(),
        dangerous_service=DangerousConfirmService(),
        completion_callback=lambda button_id, result: completions.append((button_id, result.message)),
        max_workers=1,
        max_pending=1,
    )

    try:
        result = runner.handle_button_press("A1")

        assert result.success
        assert result.message == "Action started."
        assert started.wait(timeout=1)
        assert completions == []

        release.set()
        deadline = threading.Event()
        deadline.wait(timeout=0.1)

        for _ in range(20):
            if completions:
                break
            deadline.wait(timeout=0.05)

        assert completions == [("A1", "Slow action finished.")]
    finally:
        release.set()
        runner.shutdown()
