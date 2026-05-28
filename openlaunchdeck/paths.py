from __future__ import annotations

import os
import sys
from pathlib import Path

from .version import APP_NAME


def _base_app_data() -> Path:
    if sys.platform == "win32":
        root = os.environ.get("APPDATA")
        if root:
            return Path(root) / APP_NAME
    return Path.home() / f".{APP_NAME.lower()}"


APP_DATA_DIR = _base_app_data()
SETTINGS_FILE = APP_DATA_DIR / "settings.json"
PROFILES_DIR = APP_DATA_DIR / "profiles"
LOGS_DIR = APP_DATA_DIR / "logs"
BACKUPS_DIR = APP_DATA_DIR / "backups"
MIDI_MAPPINGS_DIR = APP_DATA_DIR / "midi_mappings"
IMPORTED_ASSETS_DIR = APP_DATA_DIR / "imported_assets"
UPDATES_DIR = APP_DATA_DIR / "updates"

PACKAGE_DIR = Path(__file__).resolve().parent
RESOURCES_DIR = PACKAGE_DIR / "resources"
STARTER_PROFILES_DIR = RESOURCES_DIR / "starter_profiles"
THEMES_DIR = RESOURCES_DIR / "themes"


def ensure_user_dirs() -> None:
    for path in (
        APP_DATA_DIR,
        PROFILES_DIR,
        LOGS_DIR,
        BACKUPS_DIR,
        MIDI_MAPPINGS_DIR,
        IMPORTED_ASSETS_DIR,
        UPDATES_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)


def open_folder_path(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
