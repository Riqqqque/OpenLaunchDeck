from __future__ import annotations

import threading
from concurrent.futures import Future, ThreadPoolExecutor
from collections.abc import Callable

from ..actions.base import ActionResult
from ..actions.context import ActionContext
from ..actions.registry import ActionRegistry
from ..models.button import ButtonConfig
from .dangerous_confirm import DangerousConfirmService
from .performance_monitor import PerformanceMonitor
from .qt_dispatch import MainThreadDispatcher


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
        max_workers: int = 2,
        max_pending: int = 8,
        interactive_workers: int = 1,
        max_interactive_pending: int = 16,
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
        self.executor = ThreadPoolExecutor(max_workers=max(1, max_workers), thread_name_prefix="openlaunchdeck-action")
        self.interactive_executor = ThreadPoolExecutor(
            max_workers=max(1, interactive_workers),
            thread_name_prefix="openlaunchdeck-input",
        )
        self._pending_limits = {
            "background": max(1, max_pending),
            "interactive": max(1, max_interactive_pending),
        }
        self._pending_limit = self._pending_limits["background"]
        self._pending_counts = {"background": 0, "interactive": 0}
        self._pending_lock = threading.Lock()
        self._shutting_down = False
        self._main_thread = MainThreadDispatcher()

    def handle_button_press(self, button_id: str, source: str = "simulation") -> ActionResult:
        with self._pending_lock:
            if self._shutting_down:
                return ActionResult.fail("OpenLaunchDeck is shutting down.")
        start = self.performance_monitor.now()
        page = self.profile_service.current_page
        button = page.get_button(button_id)
        if not button.enabled:
            result = ActionResult.fail("Button is disabled.")
            self._complete(button_id, result)
            return result
        if self._requires_confirmation(button):
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
        with self._pending_lock:
            self._shutting_down = True
        self.completion_callback = None
        self.executor.shutdown(wait=False, cancel_futures=True)
        self.interactive_executor.shutdown(wait=False, cancel_futures=True)

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
            action_executor=self._execute_nested_action,
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
            lane = "interactive" if getattr(action, "execution_lane", "background") == "interactive" else "background"
            if not self._try_reserve_action_slot(lane):
                result = ActionResult.fail(f"{lane.title()} action queue is busy. Try again in a moment.")
                self._complete(button_id, result)
                return result
            executor = self.interactive_executor if lane == "interactive" else self.executor
            try:
                future = executor.submit(self._run_action, button_id, action, context, config)
            except RuntimeError:
                self._release_action_slot(None, lane)
                result = ActionResult.fail("OpenLaunchDeck is shutting down.")
                self._complete(button_id, result)
                return result
            future.add_done_callback(lambda completed, selected_lane=lane: self._release_action_slot(completed, selected_lane))
            return ActionResult.ok("Action started.")
        result = self._run_action(button_id, action, context, config)
        return result

    @staticmethod
    def _requires_confirmation(button: ButtonConfig) -> bool:
        if button.dangerous:
            return True
        action_config = button.action
        if not action_config:
            return False
        action_type = str(action_config.type or "").strip()
        operation = str(action_config.config.get("operation") or "").strip()
        return action_type == "obs_websocket" and operation == "start_streaming"

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
            if result.success:
                self.logger.info("Button %s: %s", button_id, result.message)
            else:
                self.logger.warning("Button %s: %s", button_id, result.message)
        if self.completion_callback:
            self.completion_callback(button_id, result)

    def _try_reserve_action_slot(self, lane: str) -> bool:
        with self._pending_lock:
            if self._shutting_down or self._pending_counts[lane] >= self._pending_limits[lane]:
                return False
            self._pending_counts[lane] += 1
            return True

    def _release_action_slot(self, _future: Future | None, lane: str) -> None:
        with self._pending_lock:
            self._pending_counts[lane] = max(0, self._pending_counts[lane] - 1)

    def _execute_nested_action(self, action_type: str, context: ActionContext, config: dict) -> ActionResult:
        action = self.registry.get(action_type)
        if action.blocking:
            return action.execute(context, config)
        return self._main_thread.call(lambda: action.execute(context, config))
