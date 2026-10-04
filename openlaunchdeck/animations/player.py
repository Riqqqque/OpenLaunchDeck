from __future__ import annotations

import random
import threading
import time
from collections.abc import Callable, Iterator

from ..constants import BUTTON_IDS
from .library import AnimationLibrary
from .model import FRAME_SIZE, MAX_FPS, scale_color

# Never animate faster than the Launchpad comfortably takes full-grid updates.
MAX_PLAYBACK_FPS = MAX_FPS
IDLE_POLL_SECONDS = 1.0


class IdleAnimationPlayer:
    """Plays an idle animation on the Launchpad after a period with no pad use.

    Pad presses call note_activity(), which stops playback immediately and hands
    the pads back to the normal page lighting.
    """

    def __init__(
        self,
        lighting_service,
        device,
        settings_service,
        library: AnimationLibrary,
        logger=None,
        can_start: Callable[[], bool] | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.lighting = lighting_service
        self.device = device
        self.settings_service = settings_service
        self.library = library
        self.logger = logger
        self.can_start = can_start
        self._clock = clock
        self._state_lock = threading.Lock()
        self._wake = threading.Event()
        self._shutdown = False
        self._last_activity = clock()
        self._frames: Iterator[list[str]] | None = None
        self._fps = 10
        self._preview_until: float | None = None
        self._brightness_override: int | None = None
        self.current_animation_id = ""
        self._thread: threading.Thread | None = None

    @property
    def playing(self) -> bool:
        return self._frames is not None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run, name="openlaunchdeck-idle-animation", daemon=True)
        self._thread.start()

    def shutdown(self) -> None:
        with self._state_lock:
            self._shutdown = True
        self.stop()
        self._wake.set()
        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=1.0)

    def note_activity(self) -> bool:
        """Record pad use. Returns True when this press stopped an animation."""
        with self._state_lock:
            self._last_activity = self._clock()
            was_playing = self._stop_locked()
        self._wake.set()
        return was_playing

    def stop(self) -> None:
        with self._state_lock:
            self._stop_locked()
        self._wake.set()

    def settings_changed(self) -> None:
        """Re-read settings now; restarts the idle countdown and any running animation."""
        self.note_activity()

    def preview(
        self,
        animation_id=None,
        seconds: float = 8.0,
        speed: int | None = None,
        brightness: int | None = None,
    ) -> bool:
        """Play right away for a few seconds, ignoring the idle timeout and the enabled switch.

        animation_id may also be an animation object, such as an unsaved one from the editor.
        speed and brightness (percent) override the saved settings for this preview only.
        """
        with self._state_lock:
            if self._shutdown or not self._device_ready():
                return False
            self._stop_locked()
            if not self._begin_locked(animation_id, preview=True, speed=speed):
                return False
            self._brightness_override = brightness
            self._preview_until = self._clock() + max(1.0, seconds)
        self._wake.set()
        return True

    def _settings(self):
        return self.settings_service.settings

    def _device_ready(self) -> bool:
        return bool(self.device is not None and getattr(self.device, "connected", False))

    def _stop_locked(self) -> bool:
        was_playing = self._frames is not None
        self._frames = None
        self._preview_until = None
        self._brightness_override = None
        self.current_animation_id = ""
        if was_playing:
            self.lighting.end_overlay()
        return was_playing

    def _choose_animation_id(self, requested: str | None) -> str | None:
        settings = self._settings()
        if requested:
            return requested if self.library.get(requested) else None
        if settings.idle_animation_shuffle:
            choices = [animation.id for animation in self.library.all()]
            return random.choice(choices) if choices else None
        if self.library.get(settings.idle_animation_id):
            return settings.idle_animation_id
        return "rainbow_wave"

    def _begin_locked(self, requested, preview: bool = False, speed: int | None = None) -> bool:
        if hasattr(requested, "iter_frames"):
            # An unsaved animation straight from the editor.
            animation = requested
        else:
            animation_id = self._choose_animation_id(requested)
            animation = self.library.get(animation_id) if animation_id else None
        if animation is None:
            return False
        if not self.lighting.begin_overlay():
            return False
        speed_percent = speed if speed is not None else self._settings().idle_animation_speed
        self._fps = max(1.0, min(MAX_PLAYBACK_FPS, animation.fps * max(25, min(300, speed_percent)) / 100))
        self._frames = animation.iter_frames(random.randrange(1 << 30))
        self.current_animation_id = animation.id
        if self.logger:
            self.logger.info("Idle animation %s: %s", "preview" if preview else "started", animation.id)
        return True

    def _ready_to_idle(self) -> bool:
        settings = self._settings()
        if not settings.idle_animation_enabled or not self._device_ready():
            return False
        if getattr(self.lighting, "overlay_active", False):
            return False
        if self.can_start is not None:
            try:
                return bool(self.can_start())
            except Exception:
                if self.logger:
                    self.logger.exception("Idle animation start check failed.")
                return False
        return True

    def _run(self) -> None:
        while True:
            with self._state_lock:
                if self._shutdown:
                    return
                delay = self._step_locked()
            self._wake.wait(timeout=delay)
            self._wake.clear()

    def _step_locked(self) -> float:
        now = self._clock()
        if self._frames is None:
            settings = self._settings()
            remaining = settings.idle_animation_timeout_seconds - (now - self._last_activity)
            if remaining > 0:
                return min(IDLE_POLL_SECONDS, remaining)
            if not self._ready_to_idle() or not self._begin_locked(None):
                return IDLE_POLL_SECONDS
        if not self._device_ready() or (self._preview_until is not None and now >= self._preview_until):
            self._stop_locked()
            self._last_activity = now
            return IDLE_POLL_SECONDS
        try:
            frame = next(self._frames)
        except Exception:
            if self.logger:
                self.logger.exception("Idle animation %s stopped with an error.", self.current_animation_id)
            self._stop_locked()
            self._last_activity = now
            return IDLE_POLL_SECONDS
        brightness_percent = self._brightness_override
        if brightness_percent is None:
            brightness_percent = self._settings().idle_animation_brightness
        brightness = max(10, min(100, brightness_percent)) / 100
        colors = {
            button_id: scale_color(frame[index], brightness)
            for index, button_id in enumerate(BUTTON_IDS[:FRAME_SIZE])
        }
        self.lighting.send_overlay_frame(colors)
        return 1.0 / self._fps
