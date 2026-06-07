# OpenLaunchDeck Wiki

Welcome to the OpenLaunchDeck wiki.

OpenLaunchDeck turns a Novation Launchpad Mini MK3 into a Windows macro deck for streaming, gaming, OBS control, soundboard playback, and everyday shortcuts.

This wiki is written for two groups at the same time:

- New users who want to plug in the Launchpad and make useful buttons.
- Contributors who want to understand how the app is supposed to work before changing it.

If you are new, start with Quick Start. If something goes wrong, jump to Troubleshooting.

## Start Here

- [Quick Start](Quick-Start.md) - install, launch, pick a profile, and make your first button.
- [Launchpad Mini MK3 Setup](Launchpad-Mini-MK3-Setup.md) - USB MIDI connection, Programmer Mode, mapping checks, lighting, and calibration.
- [Profiles, Pages, And Macros](Profiles-Pages-And-Macros.md) - how profiles, pages, buttons, and actions fit together.
- [OBS WebSocket Setup](OBS-WebSocket-Setup.md) - replay buffer clips, screenshots, scene switching, and source toggles.
- [Soundboard And Discord Routing](Soundboard-and-Discord-Routing.md) - local sounds, simple voice routing, duplicate output names, and quality fixes.
- [Performance And Gaming](Performance-And-Gaming.md) - keep the app light while gaming or streaming.
- [Troubleshooting](Troubleshooting.md) - common fixes for device, OBS, hotkey, update, and soundboard issues.
- [Release And Update Flow](Release-and-Update-Flow.md) - install, update, checksums, and preserved user data.

## Release Assets

Release assets include:

- `OpenLaunchDeckSetup-<version>.exe`
- `OpenLaunchDeckSetup-<version>.exe.sha256`
- `OpenLaunchDeck-<version>-Windows.zip`
- `OpenLaunchDeck-<version>-Windows.zip.sha256`

Install the setup EXE for normal use. The portable ZIP is useful for testing without replacing the installed copy.

## What Works In The Current Release

- Installable Windows desktop app.
- 8x8 editable Launchpad grid.
- Simulation mode when no Launchpad is connected.
- Physical Launchpad Mini MK3 pad presses when MIDI ports are connected and mapped.
- RGB lighting structure with page refresh and feedback states.
- Profiles and pages stored in AppData.
- Soundboard playback for local `.wav` and `.mp3` files.
- Voice-chat soundboard routing with OpenLaunchDeck's simple route controls.
- OBS WebSocket actions for recording, streaming, replay buffer clips, screenshots, scene switching, and input mute toggles.
- Hotkey actions, including extended function keys such as `F13` through `F24`.
- Manual update checks with checksum verification.

## Known Limits

- OpenLaunchDeck does not install audio drivers. Voice-chat routing needs a Windows recording endpoint that receives the routed soundboard playback.
- The Launchpad Mini MK3 8x8 grid is the supported macro surface. Extra hardware navigation buttons can be inspected in MIDI Debug, but they are not bound to previous/next app pages by default.
- OBS actions need OBS running with WebSocket enabled.
- Some games block normal keyboard automation. Use OBS WebSocket for clips/screenshots when possible.

## User Data Location

OpenLaunchDeck keeps user data outside the install folder:

`%APPDATA%\OpenLaunchDeck`

That folder contains settings, profiles, backups, logs, MIDI mappings, and imported assets.

Program upgrades replace files under Program Files. They should not delete user data.
