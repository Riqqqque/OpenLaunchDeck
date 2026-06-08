from __future__ import annotations

import time
from dataclasses import dataclass

from ..constants import DEFAULT_DANGEROUS_ARM_SECONDS, DEFAULT_DANGEROUS_CONFIRM_DELAY_SECONDS


@dataclass(slots=True)
class ArmedButton:
    button_id: str
    armed_at: float
    expires_at: float


class DangerousConfirmService:
    def __init__(
        self,
        arm_seconds: float = DEFAULT_DANGEROUS_ARM_SECONDS,
        confirm_delay_seconds: float = DEFAULT_DANGEROUS_CONFIRM_DELAY_SECONDS,
    ) -> None:
        self.arm_seconds = arm_seconds
        self.confirm_delay_seconds = max(0.0, confirm_delay_seconds)
        self._armed: dict[str, ArmedButton] = {}

    def arm_or_confirm(self, button_id: str) -> bool:
        self.prune()
        now = time.monotonic()
        armed = self._armed.get(button_id)
        if armed and armed.expires_at >= now:
            if now - armed.armed_at >= self.confirm_delay_seconds:
                self._armed.pop(button_id, None)
                return True
            return False
        self._armed[button_id] = ArmedButton(button_id, now, now + self.arm_seconds)
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
