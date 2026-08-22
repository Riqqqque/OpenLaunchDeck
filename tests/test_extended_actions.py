from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from PySide6.QtWidgets import QApplication

from openlaunchdeck.actions import mouse_control
from openlaunchdeck.actions.clipboard_action import ClipboardAction
from openlaunchdeck.actions.context import ActionContext
from openlaunchdeck.actions.mouse_control import (
    MOUSEEVENTF_LEFTDOWN,
    MOUSEEVENTF_LEFTUP,
    MOUSEEVENTF_WHEEL,
    MouseControlAction,
    _mouse_events,
    _send_mouse_windows,
)
from openlaunchdeck.actions.navigate_deck import NavigateDeckAction
from openlaunchdeck.actions.random_sound import RandomSoundAction, _choose_sound
from openlaunchdeck.actions.switch_profile import SwitchProfileAction
from openlaunchdeck.actions.window_control import _control_foreground_window
from openlaunchdeck.models.button import ButtonConfig
from openlaunchdeck.models.page import Page
from openlaunchdeck.models.profile import Profile


class FakeProfileService:
    def __init__(self) -> None:
        first = Profile(
            name="First",
            id="first",
            pages=[Page.blank("Main", "main"), Page.blank("Second", "second")],
            default_page="main",
        )
        second = Profile.blank("Second Profile", "second_profile")
        self.profiles = {first.id: first, second.id: second}
        self.current_profile_id = first.id
        self.current_page_id = first.default_page

    @property
    def current_profile(self):
        return self.profiles[self.current_profile_id]

    @property
    def current_page(self):
        return self.current_profile.get_page(self.current_page_id)

    def set_current_page(self, page_id: str) -> bool:
        if page_id not in self.current_profile.page_ids():
            return False
        self.current_page_id = page_id
        return True

    def set_current_profile(self, profile_id: str) -> bool:
        if profile_id not in self.profiles:
            return False
        self.current_profile_id = profile_id
        self.current_page_id = self.current_profile.default_page
        return True


class FakeAudio:
    def __init__(self) -> None:
        self.stopped = []

    def stop_page(self, page_id: str, only_page_change: bool = False) -> None:
        self.stopped.append((page_id, only_page_change))


class FakeSettings:
    def __init__(self) -> None:
        self.changes = []

    def update(self, **changes) -> None:
        self.changes.append(changes)


def make_context(service=None, audio=None, settings=None, executor=None) -> ActionContext:
    service = service or FakeProfileService()
    return ActionContext(
        logger=None,
        current_profile=service.current_profile,
        current_page=service.current_page,
        button_id="A1",
        button_config=ButtonConfig.blank("A1"),
        profile_service=service,
        audio_engine=audio,
        settings_service=settings,
        action_executor=executor,
    )


def test_navigate_deck_moves_pages_and_profiles_with_wrap():
    service = FakeProfileService()
    audio = FakeAudio()
    settings = FakeSettings()
    context = make_context(service, audio, settings)
    action = NavigateDeckAction()

    result = action.execute(context, {"operation": "previous_page", "wrap": True})
    assert result.success and service.current_page_id == "second"
    result = action.execute(context, {"operation": "next_profile", "wrap": True})

    assert result.success and result.details["profile_changed"] is True
    assert service.current_profile_id == "second_profile"
    assert settings.changes == [{"default_profile": "second_profile"}]
    assert audio.stopped == [("main", True), ("second", True)]


def test_navigate_deck_can_stop_at_page_boundary():
    service = FakeProfileService()
    result = NavigateDeckAction().execute(make_context(service), {"operation": "previous_page", "wrap": False})

    assert not result.success
    assert service.current_page_id == "main"


def test_switch_profile_uses_dynamic_target_and_persists_default():
    service = FakeProfileService()
    settings = FakeSettings()
    result = SwitchProfileAction().execute(
        make_context(service, FakeAudio(), settings),
        {"profile_id": "second_profile"},
    )

    assert result.success
    assert service.current_profile_id == "second_profile"
    assert settings.changes == [{"default_profile": "second_profile"}]


def test_clipboard_action_copies_and_clears_text():
    app = QApplication.instance() or QApplication([])
    action = ClipboardAction()
    context = make_context()

    assert action.execute(context, {"operation": "copy_text", "text": "ready"}).success
    assert app.clipboard().text() == "ready"
    assert action.execute(context, {"operation": "clear"}).success
    assert app.clipboard().text() == ""


class FakeUser32:
    def __init__(self, process_id: int = 99999) -> None:
        self.process_id = process_id
        self.shown = []
        self.posted = []

    def GetForegroundWindow(self):
        return 123

    def GetWindowThreadProcessId(self, _hwnd, pointer):
        pointer._obj.value = self.process_id
        return 1

    def PostMessageW(self, *args):
        self.posted.append(args)
        return 1

    def ShowWindowAsync(self, hwnd, command):
        self.shown.append((hwnd, command))
        return 0


