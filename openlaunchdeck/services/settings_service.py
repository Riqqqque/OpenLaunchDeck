from __future__ import annotations

from ..config_store import read_json, write_json
from ..models.settings import Settings
from ..paths import SETTINGS_FILE, ensure_user_dirs


class SettingsService:
    def __init__(self) -> None:
        ensure_user_dirs()
        self.settings = Settings.from_dict(read_json(SETTINGS_FILE, {}))

    def save(self) -> None:
        write_json(SETTINGS_FILE, self.settings.to_dict())

    def update(self, **changes) -> Settings:
        for key, value in changes.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
        self.settings = Settings.from_dict(self.settings.to_dict())
        self.save()
        return self.settings
