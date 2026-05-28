from pathlib import Path

from openlaunchdeck.paths import APP_DATA_DIR, BACKUPS_DIR, LOGS_DIR, MIDI_MAPPINGS_DIR, PROFILES_DIR, SETTINGS_FILE
from openlaunchdeck.version import APP_NAME


def test_user_data_paths_are_outside_repository():
    repo_root = Path.cwd().resolve()

    for path in [APP_DATA_DIR, SETTINGS_FILE, PROFILES_DIR, LOGS_DIR, BACKUPS_DIR, MIDI_MAPPINGS_DIR]:
        resolved = path.resolve()
        assert APP_NAME in resolved.parts
        assert not resolved.is_relative_to(repo_root)
