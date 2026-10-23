from __future__ import annotations

import shutil
from datetime import datetime

from ..paths import BACKUPS_DIR, PROFILES_DIR


# Automatic backups are made before each update; keep the newest ones only.
KEEP_AUTOMATIC_BACKUPS = 20


class BackupService:
    def backup_profiles(self) -> str:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        target = BACKUPS_DIR / f"profiles-{stamp}"
        target.mkdir(parents=True, exist_ok=True)
        for profile in PROFILES_DIR.glob("*.json"):
            shutil.copy2(profile, target / profile.name)
        self.prune_automatic_backups()
        return str(target)

    @staticmethod
    def prune_automatic_backups(keep: int = KEEP_AUTOMATIC_BACKUPS) -> list[str]:
        """Delete the oldest automatic profile backups beyond `keep`. Other backups are left alone."""
        automatic = sorted(path for path in BACKUPS_DIR.glob("profiles-*") if path.is_dir())
        removed = []
        for old in automatic[: max(0, len(automatic) - keep)]:
            shutil.rmtree(old, ignore_errors=True)
            removed.append(old.name)
        return removed