def test_window_control_sends_nonblocking_show_and_close_requests():
    user32 = FakeUser32()

    assert _control_foreground_window("maximize", user32).success
    assert user32.shown == [(123, 3)]
    assert _control_foreground_window("close", user32).success
    assert user32.posted[0][1] == 0x0010


def test_mouse_control_uses_requested_click_and_scroll(monkeypatch):
    calls = []
    fake = SimpleNamespace(
        click=lambda **kwargs: calls.append(("click", kwargs)),
        scroll=lambda amount, **kwargs: calls.append(("scroll", amount, kwargs)),
    )
    monkeypatch.setitem(__import__("sys").modules, "pyautogui", fake)
    monkeypatch.setattr(mouse_control.sys, "platform", "linux")
    action = MouseControlAction()

    assert action.execute(make_context(), {"operation": "double_click"}).success
    assert action.execute(make_context(), {"operation": "scroll_down", "scroll_amount": 5}).success
    assert calls[0][1]["clicks"] == 2
    assert calls[1][1] == -5


def test_windows_mouse_control_uses_native_backend(monkeypatch):
    calls = []
    monkeypatch.setattr(mouse_control.sys, "platform", "win32")
    monkeypatch.setattr(mouse_control, "_send_mouse_windows", lambda operation, amount: calls.append((operation, amount)))

    result = MouseControlAction().execute(make_context(), {"operation": "right_click"})

    assert result.success
    assert calls == [("right_click", 3)]


def test_native_mouse_event_sequences_cover_clicks_and_signed_scroll():
    assert _mouse_events("left_click", 3) == [
        (MOUSEEVENTF_LEFTDOWN, 0),
        (MOUSEEVENTF_LEFTUP, 0),
    ]
    assert _mouse_events("double_click", 3) == [
        (MOUSEEVENTF_LEFTDOWN, 0),
        (MOUSEEVENTF_LEFTUP, 0),
        (MOUSEEVENTF_LEFTDOWN, 0),
        (MOUSEEVENTF_LEFTUP, 0),
    ]
    assert _mouse_events("scroll_up", 4) == [(MOUSEEVENTF_WHEEL, 480)]
    assert _mouse_events("scroll_down", 4) == [(MOUSEEVENTF_WHEEL, -480)]


def test_native_mouse_sender_builds_windows_input_structures():
    calls = []

    class SendInput:
        argtypes = None
        restype = None

        def __call__(self, count, inputs, structure_size):
            calls.append(
                (
                    count,
                    [inputs[index].mi.dwFlags for index in range(count)],
                    [inputs[index].mi.mouseData for index in range(count)],
                    structure_size,
                )
            )
            return count

    _send_mouse_windows("scroll_down", 4, SimpleNamespace(SendInput=SendInput()))

    assert calls[0][0] == 1
    assert calls[0][1] == [MOUSEEVENTF_WHEEL]
    assert calls[0][2][0] & 0xFFFFFFFF == (-480) & 0xFFFFFFFF
    assert calls[0][3] > 0


def test_random_sound_selection_and_dispatch(tmp_path, monkeypatch):
    (tmp_path / "ignore.txt").write_text("x", encoding="utf-8")
    sound = tmp_path / "clip.wav"
    sound.write_bytes(b"RIFF")
    monkeypatch.setattr("openlaunchdeck.actions.random_sound.random.randrange", lambda _count: 0)
    calls = []

    assert _choose_sound(tmp_path, recursive=False) == sound
    context = make_context(executor=lambda action_type, _context, config: calls.append((action_type, config)) or SimpleNamespace(success=True))
    result = RandomSoundAction().execute(
        context,
        {
            "folder_path": str(tmp_path),
            "volume": 65,
            "loop": True,
            "behavior_when_already_playing": "overlap",
            "stop_on_page_change": True,
        },
    )

    assert result.success
    assert calls[0][0] == "play_sound"
    assert Path(calls[0][1]["file_path"]) == sound
    assert calls[0][1]["loop"] is True
    assert calls[0][1]["behavior_when_already_playing"] == "overlap"
    assert calls[0][1]["stop_on_page_change"] is True


def test_random_sound_does_not_start_after_page_change(tmp_path, monkeypatch):
    sound = tmp_path / "clip.wav"
    sound.write_bytes(b"RIFF")
    service = FakeProfileService()
    calls = []

    def change_page_during_scan(_folder, _recursive):
        service.set_current_page("second")
        return sound

    monkeypatch.setattr("openlaunchdeck.actions.random_sound._choose_sound", change_page_during_scan)
    context = make_context(
        service=service,
        executor=lambda action_type, _context, config: calls.append((action_type, config)),
    )

    result = RandomSoundAction().execute(
        context,
        {"folder_path": str(tmp_path), "stop_on_page_change": True},
    )

    assert not result.success
    assert calls == []
