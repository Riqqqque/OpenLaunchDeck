from __future__ import annotations

from collections.abc import Callable
import threading
import time
from typing import Any

from ..constants import NAMED_COLORS
from ..services.performance_monitor import PerformanceMonitor
from .midi_mapping import MidiMapping


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
        midi_in_callback: Callable[[Any, str], None] | None = None,
        midi_out_callback: Callable[[Any, str], None] | None = None,
        disconnect_callback: Callable[[str], None] | None = None,
        performance_monitor: PerformanceMonitor | None = None,
    ) -> None:
        self.mapping = mapping or MidiMapping.load_user_default(logger)
        self.logger = logger
        self.button_callback = button_callback
        self.midi_in_callback = midi_in_callback
        self.midi_out_callback = midi_out_callback
        self.disconnect_callback = disconnect_callback
        self.performance_monitor = performance_monitor or PerformanceMonitor(logger)
        self.input_port_name = ""
        self.output_port_name = ""
        self.input_port = None
        self.output_port = None
        self.connected = False
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
        try:
            receive_start = time.perf_counter()
            self.performance_monitor.mark("midi_raw_receive")
            if self.logger:
                self.logger.debug("MIDI IN raw received_at=%.6f %r", receive_start, message)
            if self.midi_in_callback:
                self.midi_in_callback(message, repr(message))
            parsed = self.mapping.parse_message(message)
            parse_ms = (time.perf_counter() - receive_start) * 1000
            self.performance_monitor.record("midi_event_parse", parse_ms, recognized=bool(parsed))
            if self.logger and parsed:
                self.logger.debug("MIDI parsed %s pressed=%s in %.3f ms", parsed.button_id, parsed.pressed, parse_ms)
            elif self.logger:
                self.logger.debug("MIDI parse ignored message in %.3f ms", parse_ms)
            if parsed and self.button_callback:
                self.button_callback(parsed.button_id, parsed.pressed, message)
        except Exception as exc:
            if self.logger:
                self.logger.exception("MIDI input callback failed.")
            self._mark_disconnected(f"MIDI input failed: {exc}")

    def set_pad_color(self, button_id: str, color: str) -> None:
        self.set_many_pad_colors({button_id: color})

    def set_many_pad_colors(self, colors: dict[str, str]) -> int:
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
            for button_id, color in colors.items():
                message = self._color_message(mido, button_id, color)
                if message is None:
                    continue
                try:
                    self.output_port.send(message)
                    sent += 1
                    if self.midi_out_callback:
                        self.midi_out_callback(message, repr(message))
                    if self.logger:
                        self.logger.debug("MIDI OUT %s color=%s %r", button_id, color, message)
                except Exception as exc:
                    self._mark_disconnected(f"Could not send MIDI lighting: {exc}")
                    break
        elapsed_ms = (time.perf_counter() - start) * 1000
        self.performance_monitor.record("midi_lighting_batch", elapsed_ms, sent=sent)
        if self.logger:
            self.logger.debug("MIDI lighting batch sent=%s elapsed=%.3f ms", sent, elapsed_ms)
        return sent

    def _color_message(self, mido, button_id: str, color: str):
        address = self.mapping.address_for_button(button_id)
        if not address:
            return None
        value = color_to_palette_value(color)
        if address.message_type == "note":
            return mido.Message("note_on", note=address.number, velocity=value, channel=address.channel)
        return mido.Message("control_change", control=address.number, value=value, channel=address.channel)

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
            if self.midi_out_callback:
                self.midi_out_callback(message, repr(message))
            if self.logger:
                self.logger.debug("MIDI OUT %s %r", label, message)
            return True
        except Exception as exc:
            self._mark_disconnected(f"Could not send MIDI SysEx {label}: {exc}")
            if strict:
                raise RuntimeError(f"Could not send MIDI SysEx {label}: {exc}") from exc
            return False

    def clear_all_pads(self) -> None:
        self.set_many_pad_colors({button_id: "off" for button_id in self.mapping.button_to_address})

    def flash_pad(self, button_id: str, color: str = "white") -> None:
        self.set_pad_color(button_id, color)

    def _mark_disconnected(self, reason: str) -> None:
        if self.logger:
            self.logger.warning("%s", reason)
        self.connected = False
        if self.disconnect_callback:
            self.disconnect_callback(reason)


def color_to_palette_value(color: str) -> int:
    if color in LAUNCHPAD_PALETTE:
        return LAUNCHPAD_PALETTE[color]
    if color in NAMED_COLORS:
        return LAUNCHPAD_PALETTE.get(color, 0)
    return 0
