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


def create_default_registry() -> ActionRegistry:
    from .delay import DelayAction
    from .hotkey import HotkeyAction
    from .http_request import HttpRequestAction
    from .media_control import MediaControlAction
    from .multi_action import MultiAction
    from .noop import NoopAction
    from .obs_websocket import ObsWebSocketAction
    from .open_path import OpenPathAction
    from .open_url import OpenUrlAction
    from .play_sound import PlaySoundAction
    from .powershell import PowerShellAction
    from .run_command import RunCommandAction
    from .ssh_command import SshCommandAction
    from .stop_sound import StopSoundAction
    from .switch_page import SwitchPageAction
    from .type_text import TypeTextAction
    from .volume_control import VolumeControlAction

    registry = ActionRegistry()
    for action in (
        NoopAction(),
        SwitchPageAction(),
        OpenUrlAction(),
        OpenPathAction(),
        RunCommandAction(),
        PowerShellAction(),
        HotkeyAction(),
        TypeTextAction(),
        MediaControlAction(),
        VolumeControlAction(),
        HttpRequestAction(),
        PlaySoundAction(),
        StopSoundAction(),
        DelayAction(),
        MultiAction(),
        SshCommandAction(),
        ObsWebSocketAction(),
    ):
        registry.register(action)
    return registry
