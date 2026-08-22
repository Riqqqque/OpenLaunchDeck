from __future__ import annotations

from collections.abc import Iterable

from .base import BaseAction


class ActionRegistry:
    def __init__(self) -> None:
        self._actions: dict[str, BaseAction] = {}

    def register(self, action: BaseAction) -> None:
        self._actions[action.type_name] = action

    def get(self, action_type: str) -> BaseAction:
        return self._actions.get(action_type, self._actions["noop"])

    def all(self) -> Iterable[BaseAction]:
        return self._actions.values()

    def names(self) -> list[str]:
        return sorted(self._actions)

    def has(self, action_type: str) -> bool:
        return action_type in self._actions


def create_default_registry() -> ActionRegistry:
    from .clipboard_action import ClipboardAction
    from .delay import DelayAction
    from .hotkey import HotkeyAction
    from .http_request import HttpRequestAction
    from .media_control import MediaControlAction
    from .mouse_control import MouseControlAction
    from .multi_action import MultiAction
    from .navigate_deck import NavigateDeckAction
    from .noop import NoopAction
    from .obs_websocket import ObsWebSocketAction
    from .open_path import OpenPathAction
    from .open_url import OpenUrlAction
    from .play_sound import PlaySoundAction
    from .powershell import PowerShellAction
    from .random_sound import RandomSoundAction
    from .run_command import RunCommandAction
    from .ssh_command import SshCommandAction
    from .stop_sound import StopSoundAction
    from .switch_page import SwitchPageAction
    from .switch_profile import SwitchProfileAction
    from .type_text import TypeTextAction
    from .volume_control import VolumeControlAction
    from .window_control import WindowControlAction

    registry = ActionRegistry()
    for action in (
        NoopAction(),
        SwitchPageAction(),
        SwitchProfileAction(),
        NavigateDeckAction(),
        OpenUrlAction(),
        OpenPathAction(),
        RunCommandAction(),
        PowerShellAction(),
        HotkeyAction(),
        TypeTextAction(),
        ClipboardAction(),
        WindowControlAction(),
        MouseControlAction(),
        MediaControlAction(),
        VolumeControlAction(),
        HttpRequestAction(),
        PlaySoundAction(),
        RandomSoundAction(),
        StopSoundAction(),
        DelayAction(),
        MultiAction(),
        SshCommandAction(),
        ObsWebSocketAction(),
    ):
        registry.register(action)
    return registry
