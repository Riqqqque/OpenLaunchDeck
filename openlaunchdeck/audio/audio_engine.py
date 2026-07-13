from __future__ import annotations

import itertools
import threading
import time
from pathlib import Path
from typing import Callable

from ..actions.base import ActionResult
from ..services.performance_monitor import PerformanceMonitor
from .mic_bridge import MicBridge, MicBridgeState
from .output_devices import device_id_from_qt
from .sound_instance import SoundInstance, SoundMetadata
from .voice_routing import VoiceRouteStatus, current_voice_route_status


SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".ogg"}


def clamp_percent(value, default: int = 100) -> int:
    if value in (None, ""):
        value = default
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(0, min(100, number))


def percent_from_config(config: dict, key: str, default: int) -> int:
    return clamp_percent(config.get(key, default), default)


def soundboard_gain(volume: int, global_volume: int) -> float:
    combined = (clamp_percent(volume) / 100.0) * (clamp_percent(global_volume) / 100.0)
    return combined * combined


class AudioEngine:
    def __init__(
        self,
        logger=None,
        global_volume: int = 100,
        default_output_device_id: str = "",
        voice_chat_output_device_id: str = "",
        monitor_voice_chat_routes: bool = True,
        voice_route_microphone_enabled: bool = False,
        voice_route_microphone_device_id: str = "",
        voice_route_microphone_volume: int = 100,
        performance_logging_enabled: bool = False,
        performance_monitor: PerformanceMonitor | None = None,
    ) -> None:
        self.logger = logger
        self.global_volume = clamp_percent(global_volume)
        self.default_output_device_id = default_output_device_id
        self.voice_chat_output_device_id = voice_chat_output_device_id
        self.monitor_voice_chat_routes = bool(monitor_voice_chat_routes)
        self.voice_route_microphone_enabled = bool(voice_route_microphone_enabled)
        self.voice_route_microphone_device_id = voice_route_microphone_device_id
        self.voice_route_microphone_volume = clamp_percent(voice_route_microphone_volume)
        self.performance_logging_enabled = performance_logging_enabled
        self.performance_monitor = performance_monitor or PerformanceMonitor(logger, performance_logging_enabled)
        self.mic_bridge = MicBridge(logger)
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
        volume = percent_from_config(config, "volume", 100)
        effective_volume = soundboard_gain(volume, self.global_volume)
        loop = bool(config.get("loop", False))
        route_to_voice_chat = bool(config.get("route_to_voice_chat", False))
        output_routes = self._build_output_routes(config, route_to_voice_chat)
        if isinstance(output_routes, ActionResult):
            return output_routes
        started_instance_ids: list[str] = []
        try:
            for route_name, requested_device_id, routed_to_voice_chat in output_routes:
                audio_output = self._create_audio_output(
                    QAudioOutput,
                    QMediaDevices,
                    requested_device_id,
                    route_name=route_name,
                    allow_default=not routed_to_voice_chat,
                )
                if audio_output is None:
                    for instance_id in started_instance_ids:
                        self._stop_instance(instance_id)
                    if route_name == "voice_chat":
                        return ActionResult.fail("Voice route output device is not available.")
                    return ActionResult.fail("Selected soundboard output device is not available.")
                audio_output.setVolume(effective_volume)
                player = QMediaPlayer()
                player.setAudioOutput(audio_output)
                player.setSource(QUrl.fromLocalFile(metadata.file_path))
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
                    routed_to_voice_chat=routed_to_voice_chat,
                )
                with self._lock:
                    self._instances[instance_id] = instance
                started_instance_ids.append(instance_id)

                def cleanup(status, captured_instance_id=instance_id) -> None:
                    try:
                        if status == QMediaPlayer.MediaStatus.EndOfMedia and not loop:
                            self._remove_instance(captured_instance_id)
                    except Exception:
                        self._remove_instance(captured_instance_id)

                player.mediaStatusChanged.connect(cleanup)
                player.errorOccurred.connect(lambda *_, captured_instance_id=instance_id: self._on_player_error(captured_instance_id))
                player.play()
                if self.logger and route_name:
                    self.logger.debug("Started sound output route %s for %s.", route_name, button_id)
        except Exception as exc:
            for instance_id in started_instance_ids:
                self._stop_instance(instance_id)
            if self.logger:
                self.logger.exception("Audio playback failed.")
            return ActionResult.fail(f"Sound playback failed: {exc}")
        elapsed_ms = (time.perf_counter() - start) * 1000
        self.performance_monitor.record("sound_playback_trigger", elapsed_ms, button=button_id)
        self._log_timing("Sound action started", elapsed_ms)
        self._emit_state_changed()
        if route_to_voice_chat:
            return ActionResult.ok("Sound routed to voice chat.", should_update_lighting=True)
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
        with self._lock:
            return any(instance.button_id == button_id for instance in self._instances.values())

    def playing_button_ids(self) -> set[str]:
        with self._lock:
            return {instance.button_id for instance in self._instances.values()}

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

    def shutdown(self) -> None:
        self.stop_all()
        self.mic_bridge.stop()

    def set_global_volume(self, volume: int) -> None:
        self.global_volume = clamp_percent(volume)
        with self._lock:
            instances = list(self._instances.values())
        for instance in instances:
            if instance.audio_output is not None:
                instance.audio_output.setVolume(soundboard_gain(instance.volume, self.global_volume))

    def set_default_output_device(self, device_id: str) -> None:
        self.default_output_device_id = device_id

    def set_voice_chat_output_device(self, device_id: str) -> None:
        self.voice_chat_output_device_id = device_id
        if self.voice_route_microphone_enabled:
            self.refresh_voice_route_microphone()

    def set_monitor_voice_chat_routes(self, enabled: bool) -> None:
        self.monitor_voice_chat_routes = bool(enabled)

    def set_voice_route_microphone_device(self, device_id: str) -> None:
        self.voice_route_microphone_device_id = device_id
        if self.voice_route_microphone_enabled:
            self.refresh_voice_route_microphone()

    def set_voice_route_microphone_enabled(self, enabled: bool) -> ActionResult:
        self.voice_route_microphone_enabled = bool(enabled)
        if not self.voice_route_microphone_enabled:
            self.mic_bridge.stop()
            return ActionResult.ok("Microphone route is off.")
        return self.refresh_voice_route_microphone()

    def set_voice_route_microphone_volume(self, volume: int) -> None:
        self.voice_route_microphone_volume = clamp_percent(volume)
        self.mic_bridge.set_volume(self.voice_route_microphone_volume)

    def refresh_voice_route_microphone(self) -> ActionResult:
        if not self.voice_route_microphone_enabled:
            self.mic_bridge.stop()
            return ActionResult.ok("Microphone route is off.")
        return self.mic_bridge.start(
            self.voice_route_microphone_device_id,
            self.voice_chat_output_device_id,
            self.voice_route_microphone_volume,
        )

    def voice_route_microphone_state(self) -> MicBridgeState:
        return self.mic_bridge.state

    def voice_route_status(self) -> VoiceRouteStatus:
        return current_voice_route_status(self.voice_chat_output_device_id)

    def voice_route_ready(self) -> bool:
        return self.voice_route_status().ready

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

    def _build_output_routes(self, config: dict, route_to_voice_chat: bool) -> list[tuple[str, str, bool]] | ActionResult:
        if not route_to_voice_chat:
            return [("default", str(config.get("output_device_id") or ""), False)]
        voice_device_id = str(config.get("voice_chat_output_device_id") or self.voice_chat_output_device_id or "")
        if not voice_device_id:
            return ActionResult.fail("Choose a voice route output device in the Soundboard panel.")
        routes: list[tuple[str, str, bool]] = [("voice_chat", voice_device_id, True)]
        if self.monitor_voice_chat_routes:
            monitor_device_id = str(config.get("output_device_id") or self.default_output_device_id or "")
            if monitor_device_id != voice_device_id:
                routes.append(("monitor", monitor_device_id, False))
        return routes

    def _create_audio_output(
        self,
        QAudioOutput,
        QMediaDevices,
        requested_device_id: str,
        route_name: str,
        allow_default: bool = True,
    ):
        explicit_device_id = str(requested_device_id or "")
        saved_default_id = str(self.default_output_device_id or "")
        device_id = explicit_device_id or saved_default_id
        if device_id:
            try:
                for device in QMediaDevices.audioOutputs():
                    if device_id_from_qt(device) == device_id:
                        return QAudioOutput(device)
            except Exception:
                if self.logger:
                    self.logger.exception("Could not select requested audio output device.")
                return None
            if self.logger:
                self.logger.warning("Selected soundboard output is unavailable for %s route: %s", route_name, device_id)
            return None
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
