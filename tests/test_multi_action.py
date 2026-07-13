import os
import logging
import threading
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QApplication

from openlaunchdeck.actions.base import ActionResult, BaseAction
from openlaunchdeck.actions.context import ActionContext
from openlaunchdeck.actions.registry import create_default_registry
from openlaunchdeck.models.action_config import ActionConfig
from openlaunchdeck.models.button import ButtonConfig
from openlaunchdeck.models.profile import Profile
from openlaunchdeck.services.action_runner import ActionRunner
from openlaunchdeck.services.dangerous_confirm import DangerousConfirmService


class MainThreadAction(BaseAction):
    type_name = "main_thread_test"

    def __init__(self) -> None:
        self.thread = None

    def execute(self, context, config):
        self.thread = QThread.currentThread()
        return ActionResult.ok("Main-thread step ran.", should_update_lighting=True, page_changed=True)


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


def test_runner_marshals_nonblocking_multi_action_steps_to_qt_thread():
    app = QApplication.instance() or QApplication([])
    registry = create_default_registry()
    main_thread_action = MainThreadAction()
    registry.register(main_thread_action)
    profile = Profile.blank()
    profile.get_page("main").buttons["A1"] = ButtonConfig(
        id="A1",
        action=ActionConfig(
            "multi_action",
            {"steps": [{"type": "main_thread_test", "config": {}}]},
        ),
    )

    class ProfileService:
        current_profile = profile
        current_page = profile.get_page("main")

    completed = threading.Event()
    results = []
    runner = ActionRunner(
        registry=registry,
        profile_service=ProfileService(),
        dangerous_service=DangerousConfirmService(),
        completion_callback=lambda _button_id, result: (results.append(result), completed.set()),
    )
    try:
        runner.handle_button_press("A1")
        deadline = time.monotonic() + 2
        while not completed.is_set() and time.monotonic() < deadline:
            app.processEvents()
            time.sleep(0.01)

        assert completed.is_set()
        assert main_thread_action.thread == app.thread()
        assert results[0].details["page_changed"] is True
        assert results[0].should_update_lighting is True
    finally:
        runner.shutdown()
