from __future__ import annotations


def list_output_devices() -> list[dict[str, str]]:
    try:
        from PySide6.QtMultimedia import QMediaDevices
    except Exception:
        return []
    devices = []
    for device in QMediaDevices.audioOutputs():
        devices.append(
            {
                "id": bytes(device.id()).decode(errors="replace"),
                "description": device.description(),
            }
        )
    return devices
