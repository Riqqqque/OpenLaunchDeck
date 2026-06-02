from openlaunchdeck.devices.midi_manager import _find_launchpad_name, _resolve_launchpad_port


def test_detects_windows_launchpad_mini_mk3_abbreviated_port_name():
    ports = [
        "Microsoft GS Wavetable Synth",
        "LPMiniMK3 MIDI",
        "MIDIIN2 (LPMiniMK3 MIDI)",
    ]

    assert _find_launchpad_name(ports) == "MIDIIN2 (LPMiniMK3 MIDI)"


def test_detects_secondary_windows_launchpad_mini_mk3_port_name():
    ports = [
        "Microsoft GS Wavetable Synth",
        "MIDIIN2 (LPMiniMK3 MIDI)",
    ]

    assert _find_launchpad_name(ports) == "MIDIIN2 (LPMiniMK3 MIDI)"


def test_detects_numbered_mido_secondary_launchpad_port_name():
    ports = [
        "LPMiniMK3 MIDI 0",
        "LPMiniMK3 MIDI 1",
    ]

    assert _find_launchpad_name(ports) == "LPMiniMK3 MIDI 1"


def test_detects_launchpad_name_without_exact_windows_abbreviation():
    ports = [
        "Generic MIDI Device",
        "Launchpad Mini MK3 MIDI",
    ]

    assert _find_launchpad_name(ports) == "Launchpad Mini MK3 MIDI"


def test_resolve_replaces_stale_primary_launchpad_interface():
    ports = [
        "LPMiniMK3 MIDI 0",
        "LPMiniMK3 MIDI 1",
    ]

    assert _resolve_launchpad_port("LPMiniMK3 MIDI 0", ports) == "LPMiniMK3 MIDI 1"


def test_resolve_keeps_available_manual_non_launchpad_port():
    ports = [
        "Custom MIDI Device",
        "LPMiniMK3 MIDI 1",
    ]

    assert _resolve_launchpad_port("Custom MIDI Device", ports) == "Custom MIDI Device"
