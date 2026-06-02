import sys
import types

from openlaunchdeck.audio.output_devices import hidden_advanced_output_count, hidden_duplicate_count, list_output_devices


class FakeDevice:
    def __init__(self, device_id, description):
        self._device_id = device_id
        self._description = description

    def id(self):
        return self._device_id

    def description(self):
        return self._description


class FakeMediaDevices:
    devices = []

    @staticmethod
    def audioOutputs():
        return list(FakeMediaDevices.devices)


def install_fake_qt(monkeypatch):
    fake_module = types.SimpleNamespace(QMediaDevices=FakeMediaDevices)
    monkeypatch.setitem(sys.modules, "PySide6.QtMultimedia", fake_module)


def test_output_devices_hide_duplicate_descriptions(monkeypatch):
    install_fake_qt(monkeypatch)
    FakeMediaDevices.devices = [
        FakeDevice(b"realtek", "Speakers (Realtek USB2.0 Audio)"),
        FakeDevice(b"voicemeeter-1", "Speakers (VB-Audio Voicemeeter VAIO)"),
        FakeDevice(b"voicemeeter-2", "Speakers (VB-Audio Voicemeeter VAIO)"),
        FakeDevice(b"voicemeeter-3", "  Speakers (VB-Audio Voicemeeter VAIO)  "),
    ]

    devices = list_output_devices()

    assert [device["description"] for device in devices] == [
        "Speakers (Realtek USB2.0 Audio)",
        "Speakers (VB-Audio Voicemeeter VAIO)",
    ]
    assert devices[1]["id"] == "voicemeeter-1"
    assert devices[1]["duplicate_count"] == 3
    assert devices[1]["hidden_duplicate_count"] == 2
    assert hidden_duplicate_count(devices) == 2


def test_output_devices_can_include_raw_duplicates(monkeypatch):
    install_fake_qt(monkeypatch)
    FakeMediaDevices.devices = [
        FakeDevice("a", "Speakers (VB-Audio Voicemeeter VAIO)"),
        FakeDevice("b", "Speakers (VB-Audio Voicemeeter VAIO)"),
    ]

    devices = list_output_devices(include_duplicates=True)

    assert [device["id"] for device in devices] == ["a", "b"]
    assert hidden_duplicate_count(devices) == 0


def test_output_devices_hide_advanced_voicemeeter_buses(monkeypatch):
    install_fake_qt(monkeypatch)
    FakeMediaDevices.devices = [
        FakeDevice("aux", "Voicemeeter AUX Input (VB-Audio Voicemeeter VAIO)"),
        FakeDevice("in-1", "Voicemeeter In 1 (VB-Audio Voicemeeter VAIO)"),
        FakeDevice("in-2", "Voicemeeter In 2 (VB-Audio Voicemeeter VAIO)"),
        FakeDevice("main", "Voicemeeter Input (VB-Audio Voicemeeter VAIO)"),
    ]

    devices = list_output_devices()

    assert [device["id"] for device in devices] == ["aux", "main"]
    assert hidden_advanced_output_count() == 2


def test_output_devices_can_include_advanced_voicemeeter_buses(monkeypatch):
    install_fake_qt(monkeypatch)
    FakeMediaDevices.devices = [
        FakeDevice("in-1", "Voicemeeter In 1 (VB-Audio Voicemeeter VAIO)"),
    ]

    devices = list_output_devices(include_advanced=True)

    assert [device["id"] for device in devices] == ["in-1"]
