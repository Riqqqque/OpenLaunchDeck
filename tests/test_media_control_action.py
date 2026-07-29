from openlaunchdeck.actions import media_control
from openlaunchdeck.actions.media_control import (
    MediaControlAction,
    WINDOWS_APP_COMMANDS,
    WINDOWS_MEDIA_KEYS,
    _send_app_command_windows,
)


class FakeFunction:
    def __init__(self, callback):
        self.callback = callback
        self.argtypes = None
        self.restype = None

    def __call__(self, *args):
        return self.callback(*args)


class FakeUser32:
    def __init__(self, foreground=1234, send_result=1):
        self.calls = []
        self.GetForegroundWindow = FakeFunction(lambda: foreground)
        self.SendNotifyMessageW = FakeFunction(self._send)
        self.send_result = send_result

    def _send(self, *args):
        self.calls.append(args)
        return self.send_result


def test_windows_media_controls_send_app_commands(monkeypatch):
    calls = []
    monkeypatch.setattr(media_control.sys, "platform", "win32")
    monkeypatch.setattr(media_control, "_send_app_command_windows", lambda control: calls.append(control))

    for operation in WINDOWS_APP_COMMANDS:
        result = MediaControlAction().execute(None, {"control": operation})
        assert result.success
        assert calls[-1] == operation


def test_app_command_uses_foreground_window_without_waiting():
    user32 = FakeUser32()

    _send_app_command_windows("play_pause", user32)

    assert user32.calls == [(1234, 0x0319, 1234, WINDOWS_APP_COMMANDS["play_pause"] << 16)]


def test_windows_media_control_falls_back_to_keyboard(monkeypatch):
    calls = []
    monkeypatch.setattr(media_control.sys, "platform", "win32")
    monkeypatch.setattr(
        media_control,
        "_send_app_command_windows",
        lambda _control: (_ for _ in ()).throw(RuntimeError("message blocked")),
    )
    monkeypatch.setattr(media_control, "send_hotkey", lambda keys: calls.append(keys) or "windows")

    result = MediaControlAction().execute(None, {"control": "play_pause"})

    assert result.success
    assert calls == [[WINDOWS_MEDIA_KEYS["play_pause"]]]


def test_windows_media_control_reports_both_backend_failures(monkeypatch):
    monkeypatch.setattr(media_control.sys, "platform", "win32")
    monkeypatch.setattr(
        media_control,
        "_send_app_command_windows",
        lambda _control: (_ for _ in ()).throw(RuntimeError("message blocked")),
    )
    monkeypatch.setattr(
        media_control,
        "send_hotkey",
        lambda _keys: (_ for _ in ()).throw(RuntimeError("input blocked")),
    )

    result = MediaControlAction().execute(None, {"control": "play_pause"})

    assert not result.success
    assert "message blocked" in result.message
    assert "input blocked" in result.message


def test_media_control_rejects_unknown_operation():
    result = MediaControlAction().execute(None, {"control": "not-a-control"})

    assert not result.success
    assert result.message == "Unknown media control."
