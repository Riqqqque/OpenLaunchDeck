from __future__ import annotations


class StartupService:
    def is_available(self) -> bool:
        return False

    def set_enabled(self, enabled: bool) -> bool:
        return False
