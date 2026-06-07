from __future__ import annotations

from dataclasses import dataclass

from .input_devices import list_input_devices
from .output_devices import list_output_devices, normalize_device_description


BRIDGE_OUTPUT_NAME = "OpenLaunchDeck Voice Output"
BRIDGE_INPUT_NAME = "OpenLaunchDeck Voice Input"
BRIDGE_HARDWARE_ID = r"ROOT\OPENLAUNCHDECK_AUDIO_BRIDGE"


@dataclass(frozen=True, slots=True)
class BridgeDriverStatus:
    installed: bool
    ready: bool
    output_id: str = ""
    output_name: str = ""
    input_id: str = ""
    input_name: str = ""
    message: str = "OpenLaunchDeck Audio Bridge is not installed."


def detect_openlaunchdeck_bridge(
    output_devices: list[dict[str, str | int]] | None = None,
    input_devices: list[dict[str, str | int]] | None = None,
) -> BridgeDriverStatus:
    output_devices = output_devices if output_devices is not None else list_output_devices(include_duplicates=True, include_advanced=True)
    input_devices = input_devices if input_devices is not None else list_input_devices(include_duplicates=True)
    output = _find_named_device(output_devices, BRIDGE_OUTPUT_NAME)
    input_device = _find_named_device(input_devices, BRIDGE_INPUT_NAME)
    if output is None and input_device is None:
        return BridgeDriverStatus(installed=False, ready=False)
    if output is None:
        return BridgeDriverStatus(
            installed=True,
            ready=False,
            input_id=str(input_device.get("id") or ""),
            input_name=_device_name(input_device),
            message=f"{BRIDGE_INPUT_NAME} exists, but {BRIDGE_OUTPUT_NAME} is missing.",
        )
    if input_device is None:
        return BridgeDriverStatus(
            installed=True,
            ready=False,
            output_id=str(output.get("id") or ""),
            output_name=_device_name(output),
            message=f"{BRIDGE_OUTPUT_NAME} exists, but {BRIDGE_INPUT_NAME} is missing.",
        )
    return BridgeDriverStatus(
        installed=True,
        ready=True,
        output_id=str(output.get("id") or ""),
        output_name=_device_name(output),
        input_id=str(input_device.get("id") or ""),
        input_name=_device_name(input_device),
        message=f"OpenLaunchDeck Audio Bridge is ready. Set Discord input to {BRIDGE_INPUT_NAME}.",
    )


def is_openlaunchdeck_bridge_device(description: str) -> bool:
    normalized = normalize_device_description(description)
    return normalized in {
        normalize_device_description(BRIDGE_OUTPUT_NAME),
        normalize_device_description(BRIDGE_INPUT_NAME),
    }


def _find_named_device(devices: list[dict[str, str | int]], name: str) -> dict[str, str | int] | None:
    normalized_name = normalize_device_description(name)
    for device in devices:
        if normalize_device_description(_device_name(device)) == normalized_name:
            return device
    return None


def _device_name(device: dict[str, str | int]) -> str:
    return str(device.get("display_name") or device.get("description") or "Audio device")
