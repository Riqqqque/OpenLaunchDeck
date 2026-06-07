from openlaunchdeck.audio.bridge_driver import BRIDGE_INPUT_NAME, BRIDGE_OUTPUT_NAME
from openlaunchdeck.audio.voice_routing import analyze_voice_route, find_best_voice_route


def device(device_id: str, description: str) -> dict[str, str]:
    return {"id": device_id, "description": description, "display_name": description}


def test_voice_route_reports_not_configured():
    status = analyze_voice_route("", [], [])

    assert status.ready is False
    assert status.configured is False
    assert status.route_kind == "not_configured"


def test_voice_route_reports_missing_saved_output():
    status = analyze_voice_route("saved", [], [])

    assert status.ready is False
    assert status.configured is True
    assert status.route_kind == "missing_output"


def test_voice_route_matches_simple_cable_pair():
    outputs = [device("out", "CABLE Input (Virtual Cable)")]
    inputs = [device("in", "CABLE Output (Virtual Cable)")]

    status = analyze_voice_route("out", outputs, inputs)

    assert status.ready is True
    assert status.uses_legacy_mixer is False
    assert status.can_remove_legacy_mixer is True
    assert status.discord_input_name == "CABLE Output (Virtual Cable)"


def test_voice_route_matches_vb_audio_cable_windows_names():
    outputs = [device("out", "Speakers (VB-Audio Virtual Cable)")]
    inputs = [device("in", "CABLE Output (VB-Audio Virtual Cable)")]

    status = analyze_voice_route("out", outputs, inputs)

    assert status.ready is True
    assert status.route_kind == "paired_bridge"
    assert status.uses_legacy_mixer is False
    assert status.discord_input_name == "CABLE Output (VB-Audio Virtual Cable)"


def test_voice_route_matches_virtual_audio_cable_line():
    outputs = [device("out", "Line 1 (Virtual Audio Cable)")]
    inputs = [device("in", "Line 1 (Virtual Audio Cable)")]

    status = analyze_voice_route("out", outputs, inputs)

    assert status.ready is True
    assert status.route_kind == "paired_bridge"
    assert status.discord_input_name == "Line 1 (Virtual Audio Cable)"


def test_voice_route_detects_legacy_mixer_pair():
    outputs = [device("out", "Studio Mixer Input (Studio Virtual Mixer VAIO)")]
    inputs = [device("in", "Studio Mixer Out B1 (Studio Virtual Mixer VAIO)")]

    status = analyze_voice_route("out", outputs, inputs)

    assert status.ready is True
    assert status.uses_legacy_mixer is True
    assert status.can_remove_legacy_mixer is False


def test_voice_route_matches_legacy_aux_pair_before_main_pair():
    outputs = [device("out", "Studio Mixer AUX Input (Studio Virtual Mixer VAIO)")]
    inputs = [
        device("main", "Studio Mixer Out B1 (Studio Virtual Mixer VAIO)"),
        device("aux", "Studio Mixer Out B2 (Studio Virtual Mixer VAIO)"),
    ]

    status = analyze_voice_route("out", outputs, inputs)

    assert status.ready is True
    assert status.input_id == "aux"
    assert status.uses_legacy_mixer is True


def test_voice_route_requires_matching_input():
    outputs = [device("out", "CABLE Input (Virtual Cable)")]
    inputs = [device("mic", "Analogue 1 + 2 (Focusrite USB Audio)")]

    status = analyze_voice_route("out", outputs, inputs)

    assert status.ready is False
    assert status.route_kind == "missing_input"
    assert "matching recording device" in status.message


def test_find_best_voice_route_prefers_non_legacy_route():
    outputs = [
        device("legacy-out", "Studio Mixer Input (Studio Virtual Mixer VAIO)"),
        device("cable-out", "CABLE Input (Virtual Cable)"),
    ]
    inputs = [
        device("legacy-in", "Studio Mixer Out B1 (Studio Virtual Mixer VAIO)"),
        device("cable-in", "CABLE Output (Virtual Cable)"),
    ]

    status = find_best_voice_route(outputs, inputs)

    assert status is not None
    assert status.output_id == "cable-out"
    assert status.input_id == "cable-in"


def test_find_best_voice_route_prefers_openlaunchdeck_bridge():
    outputs = [
        device("cable-out", "CABLE Input (Virtual Cable)"),
        device("bridge-out", BRIDGE_OUTPUT_NAME),
    ]
    inputs = [
        device("cable-in", "CABLE Output (Virtual Cable)"),
        device("bridge-in", BRIDGE_INPUT_NAME),
    ]

    status = find_best_voice_route(outputs, inputs)

    assert status is not None
    assert status.output_id == "bridge-out"
    assert status.input_id == "bridge-in"
    assert status.route_kind == "openlaunchdeck_bridge"


def test_find_best_voice_route_returns_none_without_ready_route():
    status = find_best_voice_route(
        [device("out", "CABLE Input (Virtual Cable)")],
        [device("mic", "Analogue 1 + 2 (Focusrite USB Audio)")],
    )

    assert status is None


def test_find_best_voice_route_does_not_fallback_to_legacy_by_default():
    status = find_best_voice_route(
        [device("legacy-out", "Studio Mixer Input (Studio Virtual Mixer VAIO)")],
        [device("legacy-in", "Studio Mixer Out B1 (Studio Virtual Mixer VAIO)")],
    )

    assert status is None


def test_find_best_voice_route_can_return_legacy_when_allowed():
    status = find_best_voice_route(
        [device("legacy-out", "Studio Mixer Input (Studio Virtual Mixer VAIO)")],
        [device("legacy-in", "Studio Mixer Out B1 (Studio Virtual Mixer VAIO)")],
        allow_legacy_fallback=True,
    )

    assert status is not None
    assert status.uses_legacy_mixer is True
