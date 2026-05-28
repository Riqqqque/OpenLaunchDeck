from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from collections.abc import Callable

from ..actions.base import ActionResult
from ..actions.context import ActionContext
from ..actions.registry import ActionRegistry
from ..models.button import ButtonConfig
from .dangerous_confirm import DangerousConfirmService
from .performance_monitor import PerformanceMonitor


class ActionRunner:
    def __init__(
        self,
        registry: ActionRegistry,
        profile_service,
        dangerous_service: DangerousConfirmService,
        audio_engine=None,
        lighting_service=None,
        device_manager=None,
        settings_service=None,
        logger=None,
        performance_monitor: PerformanceMonitor | None = None,
        completion_callback: Callable[[str, ActionResult], None] | None = None,
    ) -> None:
        self.registry = registry
        self.profile_service = profile_service
        self.dangerous_service = dangerous_service
        self.audio_engine = audio_engine
        self.lighting_service = lighting_service
        self.device_manager = device_manager
        self.settings_service = settings_service
        self.logger = logger
        self.performance_monitor = performance_monitor or PerformanceMonitor(logger)
        self.completion_callback = completion_callback
        self.executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="openlaunchdeck-action")

    def handle_button_press(self, button_id: str, source: str = "simulation") -> ActionResult:
        start = self.performance_monitor.now()
        page = self.profile_service.current_page
        button = page.get_button(button_id)
        if not button.enabled:
            result = ActionResult.fail("Button is disabled.")
            self._complete(button_id, result)
            return result
        if button.dangerous:
            confirmed = self.dangerous_service.arm_or_confirm(button_id)
            if not confirmed:
                result = ActionResult(False, "Press again within 5 seconds to run this action.", should_update_lighting=True)
                self._complete(button_id, result)
                return result
        result = self._dispatch(button_id, button, start, source)
        self.performance_monitor.record_since("button_press_total", start, source=source, button=button_id)
        return result

    def disarm_all(self) -> None:
        self.dangerous_service.disarm_all()

    def shutdown(self) -> None:
        self.executor.shutdown(wait=False, cancel_futures=True)

    def _dispatch(self, button_id: str, button: ButtonConfig, press_start: float, source: str) -> ActionResult:
        action_config = button.action
        action = self.registry.get(action_config.type if action_config else "noop")
        context = ActionContext(
            logger=self.logger,
            current_profile=self.profile_service.current_profile,
            current_page=self.profile_service.current_page,
            button_id=button_id,
            button_config=button,
            audio_engine=self.audio_engine,
            profile_service=self.profile_service,
            lighting_service=self.lighting_service,
            device_manager=self.device_manager,
            settings_service=self.settings_service,
            action_registry=self.registry,
        )
        config = dict(action_config.config if action_config else {})
        config.setdefault("_page_id", context.current_page.id)
        self.performance_monitor.record_since(
            "button_press_to_action_dispatch",
            press_start,
            source=source,
            button=button_id,
            action=action.type_name,
        )
        if action.blocking:
            self.executor.submit(self._run_action, button_id, action, context, config)
            result = ActionResult.ok("Action started.")
            self._complete(button_id, result)
            return result
        result = self._run_action(button_id, action, context, config)
        return result

    def _run_action(self, button_id: str, action, context: ActionContext, config: dict) -> ActionResult:
        with self.performance_monitor.measure(f"action:{action.type_name}"):
            try:
                result = action.execute(context, config)
            except Exception as exc:
                if self.logger:
                    self.logger.exception("Action failed: %s", action.type_name)
                result = ActionResult.fail(f"Action failed: {exc}")
        self._complete(button_id, result)
        return result

    def _complete(self, button_id: str, result: ActionResult) -> None:
        if self.logger:
            level = self.logger.info if result.success else self.logger.warning
            level("Button %s: %s", button_id, result.message)
        if self.completion_callback:
            self.completion_callback(button_id, result)
