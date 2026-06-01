# Changelog

## 0.1.2

- Fixed installer shortcut icon metadata for Start Menu and Desktop shortcuts.
- Ensured installer-created shortcuts use the OpenLaunchDeck executable icon explicitly.

## 0.1.1

- Added OpenLaunchDeck logo and Windows icon assets.
- Wired the icon into the desktop window, system tray, PyInstaller executable, and installer.
- Added release support documents and dependency update checks for repository maintenance.
- Updated package metadata so icon assets are included with the application.

## 0.1.0

- Initial public MVP application structure.
- Added PySide6 desktop UI with editable 8x8 grid and button editor.
- Added profile/page models, JSON load/save, starter profiles, and AppData storage.
- Added simulation mode and action runner.
- Added core actions for URLs, paths, commands, hotkeys, delays, multi-actions, and soundboard playback.
- Added MIDI manager, Launchpad Mini MK3 device wrapper, mapping isolation, debug window, and calibration structure.
- Added page lighting refresh, changed-pad batching, press/success/error flashes, armed warning blink, and sound-playing state.
- Added soundboard panel, local file checks, per-sound volume, global volume, loop behavior, and stop controls.
- Added update manifest parsing, version comparison, download, checksum verification, and installer launch confirmation.
- Added performance timing helpers and optional native mapping/hash/checksum helper with Python fallback.
- Added build script, PyInstaller spec, installer script, docs, and tests.
