from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import threading
import time

from ..constants import BUTTON_IDS
from .performance_monitor import PerformanceMonitor


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
        self._blink_timers: dict[str, threading.Timer] = {}
        self._blink_states: dict[str, bool] = {}
        self._lock = threading.RLock()
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
        for button_id in BUTTON_IDS:
            button = page.get_button(button_id)
            if not button.enabled:
                colors[button_id] = "off"
            elif dangerous_service is not None and dangerous_service.is_armed(button_id):
                colors[button_id] = "yellow"
            elif audio_engine is not None and audio_engine.is_button_playing(button_id):
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
        timer = threading.Timer(delay, self._restore_after_flash, args=(button_id, restore_color))
        timer.daemon = True
        timer.start()

    def blink(self, button_id: str, color_a: str = "yellow", color_b: str = "red", period: float = 0.45) -> None:
        if not self.device or not getattr(self.device, "connected", False):
            return
        with self._lock:
            if button_id in self._blink_timers:
                return
            self._blink_states[button_id] = False
            self._send_one(button_id, color_a)
            self._schedule_blink(button_id, color_a, color_b, period)

    def stop_blink(self, button_id: str) -> None:
        with self._lock:
            timer = self._blink_timers.pop(button_id, None)
            self._blink_states.pop(button_id, None)
            if timer:
                timer.cancel()
            restore_color = self._last_colors.get(button_id)
        if restore_color and self.device and getattr(self.device, "connected", False):
            self._send_one(button_id, restore_color)

    def stop_all_blinks(self) -> None:
        for button_id in list(self._blink_timers):
            self.stop_blink(button_id)

    def clear(self) -> None:
        if self.device and getattr(self.device, "connected", False):
            self._submit(self.device.clear_all_pads)
        with self._lock:
            self._last_colors.clear()

    def shutdown(self) -> None:
        with self._lock:
            timers = list(self._blink_timers.values())
            self._blink_timers.clear()
            self._blink_states.clear()
        for timer in timers:
            timer.cancel()
        if self._executor is not None:
            self._executor.shutdown(wait=False, cancel_futures=True)

    def _restore_after_flash(self, button_id: str, restore_color: str) -> None:
        with self._lock:
            if button_id in self._blink_timers:
                return
        if self.device and getattr(self.device, "connected", False):
            self._send_one(button_id, restore_color)

    def _schedule_blink(self, button_id: str, color_a: str, color_b: str, period: float) -> None:
        timer = threading.Timer(period, self._blink_once, args=(button_id, color_a, color_b, period))
        timer.daemon = True
        self._blink_timers[button_id] = timer
        timer.start()

    def _blink_once(self, button_id: str, color_a: str, color_b: str, period: float) -> None:
        with self._lock:
            if button_id not in self._blink_timers:
                return
            state = not self._blink_states.get(button_id, False)
            self._blink_states[button_id] = state
        if self.device and getattr(self.device, "connected", False):
            self._send_one(button_id, color_a if state else color_b)
        with self._lock:
            if button_id in self._blink_timers:
                self._schedule_blink(button_id, color_a, color_b, period)

    def _send_many(self, colors: dict[str, str]) -> None:
        if not self.device or not getattr(self.device, "connected", False):
            return
        self._submit(self._send_many_now, dict(colors))

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
        if not self.device or not getattr(self.device, "connected", False):
            return
        self._submit(self._send_one_now, button_id, color)

    def _send_one_now(self, button_id: str, color: str) -> None:
        try:
            if self.device and getattr(self.device, "connected", False):
                self.device.set_pad_color(button_id, color)
        except Exception:
            if self.logger:
                self.logger.exception("Could not update Launchpad pad lighting.")

    def _submit(self, func, *args) -> None:
        if self._executor is None:
            func(*args)
            return
        try:
            self._executor.submit(func, *args)
        except RuntimeError:
            if self.logger:
                self.logger.debug("Lighting update skipped because the output worker is shutting down.")
