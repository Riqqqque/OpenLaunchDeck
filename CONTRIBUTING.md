# Contributing

Thanks for helping improve OpenLaunchDeck. Small, focused changes are easier to review and safer to release.

## Before You Start

- Search existing issues and pull requests.
- Open an issue before a large behavior or architecture change.
- Keep hardware assumptions isolated and testable.
- Never include personal paths, credentials, tokens, private server details, or exported profiles containing secrets.

## Development Setup

Open PowerShell in the repository root:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pytest
python -m openlaunchdeck.main
```

Python 3.11 through 3.13 is recommended for Windows MIDI development.

## Project Map

| Path | Responsibility |
| --- | --- |
| `openlaunchdeck/actions` | Action implementations and registration |
| `openlaunchdeck/audio` | Sound playback, output devices, and voice routing |
| `openlaunchdeck/devices` | MIDI transport, Launchpad behavior, mapping, and calibration |
| `openlaunchdeck/models` | Saved profile, page, button, settings, and update data |
| `openlaunchdeck/services` | Profiles, actions, lighting, updates, startup, backups, and performance |
| `openlaunchdeck/ui` | PySide6 windows, dialogs, grid, editors, theme, and tray |
| `openlaunchdeck/resources` | Icons, themes, and starter profiles |
| `docs/wiki` | Source of truth for the public user wiki |
| `tests` | Hardware-free automated tests |

## Engineering Rules

- Keep Launchpad note/control mappings in `openlaunchdeck/devices/midi_mapping.py`.
- Do minimal work in MIDI callbacks and send UI changes through Qt signals.
- Run commands, network work, updates, and other blocking actions off the GUI thread.
- Keep user data under `%APPDATA%\OpenLaunchDeck`, never beside installed program files.
- Return clear `ActionResult` values from every action.
- Use timeouts for network, OBS, SSH, and waited command operations.
- Preserve the Python fallback when changing optional native helpers.
- Add focused tests for changed behavior and failure paths.
- Keep documentation accurate about hardware verification and external requirements.

## Documentation

Edit user-facing wiki pages in `docs/wiki`. Do not edit the live wiki first.

Validate the pages and sync them to a local wiki clone with:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\sync-wiki.ps1 -WikiPath <wiki-clone-path>
```

The sync script publishes user pages, removes stale wiki pages, and converts repository `.md` links into rendered GitHub Wiki links.

## Before A Pull Request

Run:

```powershell
pytest
powershell -ExecutionPolicy Bypass -File build.ps1 -SkipInstaller
```

Then confirm:

- The app starts with `python -m openlaunchdeck.main`.
- Simulation mode works without a Launchpad.
- No unrelated files are included.
- New settings and profile fields load old files safely.
- Documentation links resolve.

For MIDI changes, include the Launchpad mode, selected ports, raw messages, and hardware result. For updater or installer changes, confirm AppData survives an upgrade. For release work, follow [docs/release_checklist.md](docs/release_checklist.md).

## Pull Requests

Describe the user-facing problem, the implementation, and exactly how it was tested. Screenshots are useful for visible UI changes. Keep each pull request focused on one problem.
