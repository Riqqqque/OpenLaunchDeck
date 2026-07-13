from __future__ import annotations

from datetime import datetime
import shutil

from ..config_store import read_json, write_json
from ..models.settings import Settings
from ..paths import BACKUPS_DIR, SETTINGS_FILE, ensure_user_dirs


class SettingsService:
    def __init__(self) -> None:
        ensure_user_dirs()
        self.load_warning = ""
        try:
            data = read_json(SETTINGS_FILE, {})
        except (OSError, UnicodeError, ValueError) as exc:
            backup_path = self._backup_corrupt_settings()
            backup_text = f" A copy was kept at {backup_path}." if backup_path else ""
            self.load_warning = f"Settings could not be read and defaults were loaded.{backup_text} Error: {exc}"
            data = {}
            if backup_path:
                write_json(SETTINGS_FILE, Settings().to_dict())
        self.settings = Settings.from_dict(data)

    def save(self) -> None:
        write_json(SETTINGS_FILE, self.settings.to_dict())

    def update(self, **changes) -> Settings:
        for key, value in changes.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
        self.settings = Settings.from_dict(self.settings.to_dict())
        self.save()
        return self.settings

    @staticmethod
    def _backup_corrupt_settings():
        if not SETTINGS_FILE.exists():
            return None
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        backup_path = BACKUPS_DIR / f"settings-corrupt-{stamp}.json"
        try:
            shutil.copy2(SETTINGS_FILE, backup_path)
        except OSError:
            return None
        return backup_path
