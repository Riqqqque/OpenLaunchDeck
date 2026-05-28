from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ButtonEvent:
    button_id: str
    pressed: bool = True
    source: str = "simulation"
    raw: Any | None = None


class EventBus:
    def __init__(self) -> None:
        self._listeners: dict[str, list[Callable[..., None]]] = defaultdict(list)

    def on(self, event_name: str, callback: Callable[..., None]) -> None:
        self._listeners[event_name].append(callback)

    def emit(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        for callback in list(self._listeners.get(event_name, [])):
            callback(*args, **kwargs)
