# OpenLaunchDeck Wiki

OpenLaunchDeck turns a Novation Launchpad Mini MK3 into a Windows macro deck for streaming, gaming, OBS control, soundboard playback, and everyday shortcuts.

This wiki is written for people who want a working setup first and technical details second. Start at the top, follow the checklists, and only jump deeper when something needs tuning.

## Fast Path

If you just installed the app, do these in order:

1. Install OpenLaunchDeck from the latest GitHub Release.
2. Launch the app.
3. Plug in the Launchpad Mini MK3.
4. If the header says Simulation mode, press Reconnect.
5. Pick the Basic PC, OBS Streaming, or Soundboard starter profile.
6. Click a grid pad to edit it.
7. Use Test Action in the editor to test from the app.
8. Press the physical Launchpad pad to use it for real.

Clicking a pad in the app only selects it for editing. It does not run the action.

## Start Here

- [Quick Start](Quick-Start.md) - install, launch, pick a profile, and make the first useful buttons.
- [Launchpad Mini MK3 Setup](Launchpad-Mini-MK3-Setup.md) - USB MIDI, Programmer Mode, mapping checks, lighting, and calibration.
- [Profiles, Pages, And Macros](Profiles-Pages-And-Macros.md) - profiles, pages, buttons, colors, dangerous buttons, and page switching.
- [Button Recipes](Button-Recipes.md) - exact settings for common OBS, voice chat, soundboard, and utility buttons.
- [OBS WebSocket Setup](OBS-WebSocket-Setup.md) - replay buffer clips, screenshots, scene switching, source visibility, and mute controls.
- [Streaming Safety](Streaming-Safety.md) - prevent accidental stream starts and audit OBS stream controls.
- [Soundboard And Voice Chat Routing](Soundboard-and-Discord-Routing.md) - local playback, Discord/game chat routing, mic mix, sound quality, and common fixes.
- [Performance And Gaming](Performance-And-Gaming.md) - keep the app light while gaming, streaming, and recording.
- [Troubleshooting](Troubleshooting.md) - quick fixes for Launchpad, OBS, soundboard, Discord, hotkeys, startup, and updates.
- [Release And Update Flow](Release-and-Update-Flow.md) - installs, updates, checksums, and preserved user data.

## What You Can Do In The Current Release

- Use the app without hardware in Simulation mode.
- Edit an 8x8 Launchpad-style grid.
- Connect a Launchpad Mini MK3 through USB MIDI.
- Run actions from physical pad presses.
- Light pads with configured colors and feedback states.
- Create profiles and pages.
- Use OBS WebSocket for clips, screenshots, scenes, source visibility, and mute controls.
- Require confirmation before OBS start-stream actions run.
- Play local `.wav` and `.mp3` soundboard clips.
- Route selected soundboard clips toward Discord or in-game voice chat through a Windows recording route.
- Use hotkeys, including `F13` through `F24`.
- Check for updates with checksum verification.

## What OpenLaunchDeck Does Not Do By Itself

- It does not install audio drivers for you.
- It does not make voice chat hear soundboard audio unless that app or game is set to the correct input.
- It does not bind Launchpad side buttons to page navigation by default.
- It does not silently update itself.
- It does not store your user data in the install folder.

## Important Folder

Your profiles, settings, backups, logs, MIDI mappings, and imported assets are stored here:

```text
%APPDATA%\OpenLaunchDeck
```

Installer updates replace program files. They should not delete that AppData folder.
