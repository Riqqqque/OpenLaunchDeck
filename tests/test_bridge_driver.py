from openlaunchdeck.audio.bridge_driver import (
    BRIDGE_INPUT_NAME,
    BRIDGE_OUTPUT_NAME,
    detect_openlaunchdeck_bridge,
    is_openlaunchdeck_bridge_device,
)


def device(device_id: str, description: str) -> dict[str, str]:
    return {"id": device_id, "description": description, "display_name": description}


def test_detect_openlaunchdeck_bridge_ready_when_both_endpoints_exist():
    status = detect_openlaunchdeck_bridge(
        [device("out", BRIDGE_OUTPUT_NAME)],
        [device("in", BRIDGE_INPUT_NAME)],
    )

    assert status.installed is True
    assert status.ready is True
    assert status.output_id == "out"
    assert status.input_id == "in"
    assert "voice chat input" in status.message


def test_detect_openlaunchdeck_bridge_reports_missing_input():
    status = detect_openlaunchdeck_bridge(
        [device("out", BRIDGE_OUTPUT_NAME)],
        [device("mic", "Streamer Mic")],
    )

    assert status.installed is True
    assert status.ready is False
    assert BRIDGE_INPUT_NAME in status.message


def test_detect_openlaunchdeck_bridge_reports_not_installed():
    status = detect_openlaunchdeck_bridge(
        [device("out", "Speakers")],
        [device("mic", "Streamer Mic")],
    )

    assert status.installed is False
    assert status.ready is False


def test_bridge_name_detection_is_exact():
    assert is_openlaunchdeck_bridge_device(BRIDGE_OUTPUT_NAME)
    assert is_openlaunchdeck_bridge_device(BRIDGE_INPUT_NAME)
    assert not is_openlaunchdeck_bridge_device("OpenLaunchDeck Headphones")
