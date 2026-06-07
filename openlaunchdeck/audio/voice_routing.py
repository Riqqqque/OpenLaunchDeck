from __future__ import annotations

from dataclasses import dataclass

from .input_devices import list_input_devices
from .output_devices import list_output_devices, normalize_device_description


LEGACY_MIXER_MARKERS = ("virtual mixer vaio",)


@dataclass(frozen=True, slots=True)
class VoiceRouteStatus:
    configured: bool
    ready: bool
    output_id: str
    output_name: str
    input_id: str
    input_name: str
    route_kind: str
    message: str
    uses_legacy_mixer: bool = False

    @property
    def discord_input_name(self) -> str:
        return self.input_name

    @property
    def can_remove_legacy_mixer(self) -> bool:
        return self.ready and not self.uses_legacy_mixer


def current_voice_route_status(output_device_id: str) -> VoiceRouteStatus:
    return analyze_voice_route(
        output_device_id,
        list_output_devices(include_duplicates=True, include_advanced=True),
        list_input_devices(include_duplicates=True),
    )


def find_best_voice_route(
    output_devices: list[dict[str, str | int]] | None = None,
    input_devices: list[dict[str, str | int]] | None = None,
    avoid_legacy: bool = True,
    allow_legacy_fallback: bool = False,
) -> VoiceRouteStatus | None:
    output_devices = output_devices if output_devices is not None else list_output_devices(include_duplicates=True, include_advanced=True)
    input_devices = input_devices if input_devices is not None else list_input_devices(include_duplicates=True)
    ready_routes = [
        analyze_voice_route(str(output.get("id") or ""), output_devices, input_devices)
        for output in output_devices
    ]
    ready_routes = [route for route in ready_routes if route.ready]
    if not ready_routes:
        return None
    if avoid_legacy:
        for route in ready_routes:
            if not route.uses_legacy_mixer:
                return route
        if not allow_legacy_fallback:
            return None
    return ready_routes[0]


def analyze_voice_route(
    output_device_id: str,
    output_devices: list[dict[str, str | int]],
    input_devices: list[dict[str, str | int]],
) -> VoiceRouteStatus:
    output_id = str(output_device_id or "")
    if not output_id:
        return VoiceRouteStatus(
            configured=False,
            ready=False,
            output_id="",
            output_name="",
            input_id="",
            input_name="",
            route_kind="not_configured",
            message="Choose a voice route output device for routed soundboard buttons.",
        )

    output = _find_device(output_devices, output_id)
    if output is None:
        return VoiceRouteStatus(
            configured=True,
            ready=False,
            output_id=output_id,
            output_name="Saved output is not currently available",
            input_id="",
            input_name="",
            route_kind="missing_output",
            message="The saved voice route output is not available in Windows right now.",
        )

    output_name = _device_name(output)
    input_device, route_kind = find_matching_voice_input(output_name, input_devices)
    uses_legacy = route_kind == "legacy_mixer" or _is_legacy_mixer(output_name) or (
        input_device is not None and _is_legacy_mixer(_device_name(input_device))
    )
    if input_device is None:
        return VoiceRouteStatus(
            configured=True,
            ready=False,
            output_id=output_id,
            output_name=output_name,
            input_id="",
            input_name="",
            route_kind="missing_input",
            message="Windows does not expose a matching recording device for Discord to use.",
            uses_legacy_mixer=uses_legacy,
        )

    input_name = _device_name(input_device)
    message = f"Route ready. Set Discord input to {input_name}."
    if uses_legacy:
        message = "Route works, but it still uses the old mixer driver. Replace it before uninstalling that driver."
    return VoiceRouteStatus(
        configured=True,
        ready=True,
        output_id=output_id,
        output_name=output_name,
        input_id=str(input_device.get("id") or ""),
        input_name=input_name,
        route_kind=route_kind,
        message=message,
        uses_legacy_mixer=uses_legacy,
    )


def find_matching_voice_input(
    output_name: str,
    input_devices: list[dict[str, str | int]],
) -> tuple[dict[str, str | int] | None, str]:
    output_key = _route_key(output_name)
    normalized_output = normalize_device_description(output_name)
    for input_device in input_devices:
        input_name = _device_name(input_device)
        if _route_key(input_name) == output_key and output_key:
            return input_device, "paired_bridge"
        if _is_legacy_pair(normalized_output, normalize_device_description(input_name)):
            return input_device, "legacy_mixer"
        if "stereo mix" in normalize_device_description(input_name):
            return input_device, "system_mix"
    return None, "missing_input"


def _find_device(devices: list[dict[str, str | int]], device_id: str) -> dict[str, str | int] | None:
    for device in devices:
        if str(device.get("id") or "") == device_id:
            return device
    return None


def _device_name(device: dict[str, str | int]) -> str:
    return str(device.get("display_name") or device.get("description") or "Audio device")


def _route_key(description: str) -> str:
    normalized = normalize_device_description(description)
    replacements = (
        (" playback", ""),
        (" recording", ""),
        (" input", ""),
        (" output", ""),
        (" speakers", ""),
        (" microphone", ""),
        ("(", " "),
        (")", " "),
        ("-", " "),
    )
    for old, new in replacements:
        normalized = normalized.replace(old, new)
    words = [
        word
        for word in normalized.split()
        if word
        and word not in {"audio", "device", "virtual", "driver", "wdm"}
    ]
    return " ".join(words)


def _is_legacy_mixer(description: str) -> bool:
    normalized = normalize_device_description(description)
    return any(marker in normalized for marker in LEGACY_MIXER_MARKERS)


def _is_legacy_pair(output_name: str, input_name: str) -> bool:
    if "vaio" not in output_name or "vaio" not in input_name:
        return False
    if "vaio3 input" in output_name and "out b3" in input_name:
        return True
    if "aux input" in output_name and "out b2" in input_name:
        return True
    if "aux input" not in output_name and "vaio3 input" not in output_name and "input" in output_name and "out b1" in input_name:
        return True
    return False
