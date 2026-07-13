from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import threading
import time

from ..constants import BUTTON_IDS
from .performance_monitor import PerformanceMonitor


@dataclass(slots=True)
class _BlinkState:
    color_a: str
    color_b: str
    period: float
    next_change: float
    showing_a: bool = True


class LightingService:
    def __init__(
        self,
        device=None,
        logger=None,
        performance_monitor: PerformanceMonitor | None = None,
        async_output: bool = False,
    ) -> None:
        self.device = device
        self.logger = logger
        self.performance_monitor = performance_monitor or PerformanceMonitor(logger)
        self._last_colors: dict[str, str] = {}
        self._blinks: dict[str, _BlinkState] = {}
        self._flash_restores: dict[str, tuple[float, str]] = {}
        self._lock = threading.RLock()
        self._scheduler_condition = threading.Condition(self._lock)
        self._scheduler_thread: threading.Thread | None = None
        self._shutdown_requested = False
        self._pending_colors: dict[str, str] = {}
        self._output_scheduled = False
        self._executor = (
            ThreadPoolExecutor(max_workers=1, thread_name_prefix="openlaunchdeck-lighting")
            if async_output
            else None
        )

    def set_device(self, device) -> None:
        self.device = device

    def refresh_page(self, page, audio_engine=None, dangerous_service=None, force: bool = False) -> None:
        if not self.device or not getattr(self.device, "connected", False):
            return
        start = time.perf_counter()
        colors = self.build_page_colors(page, audio_engine, dangerous_service)
        with self._lock:
            for button_id, (deadline, _restore_color) in list(self._flash_restores.items()):
                if button_id in colors:
                    self._flash_restores[button_id] = (deadline, colors[button_id])
            changed = colors if force else {button_id: color for button_id, color in colors.items() if self._last_colors.get(button_id) != color}
            if not changed:
                if self.logger:
                    self.logger.debug("Lighting refresh skipped; no pad color changes.")
                return
            self._last_colors = dict(colors)
            self._send_many(changed)
            elapsed_ms = (time.perf_counter() - start) * 1000
            self.performance_monitor.record("lighting_refresh", elapsed_ms, pads=len(changed))
            if self.logger:
                self.logger.debug("Lighting refresh pads=%s elapsed=%.3f ms", len(changed), elapsed_ms)

    def build_page_colors(self, page, audio_engine=None, dangerous_service=None) -> dict[str, str]:
        colors: dict[str, str] = {}
        playing_buttons = None
        if audio_engine is not None and hasattr(audio_engine, "playing_button_ids"):
            playing_buttons = audio_engine.playing_button_ids()
        for button_id in BUTTON_IDS:
            button = page.get_button(button_id)
            if not button.enabled:
                colors[button_id] = "off"
            elif dangerous_service is not None and dangerous_service.is_armed(button_id):
                colors[button_id] = "yellow"
            elif playing_buttons is not None and button_id in playing_buttons:
                colors[button_id] = button.active_color
            elif playing_buttons is None and audio_engine is not None and audio_engine.is_button_playing(button_id):
                colors[button_id] = button.active_color
            else:
                colors[button_id] = button.color
        return colors

    def flash(self, button_id: str, color: str, delay: float = 0.2) -> None:
        if not self.device or not getattr(self.device, "connected", False):
            return
        start = time.perf_counter()
        restore_color = self._last_colors.get(button_id, "off")
        self._send_one(button_id, color)
        elapsed_ms = (time.perf_counter() - start) * 1000
        self.performance_monitor.record("lighting_flash", elapsed_ms, button=button_id, color=color)
        if self.logger:
            self.logger.debug("Lighting flash %s color=%s elapsed=%.3f ms", button_id, color, elapsed_ms)
        with self._scheduler_condition:
            self._flash_restores[button_id] = (time.monotonic() + max(0.01, delay), restore_color)
            self._ensure_scheduler_locked()
            self._scheduler_condition.notify()

    def blink(self, button_id: str, color_a: str = "yellow", color_b: str = "red", period: float = 0.45) -> None:
        if not self.device or not getattr(self.device, "connected", False):
            return
        with self._scheduler_condition:
            if button_id in self._blinks:
                return
            safe_period = max(0.05, period)
            self._flash_restores.pop(button_id, None)
            self._blinks[button_id] = _BlinkState(
                color_a=color_a,
                color_b=color_b,
                period=safe_period,
                next_change=time.monotonic() + safe_period,
            )
            self._ensure_scheduler_locked()
            self._scheduler_condition.notify()
        self._send_one(button_id, color_a)

    def stop_blink(self, button_id: str) -> None:
        with self._scheduler_condition:
            self._blinks.pop(button_id, None)
            self._flash_restores.pop(button_id, None)
            restore_color = self._last_colors.get(button_id)
            self._scheduler_condition.notify()
        if restore_color and self.device and getattr(self.device, "connected", False):
            self._send_one(button_id, restore_color)

    def stop_all_blinks(self) -> None:
        with self._scheduler_condition:
            button_ids = list(self._blinks)
            self._blinks.clear()
            for button_id in button_ids:
                self._flash_restores.pop(button_id, None)
            restore_colors = {
                button_id: self._last_colors[button_id]
                for button_id in button_ids
                if button_id in self._last_colors
            }
            self._scheduler_condition.notify()
        if restore_colors:
            self._send_many(restore_colors)

    def clear(self) -> None:
        if self.device and getattr(self.device, "connected", False):
            with self._lock:
                self._pending_colors.clear()
            self._submit_raw(self.device.clear_all_pads)
        with self._lock:
            self._last_colors.clear()

    def shutdown(self) -> None:
        with self._scheduler_condition:
            self._shutdown_requested = True
            self._blinks.clear()
            self._flash_restores.clear()
            scheduler_thread = self._scheduler_thread
            self._scheduler_condition.notify_all()
        if scheduler_thread is not None and scheduler_thread is not threading.current_thread():
            scheduler_thread.join(timeout=1.0)
        if self._executor is not None:
            self._executor.shutdown(wait=True, cancel_futures=True)

    def _ensure_scheduler_locked(self) -> None:
        if self._scheduler_thread is not None and self._scheduler_thread.is_alive():
            return
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            name="openlaunchdeck-lighting-timer",
            daemon=True,
        )
        self._scheduler_thread.start()

    def _scheduler_loop(self) -> None:
        while True:
            colors: dict[str, str] = {}
            with self._scheduler_condition:
                while not self._shutdown_requested and not self._blinks and not self._flash_restores:
                    self._scheduler_condition.wait()
                if self._shutdown_requested:
                    return

                now = time.monotonic()
                deadlines = [state.next_change for state in self._blinks.values()]
                deadlines.extend(deadline for deadline, _color in self._flash_restores.values())
                next_deadline = min(deadlines)
                if next_deadline > now:
                    self._scheduler_condition.wait(timeout=next_deadline - now)
                    continue

                now = time.monotonic()
                for button_id, (deadline, restore_color) in list(self._flash_restores.items()):
                    if deadline > now:
                        continue
                    self._flash_restores.pop(button_id, None)
                    if button_id not in self._blinks:
                        colors[button_id] = restore_color

                for button_id, state in self._blinks.items():
                    if state.next_change > now:
                        continue
                    state.showing_a = not state.showing_a
                    state.next_change = now + state.period
                    colors[button_id] = state.color_a if state.showing_a else state.color_b

            if colors and self.device and getattr(self.device, "connected", False):
                self._send_many(colors)

    def _send_many(self, colors: dict[str, str]) -> None:
        if not self.device or not getattr(self.device, "connected", False):
            return
        if self._executor is None:
            self._send_many_now(dict(colors))
            return
        with self._lock:
            self._pending_colors.update(colors)
            if self._output_scheduled:
                return
            self._output_scheduled = True
        try:
            self._executor.submit(self._drain_pending_colors)
        except RuntimeError:
            with self._lock:
                self._output_scheduled = False
            if self.logger:
                self.logger.debug("Lighting update skipped because the output worker is shutting down.")

    def _drain_pending_colors(self) -> None:
        while True:
            with self._lock:
                if not self._pending_colors:
                    self._output_scheduled = False
                    return
                colors = dict(self._pending_colors)
                self._pending_colors.clear()
            self._send_many_now(colors)

    def _send_many_now(self, colors: dict[str, str]) -> None:
        start = time.perf_counter()
        try:
            if self.device and getattr(self.device, "connected", False):
                self.device.set_many_pad_colors(colors)
        except Exception:
            if self.logger:
                self.logger.exception("Could not refresh Launchpad lighting.")
        finally:
            self.performance_monitor.record_since("lighting_output", start, pads=len(colors))

    def _send_one(self, button_id: str, color: str) -> None:
        self._send_many({button_id: color})

    def _submit_raw(self, func, *args) -> None:
        if self._executor is None:
            func(*args)
            return
        try:
            self._executor.submit(func, *args)
        except RuntimeError:
            if self.logger:
                self.logger.debug("Lighting update skipped because the output worker is shutting down.")
