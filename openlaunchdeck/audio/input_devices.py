from __future__ import annotations

from .output_devices import device_id_from_qt, normalize_device_description


def list_input_devices(include_duplicates: bool = False) -> list[dict[str, str | int]]:
    try:
        from PySide6.QtMultimedia import QMediaDevices
    except Exception:
        return []

    devices: list[dict[str, str | int]] = []
    seen_by_description: dict[str, dict[str, str | int]] = {}
    for device in QMediaDevices.audioInputs():
        description = str(device.description() or "Audio input").strip() or "Audio input"
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
