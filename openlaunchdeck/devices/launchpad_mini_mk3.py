from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Any

from ..constants import NAMED_COLORS
from ..services.performance_monitor import PerformanceMonitor
from .midi_manager import MidiManager
from .midi_mapping import (
    MidiAddress,
    MidiMapping,
    address_for_auxiliary_control,
    parse_auxiliary_message,
)

LAUNCHPAD_PALETTE = {
    # Programmer Mode palette preset. Verify with MIDI Debug before treating a
    # mapping as hardware-certified for a release.
    "off": 0,
    "dim": 1,
    "white": 3,
    "red": 5,
    "orange": 9,
    "yellow": 13,
    "green": 21,
    "cyan": 37,
    "blue": 45,
    "purple": 49,
    "pink": 53,
}

LAUNCHPAD_SYSEX_HEADER = [0, 32, 41, 2, 13]
PROGRAMMER_MODE_SYSEX = LAUNCHPAD_SYSEX_HEADER + [14, 1]
LIVE_MODE_SYSEX = LAUNCHPAD_SYSEX_HEADER + [14, 0]


class LaunchpadMiniMk3:
    def __init__(
        self,
        mapping: MidiMapping | None = None,
        logger=None,
        button_callback: Callable[[str, bool, Any], None] | None = None,
        control_callback: Callable[[str, bool, Any], None] | None = None,
        midi_in_callback: Callable[[Any, str], None] | None = None,
        midi_out_callback: Callable[[Any, str], None] | None = None,
        disconnect_callback: Callable[[str], None] | None = None,
        performance_monitor: PerformanceMonitor | None = None,
    ) -> None:
        self.mapping = mapping or MidiMapping.load_user_default(logger)
        self.logger = logger
        self.button_callback = button_callback
        self.control_callback = control_callback
        self.midi_in_callback = midi_in_callback
        self.midi_out_callback = midi_out_callback
        self.disconnect_callback = disconnect_callback
        self.performance_monitor = performance_monitor or PerformanceMonitor(logger)
        self.input_port_name = ""
        self.output_port_name = ""
        self.input_port = None
        self.output_port = None
        self.connected = False
        self.last_input_monotonic = 0.0
        self._lock = threading.RLock()

    def connect(self, input_port_name: str, output_port_name: str) -> None:
        try:
            import mido
        except Exception as exc:
            raise RuntimeError("MIDI dependencies are not installed.") from exc
        with self._lock:
            self.close()
            self.input_port_name = input_port_name
            self.output_port_name = output_port_name
            try:
                if input_port_name:
                    self.input_port = mido.open_input(input_port_name, callback=self._on_message)
                if output_port_name:
                    self.output_port = mido.open_output(output_port_name)
            except Exception:
                self.close()
                raise
            else:
                self.connected = bool(self.input_port or self.output_port)
                self.last_input_monotonic = 0.0
                try:
                    if self.output_port and not self.enter_programmer_mode(strict=True):
                        raise RuntimeError("Launchpad did not accept the Programmer Mode command.")
                except Exception:
                    self.close()
                    raise
                if self.logger:
                    self.logger.info("Launchpad connected input=%s output=%s", input_port_name, output_port_name)

    def close(self) -> None:
        with self._lock:
            if self.output_port:
                try:
                    self.enter_live_mode()
                except Exception:
                    if self.logger:
                        self.logger.exception("Could not restore Launchpad Live mode.")
            for port in (self.input_port, self.output_port):
                try:
                    if port is not None:
                        port.close()
                except Exception:
                    if self.logger:
                        self.logger.exception("Could not close MIDI port.")
            self.input_port = None
            self.output_port = None
            self.connected = False

    def _on_message(self, message: Any) -> None:
        if not self.connected:
            return
        receive_start = time.perf_counter()
        self.last_input_monotonic = receive_start
        self.performance_monitor.mark("midi_raw_receive")
        if self.logger:
            self.logger.debug("MIDI IN raw received_at=%.6f %r", receive_start, message)
        if self.midi_in_callback:
            try:
                self.midi_in_callback(message, repr(message))
            except Exception:
                if self.logger:
                    self.logger.exception("MIDI debug callback failed.")
        try:
            parsed = self.mapping.parse_message(message)
            control = None if parsed else parse_auxiliary_message(message)
            parse_ms = (time.perf_counter() - receive_start) * 1000
            self.performance_monitor.record("midi_event_parse", parse_ms, recognized=bool(parsed or control))
            if self.logger and parsed:
                self.logger.debug("MIDI parsed %s pressed=%s in %.3f ms", parsed.button_id, parsed.pressed, parse_ms)
            elif self.logger and control:
                self.logger.debug(
                    "MIDI parsed control=%s pressed=%s in %.3f ms",
                    control.control_id,
                    control.pressed,
                    parse_ms,
                )
            elif self.logger:
                self.logger.debug("MIDI parse ignored message in %.3f ms", parse_ms)
        except Exception:
            if self.logger:
                self.logger.exception("MIDI message could not be parsed.")
            return
        if parsed and self.button_callback:
            try:
                self.button_callback(parsed.button_id, parsed.pressed, message)
            except Exception:
                if self.logger:
                    self.logger.exception("MIDI button callback failed for %s.", parsed.button_id)
        elif control and self.control_callback:
            try:
                self.control_callback(control.control_id, control.pressed, message)
            except Exception:
                if self.logger:
                    self.logger.exception("MIDI control callback failed for %s.", control.control_id)

    def set_pad_color(self, button_id: str, color: str) -> None:
        self.set_many_pad_colors({button_id: color})

    def set_many_pad_colors(self, colors: dict[str, str]) -> int:
        addresses = {
            button_id: (self.mapping.address_for_button(button_id), color)
            for button_id, color in colors.items()
        }
        return self._set_many_colors(addresses, "pads")

    def set_auxiliary_color(self, control_id: str, color: str) -> None:
        self.set_many_auxiliary_colors({control_id: color})

    def set_many_auxiliary_colors(self, colors: dict[str, str]) -> int:
        addresses = {
            control_id: (address_for_auxiliary_control(control_id), color)
            for control_id, color in colors.items()
        }
        return self._set_many_colors(addresses, "controls")

    def _set_many_colors(
        self,
        addresses: dict[str, tuple[MidiAddress | None, str]],
        group: str,
    ) -> int:
        start = time.perf_counter()
        sent = 0
        with self._lock:
            if not self.output_port:
                return 0
            try:
                import mido
            except Exception:
                if self.logger:
                    self.logger.exception("MIDI dependency is unavailable while sending lighting.")
                return 0
            entries = [
                (item_id, address, color)
                for item_id, (address, color) in addresses.items()
                if address is not None
            ]
            if not entries:
                return 0
            messages = []
            if len(entries) > 1:
                data = list(LAUNCHPAD_SYSEX_HEADER) + [3]
                for _item_id, address, color in entries:
                    data.extend((0, address.number, color_to_palette_value(color)))
                messages.append((mido.Message("sysex", data=data), entries))
            else:
                item_id, address, color = entries[0]
                if address.message_type == "note":
                    message = mido.Message(
                        "note_on",
                        note=address.number,
                        velocity=color_to_palette_value(color),
                        channel=address.channel,
                    )
                else:
                    message = mido.Message(
                        "control_change",
                        control=address.number,
                        value=color_to_palette_value(color),
                        channel=address.channel,
                    )
                messages.append((message, entries))
            for message, message_entries in messages:
                try:
                    self.output_port.send(message)
                except Exception as exc:
                    self._mark_disconnected(f"Could not send MIDI lighting: {exc}")
                    break
                sent += len(message_entries)
                if self.midi_out_callback:
                    try:
                        self.midi_out_callback(message, repr(message))
                    except Exception:
                        if self.logger:
                            self.logger.exception("MIDI debug output callback failed.")
                if self.logger:
                    summary = ", ".join(f"{item_id}={color}" for item_id, _address, color in message_entries)
                    self.logger.debug("MIDI OUT %s %s %r", group, summary, message)
        elapsed_ms = (time.perf_counter() - start) * 1000
        self.performance_monitor.record("midi_lighting_batch", elapsed_ms, sent=sent)
        if self.logger:
            self.logger.debug("MIDI lighting batch sent=%s elapsed=%.3f ms", sent, elapsed_ms)
        return sent

    def enter_programmer_mode(self, strict: bool = False) -> bool:
        return self._send_sysex(PROGRAMMER_MODE_SYSEX, "programmer_mode", strict)

    def enter_live_mode(self) -> bool:
        return self._send_sysex(LIVE_MODE_SYSEX, "live_mode")

    def _send_sysex(self, data: list[int], label: str, strict: bool = False) -> bool:
        if not self.output_port:
            return False
        try:
            import mido
            message = mido.Message("sysex", data=data)
            self.output_port.send(message)
        except Exception as exc:
            self._mark_disconnected(f"Could not send MIDI SysEx {label}: {exc}")
            if strict:
                raise RuntimeError(f"Could not send MIDI SysEx {label}: {exc}") from exc
            return False
        if self.midi_out_callback:
            try:
                self.midi_out_callback(message, repr(message))
            except Exception:
                if self.logger:
                    self.logger.exception("MIDI debug output callback failed.")
        if self.logger:
            self.logger.debug("MIDI OUT %s %r", label, message)
        return True

    def clear_all_pads(self) -> None:
        self.set_many_pad_colors({button_id: "off" for button_id in self.mapping.button_to_address})

    def clear_surface(self) -> None:
        self.clear_all_pads()
        self.set_many_auxiliary_colors(
            {control_id: "off" for control_id in (
                "top_up", "top_down", "top_left", "top_right", "session", "drums", "keys", "user",
                "scene_1", "scene_2", "scene_3", "scene_4", "scene_5", "scene_6", "scene_7", "scene_8",
            )}
        )

    def flash_pad(self, button_id: str, color: str = "white") -> None:
        self.set_pad_color(button_id, color)

    def connection_health(
        self,
        available_inputs: list[str] | None = None,
        available_outputs: list[str] | None = None,
    ) -> tuple[bool, str]:
        with self._lock:
            if not self.connected:
                return False, "MIDI device is not connected."
            input_port = self.input_port
            output_port = self.output_port
            input_name = self.input_port_name
            output_name = self.output_port_name
            if input_name and (input_port is None or bool(getattr(input_port, "closed", False))):
                return False, "MIDI input port is closed."
            if output_name and (output_port is None or bool(getattr(output_port, "closed", False))):
                return False, "MIDI output port is closed."

        inputs = MidiManager.available_input_ports() if available_inputs is None else available_inputs
        outputs = MidiManager.available_output_ports() if available_outputs is None else available_outputs
        if input_name and input_name not in inputs:
            return False, f"MIDI input port disappeared: {input_name}"
        if output_name and output_name not in outputs:
            return False, f"MIDI output port disappeared: {output_name}"
        return True, "MIDI connection is healthy."

    def mark_disconnected(self, reason: str) -> None:
        self._mark_disconnected(reason)

    def _mark_disconnected(self, reason: str) -> None:
        with self._lock:
            if not self.connected:
                return
            self.connected = False
        if self.logger:
            self.logger.warning("%s", reason)
        if self.disconnect_callback:
            self.disconnect_callback(reason)


def color_to_palette_value(color: str) -> int:
    if color in LAUNCHPAD_PALETTE:
        return LAUNCHPAD_PALETTE[color]
    if color in NAMED_COLORS:
        return LAUNCHPAD_PALETTE.get(color, 0)
    return 0
