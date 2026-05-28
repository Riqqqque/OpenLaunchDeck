from __future__ import annotations

import time
from dataclasses import dataclass

from ..constants import DEFAULT_DANGEROUS_ARM_SECONDS


@dataclass(slots=True)
class ArmedButton:
    button_id: str
    expires_at: float


class DangerousConfirmService:
    def __init__(self, arm_seconds: float = DEFAULT_DANGEROUS_ARM_SECONDS) -> None:
        self.arm_seconds = arm_seconds
        self._armed: dict[str, ArmedButton] = {}

    def arm_or_confirm(self, button_id: str) -> bool:
        self.prune()
        armed = self._armed.get(button_id)
        if armed and armed.expires_at >= time.monotonic():
            self._armed.pop(button_id, None)
            return True
        self._armed[button_id] = ArmedButton(button_id, time.monotonic() + self.arm_seconds)
        return False

    def is_armed(self, button_id: str) -> bool:
        self.prune()
        return button_id in self._armed

    def disarm(self, button_id: str) -> None:
        self._armed.pop(button_id, None)

    def disarm_all(self) -> None:
        self._armed.clear()

    def prune(self) -> None:
        now = time.monotonic()
        expired = [button_id for button_id, armed in self._armed.items() if armed.expires_at < now]
        for button_id in expired:
            self._armed.pop(button_id, None)
