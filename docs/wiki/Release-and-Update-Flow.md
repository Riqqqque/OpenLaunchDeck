# Release and Update Flow

OpenLaunchDeck publishes Windows builds through GitHub Releases.

## Install

Use the latest `OpenLaunchDeckSetup-<version>.exe` from GitHub Releases for normal installation.

The installer updates program files. It does not delete user profiles, settings, logs, backups, or MIDI mappings.

User data lives under:

`%APPDATA%\OpenLaunchDeck`

## Release Assets

Each release should include:

- Installer EXE
- Installer SHA256 checksum
- Portable Windows ZIP
- Portable ZIP SHA256 checksum

## Updating

Normal updates replace the installed app files. User data stays in AppData.

Before testing an update, verify:

- Existing profiles still load
- Settings still load
- Launchpad still connects
- OBS clip and screenshot actions still work
- Soundboard output still works

## Verified OBS Button Pattern

A practical OBS layout is:

- `H7`: OBS replay buffer clip
- `H8`: OBS screenshot

Both use OBS WebSocket instead of keyboard hotkeys.
