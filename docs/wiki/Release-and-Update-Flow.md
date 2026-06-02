# Release and Update Flow

OpenLaunchDeck publishes Windows builds through GitHub Releases.

This page explains what users should expect from updates and what maintainers should verify before publishing.

## Install

Use the latest `OpenLaunchDeckSetup-<version>.exe` from GitHub Releases for normal installation.

The installer updates program files. It does not delete user profiles, settings, logs, backups, or MIDI mappings.

User data lives under:

`%APPDATA%\OpenLaunchDeck`

Important user folders:

- `profiles`
- `settings.json`
- `logs`
- `backups`
- `midi_mappings`
- `imported_assets`
- `updates`

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

## Manual Update Path

1. Download the latest installer from GitHub Releases.
2. Close OpenLaunchDeck.
3. Run the installer.
4. Launch OpenLaunchDeck.
5. Confirm your profile is still selected.
6. Test one safe button.

## In-App Update Checks

OpenLaunchDeck can check a JSON update manifest.

The manifest includes:

- Latest version
- Minimum supported version
- Required update flag
- Download URL
- SHA256 checksum
- Release notes URL
- Publish time

The app downloads update installers to AppData, verifies SHA256, and asks before launching the installer. It does not silently install updates.

## Verified OBS Button Pattern

A practical OBS layout is:

- `H7`: OBS replay buffer clip
- `H8`: OBS screenshot

Both use OBS WebSocket instead of keyboard hotkeys.

## Maintainer Release Checklist

Before publishing a release:

1. Run tests.
2. Build the portable ZIP.
3. Build the installer.
4. Install over the previous version.
5. Confirm AppData is preserved.
6. Confirm the app launches.
7. Confirm the Launchpad connects or simulation mode works.
8. Test OBS replay and screenshot actions.
9. Test a soundboard button.
10. Upload installer, ZIP, and checksum files.
11. Update release notes.
12. Update the update manifest if one is being used.
