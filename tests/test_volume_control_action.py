from __future__ import annotations

import sys
import types

from openlaunchdeck.actions.volume_control import VolumeControlAction


class FakeVolumeController:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def step_up(self) -> None:
        self.calls.append(("up", None))

    def step_down(self) -> None:
        self.calls.append(("down", None))

    def set_volume_percent(self, value: int) -> None:
        self.calls.append(("set", value))

    def set_muted(self, muted: bool) -> None:
        self.calls.append(("mute", muted))

    def toggle_mute(self) -> bool:
        self.calls.append(("toggle", None))
        return True


def test_volume_control_uses_windows_endpoint_controller(monkeypatch):
    controller = FakeVolumeController()
    monkeypatch.setattr("openlaunchdeck.actions.volume_control.create_volume_controller", lambda: controller)
    action = VolumeControlAction()

    assert action.execute(None, {"mode": "set_volume", "target_volume": 150}).success is True
    assert action.execute(None, {"mode": "mute"}).success is True
    assert action.execute(None, {"mode": "unmute"}).success is True
    assert action.execute(None, {"mode": "toggle_mute"}).message == "Volume muted."

    assert controller.calls == [("set", 100), ("mute", True), ("mute", False), ("toggle", None)]


def test_volume_control_falls_back_to_media_key_for_step(monkeypatch):
    pressed = []
    monkeypatch.setattr("openlaunchdeck.actions.volume_control.create_volume_controller", lambda: None)
    monkeypatch.setitem(sys.modules, "pyautogui", types.SimpleNamespace(press=lambda key: pressed.append(key)))
    action = VolumeControlAction()

    result = action.execute(None, {"mode": "volume_down"})

    assert result.success is True
    assert pressed == ["volumedown"]


def test_volume_control_fails_set_volume_without_endpoint_controller(monkeypatch):
    monkeypatch.setattr("openlaunchdeck.actions.volume_control.create_volume_controller", lambda: None)
    action = VolumeControlAction()

    result = action.execute(None, {"mode": "set_volume", "target_volume": 50})

    assert result.success is False
    assert "endpoint volume control" in result.message
