from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..config_store import read_json, write_json
from ..constants import BUTTON_IDS, BUTTON_ROWS
from ..paths import MIDI_MAPPINGS_DIR


@dataclass(frozen=True, slots=True)
class MidiAddress:
    message_type: str
    number: int
    channel: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MidiAddress":
        return cls(
            message_type=str(data.get("message_type") or "note"),
            number=int(data.get("number", 0)),
            channel=int(data.get("channel", 0)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"message_type": self.message_type, "number": self.number, "channel": self.channel}

    def key(self) -> tuple[str, int, int]:
        return (self.message_type, self.number, self.channel)


@dataclass(frozen=True, slots=True)
class ParsedPadMessage:
    button_id: str
    pressed: bool
    address: MidiAddress
    velocity: int = 0
    raw: Any = None
    raw_data: list[int] = field(default_factory=list)


@dataclass
class MidiMapping:
    name: str = "Launchpad Mini MK3 Programmer Mode"
    button_to_address: dict[str, MidiAddress] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.button_to_address:
            self.button_to_address = build_programmer_mode_mapping()
            return
        defaults = build_programmer_mode_mapping()
        for button_id in BUTTON_IDS:
            self.button_to_address.setdefault(button_id, defaults[button_id])

    @property
    def address_to_button(self) -> dict[tuple[str, int, int], str]:
        return {
            address.key(): button_id
            for button_id, address in self.button_to_address.items()
        }

    def parse_message(self, message: Any) -> ParsedPadMessage | None:
        message_type = getattr(message, "type", "")
        channel = int(getattr(message, "channel", 0) or 0)
        velocity = int(getattr(message, "velocity", 0) or 0)
        if message_type in {"note_on", "note_off"}:
            address = MidiAddress("note", int(getattr(message, "note", -1)), channel)
            pressed = message_type == "note_on" and velocity > 0
        elif message_type == "control_change":
            address = MidiAddress("control", int(getattr(message, "control", -1)), channel)
            pressed = int(getattr(message, "value", 0) or 0) > 0
            velocity = int(getattr(message, "value", 0) or 0)
        else:
            return None
        button_id = self.address_to_button.get(address.key())
        if not button_id:
            return None
        return ParsedPadMessage(
            button_id=button_id,
            pressed=pressed,
            address=address,
            velocity=velocity,
            raw=message,
            raw_data=message_to_raw_data(message),
        )

    def address_for_button(self, button_id: str) -> MidiAddress | None:
        return self.button_to_address.get(button_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "buttons": {button_id: address.to_dict() for button_id, address in self.button_to_address.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "MidiMapping":
        if not isinstance(data, dict):
            return cls()
        raw_buttons = data.get("buttons")
        mapping: dict[str, MidiAddress] = {}
        if isinstance(raw_buttons, dict):
            for button_id in BUTTON_IDS:
                if isinstance(raw_buttons.get(button_id), dict):
                    mapping[button_id] = MidiAddress.from_dict(raw_buttons[button_id])
        return cls(name=str(data.get("name") or "Custom Mapping"), button_to_address=mapping)

    @classmethod
    def load_user_default(cls) -> "MidiMapping":
        path = user_mapping_path()
        if path.exists():
            return cls.from_dict(read_json(path, {}))
        return cls()

    def save_user_default(self) -> None:
        write_json(user_mapping_path(), self.to_dict())

    @classmethod
    def default(cls) -> "MidiMapping":
        return cls(name="Launchpad Mini MK3 Programmer Mode", button_to_address=build_programmer_mode_mapping())

    @classmethod
    def restore_user_default(cls) -> "MidiMapping":
        mapping = cls.default()
        mapping.save_user_default()
        return mapping

    def verification_table(self) -> list[dict[str, int | str]]:
        rows: list[dict[str, int | str]] = []
        for button_id in BUTTON_IDS:
            address = self.button_to_address[button_id]
            rows.append(
                {
                    "button_id": button_id,
                    "message_type": address.message_type,
                    "number": address.number,
                    "channel": address.channel,
                }
            )
        return rows


def build_programmer_mode_mapping() -> dict[str, MidiAddress]:
    mapping: dict[str, MidiAddress] = {}
    for row_index, row in enumerate(BUTTON_ROWS):
        midi_row = 8 - row_index
        for column in range(1, 9):
            button_id = f"{row}{column}"
            note = midi_row * 10 + column
            mapping[button_id] = MidiAddress("note", note, 0)
    return mapping


def user_mapping_path() -> Path:
    return MIDI_MAPPINGS_DIR / "launchpad_mini_mk3.json"


def message_to_raw_data(message: Any) -> list[int]:
    try:
        return list(message.bytes())
    except Exception:
        return []


def message_to_address(message: Any) -> MidiAddress | None:
    message_type = getattr(message, "type", "")
    channel = int(getattr(message, "channel", 0) or 0)
    if message_type in {"note_on", "note_off"}:
        return MidiAddress("note", int(getattr(message, "note", -1)), channel)
    if message_type == "control_change":
        return MidiAddress("control", int(getattr(message, "control", -1)), channel)
    return None
