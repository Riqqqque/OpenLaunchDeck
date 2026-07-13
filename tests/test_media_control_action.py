from openlaunchdeck.actions import media_control
from openlaunchdeck.actions.media_control import MediaControlAction, WINDOWS_MEDIA_KEYS


def test_media_controls_use_native_windows_input(monkeypatch):
    calls = []
    monkeypatch.setattr(media_control.sys, "platform", "win32")
    monkeypatch.setattr(media_control, "send_hotkey", lambda keys: calls.append(keys) or "windows")

    for operation, key in WINDOWS_MEDIA_KEYS.items():
        result = MediaControlAction().execute(None, {"control": operation})
        assert result.success
        assert calls[-1] == [key]
