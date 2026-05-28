from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..constants import BUTTON_IDS
from .midi_mapping import MidiAddress, MidiMapping, message_to_address, message_to_raw_data


@dataclass(frozen=True, slots=True)
class CalibrationCapture:
    button_id: str
    address: MidiAddress
    raw_text: str
    raw_data: list[int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "button_id": self.button_id,
            "address": self.address.to_dict(),
            "raw_text": self.raw_text,
            "raw_data": list(self.raw_data),
        }


@dataclass
class CalibrationSession:
    expected_buttons: list[str] = field(default_factory=lambda: list(BUTTON_IDS))
    captured: dict[str, MidiAddress] = field(default_factory=dict)
    raw_messages: list[CalibrationCapture] = field(default_factory=list)
    active: bool = False
    index: int = 0

    def start(self) -> str:
        self.captured.clear()
        self.raw_messages.clear()
        self.index = 0
        self.active = True
        return self.current_instruction()

    def current_instruction(self) -> str:
        if not self.active or self.index >= len(self.expected_buttons):
            return "Calibration complete."
        return f"Press {self.expected_buttons[self.index]}"

    def capture(self, message: Any) -> str:
        if not self.active or self.index >= len(self.expected_buttons):
            return "Calibration is not active."
        if not self._is_press(message):
            return self.current_instruction()
        address = message_to_address(message)
        if address is None:
            return self.current_instruction()
        button_id = self.expected_buttons[self.index]
        self.captured[button_id] = address
        self.raw_messages.append(
            CalibrationCapture(
                button_id=button_id,
                address=address,
                raw_text=repr(message),
                raw_data=message_to_raw_data(message),
            )
        )
        self.index += 1
        if self.index >= len(self.expected_buttons):
            self.active = False
            return "Calibration complete."
        return self.current_instruction()

    def to_mapping(self) -> MidiMapping:
        return MidiMapping(name="Launchpad Mini MK3 Calibrated", button_to_address=dict(self.captured))

    def raw_log_lines(self) -> list[str]:
        return [
            f"{capture.button_id}: {capture.raw_text} data={capture.raw_data} -> {capture.address.message_type} {capture.address.number} ch {capture.address.channel}"
            for capture in self.raw_messages
        ]

    @staticmethod
    def _is_press(message: Any) -> bool:
        message_type = getattr(message, "type", "")
        if message_type == "note_on":
            return int(getattr(message, "velocity", 0) or 0) > 0
        if message_type == "control_change":
            return int(getattr(message, "value", 0) or 0) > 0
        return False
