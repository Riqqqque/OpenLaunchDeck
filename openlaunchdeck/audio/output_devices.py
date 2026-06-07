from __future__ import annotations

import re


def device_id_from_qt(device) -> str:
    try:
        raw_id = device.id()
        if isinstance(raw_id, bytes):
            return raw_id.decode(errors="replace")
        if isinstance(raw_id, str):
            return raw_id
        return bytes(raw_id).decode(errors="replace")
    except Exception:
        return ""


def normalize_device_description(description: str) -> str:
    return re.sub(r"\s+", " ", str(description or "").strip()).casefold()


def is_advanced_virtual_output(description: str) -> bool:
    normalized = normalize_device_description(description)
    return bool(re.match(r"^.+\bin \d+\b.*\bvaio\b.*$", normalized))


def list_output_devices(include_duplicates: bool = False, include_advanced: bool = False) -> list[dict[str, str | int]]:
    try:
        from PySide6.QtMultimedia import QMediaDevices
    except Exception:
        return []

    devices: list[dict[str, str | int]] = []
    seen_by_description: dict[str, dict[str, str | int]] = {}
    for device in QMediaDevices.audioOutputs():
        description = str(device.description() or "Audio output").strip() or "Audio output"
        if not include_advanced and is_advanced_virtual_output(description):
            continue
        device_id = device_id_from_qt(device)
        item: dict[str, str | int] = {
            "id": device_id,
            "description": description,
            "display_name": description,
            "duplicate_count": 1,
            "hidden_duplicate_count": 0,
        }
        if include_duplicates:
            devices.append(item)
            continue

        key = normalize_device_description(description)
        existing = seen_by_description.get(key)
        if existing is None:
            seen_by_description[key] = item
            devices.append(item)
        else:
            existing["duplicate_count"] = int(existing.get("duplicate_count", 1)) + 1
            existing["hidden_duplicate_count"] = int(existing.get("hidden_duplicate_count", 0)) + 1
    return devices


def hidden_duplicate_count(devices: list[dict[str, str | int]]) -> int:
    return sum(int(device.get("hidden_duplicate_count", 0)) for device in devices)


def hidden_advanced_output_count() -> int:
    return sum(
        1
        for device in list_output_devices(include_duplicates=True, include_advanced=True)
        if is_advanced_virtual_output(str(device.get("description") or ""))
    )
