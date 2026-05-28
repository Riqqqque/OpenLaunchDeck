# Contributing

Thanks for helping improve OpenLaunchDeck.

## Development Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pytest
python -m openlaunchdeck.main
```

## Code Style

- Keep device mappings inside `openlaunchdeck/devices/midi_mapping.py`.
- Keep user data out of the install folder.
- Use services for shared app behavior instead of adding global state.
- Return clear `ActionResult` values from actions.
- Do not block the Qt GUI thread with network calls, commands, audio work, or MIDI callbacks.
- Add tests for model, action, update, or service behavior when changing those areas.
- Keep documentation honest about unfinished integrations.
- Do not commit machine-specific paths, real network addresses, secrets, credentials, tokens, or personal account details.

## Pull Requests

Before opening a pull request:

```powershell
pytest
powershell -ExecutionPolicy Bypass -File build.ps1 -SkipInstaller
```

For MIDI changes, include the Launchpad mode used during testing and a short note about raw messages observed in the MIDI debug window.

For release changes, also review `docs/release_checklist.md`, validate the update manifest flow, and confirm user data stays under `%APPDATA%\OpenLaunchDeck`.
