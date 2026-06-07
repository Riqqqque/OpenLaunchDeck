from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..actions.base import ActionResult
from .input_devices import list_input_devices
from .output_devices import device_id_from_qt, list_output_devices


@dataclass(slots=True)
class MicBridgeState:
    running: bool = False
    input_id: str = ""
    input_name: str = ""
    output_id: str = ""
    output_name: str = ""
    message: str = "Microphone route is off."


class MicBridge:
    def __init__(self, logger=None) -> None:
        self.logger = logger
        self.state = MicBridgeState()
        self._source: Any = None
        self._sink: Any = None
        self._source_device: Any = None
        try:
            from PySide6.QtMultimedia import QAudioSink, QAudioSource, QMediaDevices
        except Exception:
            self.qt_available = False
            self._qt = None
        else:
            self.qt_available = True
            self._qt = (QAudioSink, QAudioSource, QMediaDevices)

    def start(self, input_device_id: str, output_device_id: str, volume: int = 100) -> ActionResult:
        self.stop()
        if not self.qt_available or self._qt is None:
            self.state = MicBridgeState(message="QtMultimedia microphone routing is unavailable.")
            return ActionResult.fail(self.state.message)
        if not output_device_id:
            self.state = MicBridgeState(message="Choose a voice route output before routing the microphone.")
            return ActionResult.fail(self.state.message)

        QAudioSink, QAudioSource, QMediaDevices = self._qt
        input_device = self._find_input_device(QMediaDevices, input_device_id)
        output_device = self._find_output_device(QMediaDevices, output_device_id)
        if input_device is None:
            self.state = MicBridgeState(message="Selected microphone input is not available.")
            return ActionResult.fail(self.state.message)
        if output_device is None:
            self.state = MicBridgeState(message="Selected voice route output is not available.")
            return ActionResult.fail(self.state.message)

        input_name = str(input_device.description() or "Microphone")
        output_name = str(output_device.description() or "Voice route")
        try:
            audio_format = self._choose_format(input_device, output_device)
            self._source = QAudioSource(input_device, audio_format)
            self._sink = QAudioSink(output_device, audio_format)
            if hasattr(self._sink, "setVolume"):
                self._sink.setVolume(max(0, min(100, int(volume))) / 100.0)
            self._source_device = self._source.start()
            if self._source_device is None:
                self.stop()
                self.state = MicBridgeState(message="Could not start microphone capture.")
                return ActionResult.fail(self.state.message)
            self._sink.start(self._source_device)
        except Exception as exc:
            self.stop()
            if self.logger:
                self.logger.exception("Microphone voice route failed.")
            self.state = MicBridgeState(message=f"Microphone route failed: {exc}")
            return ActionResult.fail(self.state.message)

        self.state = MicBridgeState(
            running=True,
            input_id=device_id_from_qt(input_device),
            input_name=input_name,
            output_id=device_id_from_qt(output_device),
            output_name=output_name,
            message=f"Microphone route is on: {input_name} -> {output_name}.",
        )
        if self.logger:
            self.logger.info("Microphone voice route started: %s -> %s", input_name, output_name)
        return ActionResult.ok(self.state.message)

    def stop(self) -> None:
        source = self._source
        sink = self._sink
        self._source = None
        self._sink = None
        self._source_device = None
        try:
            if source is not None:
                source.stop()
        except Exception:
            if self.logger:
                self.logger.exception("Could not stop microphone capture.")
        try:
            if sink is not None:
                sink.stop()
        except Exception:
            if self.logger:
                self.logger.exception("Could not stop microphone voice route.")
        self.state = MicBridgeState()

    def set_volume(self, volume: int) -> None:
        if self._sink is not None and hasattr(self._sink, "setVolume"):
            self._sink.setVolume(max(0, min(100, int(volume))) / 100.0)

    def _find_input_device(self, QMediaDevices, device_id: str):
        devices = list(QMediaDevices.audioInputs())
        if device_id:
            for device in devices:
                if device_id_from_qt(device) == device_id:
                    return device
            return None
        try:
            default_device = QMediaDevices.defaultAudioInput()
        except Exception:
            default_device = None
        return default_device or (devices[0] if devices else None)

    def _find_output_device(self, QMediaDevices, device_id: str):
        for device in QMediaDevices.audioOutputs():
            if device_id_from_qt(device) == device_id:
                return device
        return None

    def _choose_format(self, input_device, output_device):
        audio_format = input_device.preferredFormat()
        try:
            if output_device.isFormatSupported(audio_format):
                return audio_format
            output_format = output_device.preferredFormat()
            if input_device.isFormatSupported(output_format):
                return output_format
        except Exception:
            pass
        return audio_format


def microphone_route_summary(input_device_id: str, output_device_id: str) -> str:
    input_name = _device_name(list_input_devices(include_duplicates=True), input_device_id, "System default microphone")
    output_name = _device_name(list_output_devices(include_duplicates=True, include_advanced=True), output_device_id, "No voice route output")
    return f"{input_name} -> {output_name}"


def _device_name(devices: list[dict[str, str | int]], device_id: str, fallback: str) -> str:
    if not device_id:
        return fallback
    for device in devices:
        if str(device.get("id") or "") == device_id:
            return str(device.get("display_name") or device.get("description") or fallback)
    return fallback
