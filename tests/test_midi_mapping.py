import pytest

from openlaunchdeck.devices.device_calibration import CalibrationSession
from openlaunchdeck.devices.midi_mapping import (
    MidiAddress,
    MidiMapping,
    address_for_auxiliary_control,
    auxiliary_verification_table,
    message_to_address,
    parse_auxiliary_message,
)


class FakeMessage:
    def __init__(self, type, note=None, velocity=0, channel=0, control=None, value=0):
        self.type = type
        self.note = note
        self.velocity = velocity
        self.channel = channel
        self.control = control
        self.value = value

    def bytes(self):
        if self.type in {"note_on", "note_off"}:
            status = 0x90 if self.type == "note_on" else 0x80
            return [status + self.channel, self.note, self.velocity]
        if self.type == "control_change":
            return [0xB0 + self.channel, self.control, self.value]
        return []


def test_default_mapping_programmer_mode_layout():
    mapping = MidiMapping()

    assert mapping.address_for_button("A1").number == 81
    assert mapping.address_for_button("H8").number == 18


def test_parse_note_on_to_button():
    mapping = MidiMapping()
    parsed = mapping.parse_message(FakeMessage("note_on", note=81, velocity=127))

    assert parsed is not None
    assert parsed.button_id == "A1"
    assert parsed.pressed is True


def test_parse_note_off_to_release():
    mapping = MidiMapping()
    parsed = mapping.parse_message(FakeMessage("note_off", note=81, velocity=0))

    assert parsed is not None
    assert parsed.button_id == "A1"
    assert parsed.pressed is False


def test_control_change_mapping_conversion():
    mapping = MidiMapping(name="custom", button_to_address={"A1": MidiAddress("control", 10, 1)})
    parsed = mapping.parse_message(FakeMessage("control_change", control=10, value=127, channel=1))

    assert parsed is not None
    assert parsed.button_id == "A1"
    assert parsed.raw_data == [0xB1, 10, 127]
    assert message_to_address(parsed.raw) == MidiAddress("control", 10, 1)


def test_mapping_verification_table_is_edit_friendly():
    table = MidiMapping().verification_table()

    assert table[0] == {"button_id": "A1", "message_type": "note", "number": 81, "channel": 0}
    assert table[-1] == {"button_id": "H8", "message_type": "note", "number": 18, "channel": 0}
    assert len(table) == 64


def test_partial_custom_mapping_keeps_default_fallbacks():
    mapping = MidiMapping(name="custom", button_to_address={"A1": MidiAddress("control", 20, 0)})

    assert mapping.address_for_button("A1") == MidiAddress("control", 20, 0)
    assert mapping.address_for_button("H8") == MidiAddress("note", 18, 0)
    assert len(mapping.verification_table()) == 64


def test_calibration_records_raw_messages():
    session = CalibrationSession(expected_buttons=["A1", "A2"])

    assert session.start() == "Press A1"
    assert session.capture(FakeMessage("note_on", note=81, velocity=127)) == "Press A2"
    assert session.capture(FakeMessage("control_change", control=11, value=127, channel=2)) == "Calibration complete."
    mapping = session.to_mapping()

    assert mapping.address_for_button("A1") == MidiAddress("note", 81, 0)
    assert mapping.address_for_button("A2") == MidiAddress("control", 11, 2)
    assert session.raw_log_lines()[0].startswith("A1:")


def test_mapping_rejects_duplicate_addresses():
    with pytest.raises(ValueError, match="same message"):
        MidiMapping.from_dict(
            {
                "buttons": {
                    "A1": {"message_type": "note", "number": 81, "channel": 0},
                    "A2": {"message_type": "note", "number": 81, "channel": 0},
                }
            }
        )


def test_direct_mapping_construction_rejects_duplicate_addresses():
    with pytest.raises(ValueError, match="same message"):
        MidiMapping(
            button_to_address={
                "A1": MidiAddress("note", 81),
                "A2": MidiAddress("note", 81),
            }
        )


def test_calibration_rejects_a_message_already_used_by_another_pad():
    session = CalibrationSession(expected_buttons=["A1", "A2"])
    session.start()
    message = FakeMessage("note_on", note=81, velocity=127)

    assert session.capture(message) == "Press A2"
    result = session.capture(message)

    assert result == "That message is already assigned to A1. Press A2"
    assert session.index == 1
    assert list(session.captured) == ["A1"]


def test_mapping_rejects_out_of_range_values():
    with pytest.raises(ValueError, match="between 0 and 127"):
        MidiAddress.from_dict({"message_type": "note", "number": 200, "channel": 0})


def test_programmer_mode_auxiliary_controls_use_documented_cc_map():
    left = parse_auxiliary_message(FakeMessage("control_change", control=93, value=127))
    scene_eight = parse_auxiliary_message(FakeMessage("control_change", control=19, value=127))

    assert left is not None and left.control_id == "top_left" and left.pressed is True
    assert scene_eight is not None and scene_eight.control_id == "scene_8"
    assert address_for_auxiliary_control("top_right") == MidiAddress("control", 94, 0)
    assert len(auxiliary_verification_table()) == 16


def test_auxiliary_control_release_and_unrelated_cc_are_parsed_safely():
    released = parse_auxiliary_message(FakeMessage("control_change", control=94, value=0))

    assert released is not None and released.pressed is False
    assert parse_auxiliary_message(FakeMessage("control_change", control=10, value=127)) is None
