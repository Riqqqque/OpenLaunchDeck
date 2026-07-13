from openlaunchdeck.actions import type_text
from openlaunchdeck.actions.type_text import TypeTextAction, _utf16_code_units


def test_utf16_code_units_support_bmp_and_surrogate_pairs():
    assert _utf16_code_units("A") == [0x0041]
    assert _utf16_code_units("\U0001F600") == [0xD83D, 0xDE00]


def test_type_text_uses_native_windows_input(monkeypatch):
    calls = []
    monkeypatch.setattr(type_text.sys, "platform", "win32")
    monkeypatch.setattr(type_text, "_send_text_windows", lambda text, interval: calls.append((text, interval)))

    result = TypeTextAction().execute(None, {"text": "hello", "interval": 0.01})

    assert result.success
    assert calls == [("hello", 0.01)]


def test_type_text_rejects_invalid_interval():
    result = TypeTextAction().execute(None, {"text": "hello", "interval": "fast"})

    assert not result.success
    assert "number" in result.message
