from __future__ import annotations

import itertools
import threading
import time
from pathlib import Path
from typing import Callable

from ..actions.base import ActionResult
from ..services.performance_monitor import PerformanceMonitor
from .sound_instance import SoundInstance, SoundMetadata


SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".ogg"}


class AudioEngine:
    def __init__(
        self,
        logger=None,
        global_volume: int = 100,
        default_output_device_id: str = "",
        performance_logging_enabled: bool = False,
        performance_monitor: PerformanceMonitor | None = None,
    ) -> None:
        self.logger = logger
        self.global_volume = max(0, min(100, int(global_volume)))
        self.default_output_device_id = default_output_device_id
        self.performance_logging_enabled = performance_logging_enabled
        self.performance_monitor = performance_monitor or PerformanceMonitor(logger, performance_logging_enabled)
        self.state_changed_callback: Callable[[], None] | None = None
        self._instances: dict[str, SoundInstance] = {}
        self._metadata_cache: dict[str, SoundMetadata] = {}
        self._counter = itertools.count(1)
        self._lock = threading.RLock()
        try:
            from PySide6.QtCore import QUrl
            from PySide6.QtMultimedia import QAudioOutput, QMediaDevices, QMediaPlayer
        except Exception:
            self.qt_available = False
            self._qt = None
        else:
            self.qt_available = True
            self._qt = (QUrl, QAudioOutput, QMediaDevices, QMediaPlayer)

    def play_button_sound(self, button_id: str, config: dict) -> ActionResult:
        start = time.perf_counter()
        file_path = str(config.get("file_path") or "").strip().strip('"')
        metadata_result = self.get_metadata(file_path)
        if isinstance(metadata_result, ActionResult):
            return metadata_result
        metadata = metadata_result
        if not self.qt_available or self._qt is None:
            return ActionResult.fail("QtMultimedia is unavailable.")
        behavior = str(config.get("behavior_when_already_playing") or "restart")
        existing = self.instances_for_button(button_id)
        if existing and behavior == "ignore":
            return ActionResult.ok("Sound is already playing.")
        if existing and behavior == "toggle_stop":
            self.stop_button(button_id)
            return ActionResult.ok("Stopped sound.")
        if existing and behavior == "restart":
            self.stop_button(button_id)

        QUrl, QAudioOutput, QMediaDevices, QMediaPlayer = self._qt
        player = QMediaPlayer()
        audio_output = self._create_audio_output(QAudioOutput, QMediaDevices, str(config.get("output_device_id") or ""))
        volume = max(0, min(100, int(config.get("volume", 100) or 100)))
        effective_volume = (volume / 100.0) * (self.global_volume / 100.0)
        audio_output.setVolume(effective_volume)
        player.setAudioOutput(audio_output)
        player.setSource(QUrl.fromLocalFile(metadata.file_path))
        loop = bool(config.get("loop", False))
        if loop and hasattr(player, "setLoops"):
            try:
                player.setLoops(QMediaPlayer.Loops.Infinite)
            except Exception:
                player.setLoops(-1)
        instance_id = f"{button_id}-{next(self._counter)}"
        instance = SoundInstance(
            instance_id=instance_id,
            button_id=button_id,
            page_id=str(config.get("_page_id") or ""),
            file_path=metadata.file_path,
            display_name=metadata.display_name,
            player=player,
            audio_output=audio_output,
            loop=loop,
            volume=volume,
        )
        with self._lock:
            self._instances[instance_id] = instance

        def cleanup(status) -> None:
            try:
                if status == QMediaPlayer.MediaStatus.EndOfMedia and not loop:
                    self._remove_instance(instance_id)
            except Exception:
                self._remove_instance(instance_id)

        try:
            player.mediaStatusChanged.connect(cleanup)
            player.errorOccurred.connect(lambda *_: self._on_player_error(instance_id))
            player.play()
        except Exception as exc:
            self._remove_instance(instance_id)
            if self.logger:
                self.logger.exception("Audio playback failed.")
            return ActionResult.fail(f"Sound playback failed: {exc}")
        elapsed_ms = (time.perf_counter() - start) * 1000
        self.performance_monitor.record("sound_playback_trigger", elapsed_ms, button=button_id)
        self._log_timing("Sound action started", elapsed_ms)
        self._emit_state_changed()
        return ActionResult.ok("Sound started.", should_update_lighting=True)

    def get_metadata(self, file_path: str) -> SoundMetadata | ActionResult:
        if not file_path:
            return ActionResult.fail("Choose a sound file.")
        path = Path(file_path).expanduser()
        if not path.exists() or not path.is_file():
            return ActionResult.fail(f"Sound file does not exist: {file_path}")
        suffix = path.suffix.lower()
        if suffix not in SUPPORTED_AUDIO_EXTENSIONS:
            supported = ", ".join(sorted(SUPPORTED_AUDIO_EXTENSIONS))
            return ActionResult.fail(f"Unsupported sound format '{suffix or 'unknown'}'. Supported formats: {supported}.")
        resolved = path.resolve()
        cache_key = str(resolved)
        try:
            stat = resolved.stat()
        except OSError as exc:
            return ActionResult.fail(f"Could not read sound file: {exc}")
        cached = self._metadata_cache.get(cache_key)
        if cached and cached.modified_ns == stat.st_mtime_ns and cached.size_bytes == stat.st_size:
            return cached
        metadata = SoundMetadata.from_path(resolved)
        self._metadata_cache[cache_key] = metadata
        return metadata

    def instances_for_button(self, button_id: str) -> list[SoundInstance]:
        with self._lock:
            return [instance for instance in self._instances.values() if instance.button_id == button_id]

    def is_button_playing(self, button_id: str) -> bool:
        return bool(self.instances_for_button(button_id))

    def stop_button(self, button_id: str) -> None:
        for instance in self.instances_for_button(button_id):
            self._stop_instance(instance.instance_id)

    def stop_page(self, page_id: str) -> None:
        with self._lock:
            instances = list(self._instances.values())
        for instance in instances:
            if instance.page_id == page_id:
                self._stop_instance(instance.instance_id)

    def stop_all(self) -> None:
        with self._lock:
            instance_ids = list(self._instances)
        for instance_id in instance_ids:
            self._stop_instance(instance_id)

    def set_global_volume(self, volume: int) -> None:
        self.global_volume = max(0, min(100, int(volume)))
        with self._lock:
            instances = list(self._instances.values())
        for instance in instances:
            if instance.audio_output is not None:
                instance.audio_output.setVolume((instance.volume / 100.0) * (self.global_volume / 100.0))

    def set_default_output_device(self, device_id: str) -> None:
        self.default_output_device_id = device_id

    def currently_playing(self) -> list[SoundInstance]:
        with self._lock:
            return list(self._instances.values())

    def _stop_instance(self, instance_id: str) -> None:
        instance = self._remove_instance(instance_id, emit=False)
        if not instance:
            return
        try:
            if instance.player is not None:
                instance.player.stop()
        except Exception:
            if self.logger:
                self.logger.exception("Could not stop sound instance.")
        self._emit_state_changed()

    def _remove_instance(self, instance_id: str, emit: bool = True) -> SoundInstance | None:
        with self._lock:
            instance = self._instances.pop(instance_id, None)
        if instance and emit:
            self._emit_state_changed()
        return instance

    def _on_player_error(self, instance_id: str) -> None:
        if self.logger:
            self.logger.warning("Audio backend reported a playback error for %s.", instance_id)
        self._remove_instance(instance_id)

    def _create_audio_output(self, QAudioOutput, QMediaDevices, requested_device_id: str):
        device_id = requested_device_id or self.default_output_device_id
        if device_id:
            try:
                for device in QMediaDevices.audioOutputs():
                    if bytes(device.id()).decode(errors="replace") == device_id:
                        return QAudioOutput(device)
            except Exception:
                if self.logger:
                    self.logger.exception("Could not select requested audio output device.")
        return QAudioOutput()

    def _emit_state_changed(self) -> None:
        if self.state_changed_callback:
            self.state_changed_callback()

    def _log_timing(self, label: str, elapsed_ms: float) -> None:
        if not self.logger:
            return
        if self.performance_logging_enabled:
            self.logger.info("%s in %.3f ms", label, elapsed_ms)
        else:
            self.logger.debug("%s in %.3f ms", label, elapsed_ms)
