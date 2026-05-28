from __future__ import annotations

import shutil
from datetime import datetime

from ..paths import BACKUPS_DIR, PROFILES_DIR


class BackupService:
    def backup_profiles(self) -> str:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        target = BACKUPS_DIR / f"profiles-{stamp}"
        target.mkdir(parents=True, exist_ok=True)
        for profile in PROFILES_DIR.glob("*.json"):
            shutil.copy2(profile, target / profile.name)
        return str(target)
