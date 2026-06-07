import sys
import types

from openlaunchdeck.audio.output_devices import hidden_advanced_output_count, hidden_duplicate_count, list_output_devices


class DeviceTestDouble:
    def __init__(self, device_id, description):
        self._device_id = device_id
        self._description = description

    def id(self):
        return self._device_id

    def description(self):
        return self._description


class MediaDevicesTestDouble:
    devices = []

    @staticmethod
    def audioOutputs():
        return list(MediaDevicesTestDouble.devices)


def install_qt_test_double(monkeypatch):
    qt_module_test_double = types.SimpleNamespace(QMediaDevices=MediaDevicesTestDouble)
    monkeypatch.setitem(sys.modules, "PySide6.QtMultimedia", qt_module_test_double)


def test_output_devices_hide_duplicate_descriptions(monkeypatch):
    install_qt_test_double(monkeypatch)
    MediaDevicesTestDouble.devices = [
        DeviceTestDouble(b"realtek", "Speakers (Realtek USB2.0 Audio)"),
        DeviceTestDouble(b"mixer-1", "Speakers (Studio Virtual Mixer VAIO)"),
        DeviceTestDouble(b"mixer-2", "Speakers (Studio Virtual Mixer VAIO)"),
        DeviceTestDouble(b"mixer-3", "  Speakers (Studio Virtual Mixer VAIO)  "),
    ]

    devices = list_output_devices()

    assert [device["description"] for device in devices] == [
        "Speakers (Realtek USB2.0 Audio)",
        "Speakers (Studio Virtual Mixer VAIO)",
    ]
    assert devices[1]["id"] == "mixer-1"
    assert devices[1]["duplicate_count"] == 3
    assert devices[1]["hidden_duplicate_count"] == 2
    assert hidden_duplicate_count(devices) == 2


def test_output_devices_can_include_raw_duplicates(monkeypatch):
    install_qt_test_double(monkeypatch)
    MediaDevicesTestDouble.devices = [
        DeviceTestDouble("a", "Speakers (Studio Virtual Mixer VAIO)"),
        DeviceTestDouble("b", "Speakers (Studio Virtual Mixer VAIO)"),
    ]

    devices = list_output_devices(include_duplicates=True)

    assert [device["id"] for device in devices] == ["a", "b"]
    assert hidden_duplicate_count(devices) == 0


def test_output_devices_hide_advanced_mixer_buses(monkeypatch):
    install_qt_test_double(monkeypatch)
    MediaDevicesTestDouble.devices = [
        DeviceTestDouble("aux", "Studio Mixer AUX Input (Studio Virtual Mixer VAIO)"),
        DeviceTestDouble("in-1", "Studio Mixer In 1 (Studio Virtual Mixer VAIO)"),
        DeviceTestDouble("in-2", "Studio Mixer In 2 (Studio Virtual Mixer VAIO)"),
        DeviceTestDouble("main", "Studio Mixer Input (Studio Virtual Mixer VAIO)"),
    ]

    devices = list_output_devices()

    assert [device["id"] for device in devices] == ["aux", "main"]
    assert hidden_advanced_output_count() == 2


def test_output_devices_can_include_advanced_mixer_buses(monkeypatch):
    install_qt_test_double(monkeypatch)
    MediaDevicesTestDouble.devices = [
        DeviceTestDouble("in-1", "Studio Mixer In 1 (Studio Virtual Mixer VAIO)"),
    ]

    devices = list_output_devices(include_advanced=True)

    assert [device["id"] for device in devices] == ["in-1"]

