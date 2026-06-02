# OpenLaunchDeck Wiki

OpenLaunchDeck turns a Novation Launchpad Mini MK3 into a Windows macro deck for streaming, gaming, soundboard playback, OBS control, and everyday shortcuts.

## Start Here

- [OBS WebSocket Setup](OBS-WebSocket-Setup.md) - clip replay buffer, save screenshots, switch scenes, and toggle sources.
- [Launchpad Mini MK3 Setup](Launchpad-Mini-MK3-Setup.md) - USB MIDI connection, Programmer Mode, mapping checks, and calibration.
- [Soundboard and Discord Routing](Soundboard-and-Discord-Routing.md) - play local sounds and route them through Discord with external audio routing software.
- [Release and Update Flow](Release-and-Update-Flow.md) - install, update, and preserve user data.

## Current Release

Latest verified release: `v0.1.28`

Release assets include:

- `OpenLaunchDeckSetup-0.1.28.exe`
- `OpenLaunchDeckSetup-0.1.28.exe.sha256`
- `OpenLaunchDeck-0.1.28-Windows.zip`
- `OpenLaunchDeck-0.1.28-Windows.zip.sha256`

Install the setup EXE for normal use. The portable ZIP is useful for testing without replacing the installed copy.

## User Data Location

OpenLaunchDeck keeps user data outside the install folder:

`%APPDATA%\OpenLaunchDeck`

That folder contains settings, profiles, backups, logs, MIDI mappings, and imported assets.
