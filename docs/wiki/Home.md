# OpenLaunchDeck Wiki

OpenLaunchDeck turns a **Novation Launchpad Mini MK3** into a 64-pad Windows macro deck. Use it for OBS, soundboard clips, voice chat, hotkeys, media controls, apps, websites, commands, and multi-step workflows.

This wiki is organized around tasks. Start with the short setup, then open only the guide for the feature you are configuring.

## New Here?

1. [Download the latest installer](https://github.com/Riqqqque/OpenLaunchDeck/releases/latest).
2. Follow the [Quick Start](Quick-Start.md).
3. Use [Button Recipes](Button-Recipes.md) when you are ready to add useful controls.

The app works without hardware in **Simulation mode**. Clicking a grid pad selects it for editing; it does not run the action. Use **Test Action** when you intentionally want to test from the app.

## Find The Right Guide

| I want to... | Open this page |
| --- | --- |
| Install the app and make my first button | [Quick Start](Quick-Start.md) |
| Understand every part of the window | [Using the App](Using-The-App.md) |
| Connect, calibrate, or debug the Launchpad | [Launchpad Mini MK3 Setup](Launchpad-Mini-MK3-Setup.md) |
| Create profiles and pages | [Profiles, Pages, and Macros](Profiles-Pages-And-Macros.md) |
| Learn what every action does | [Actions Reference](Actions-Reference.md) |
| Copy a proven button setup | [Button Recipes](Button-Recipes.md) |
| Save clips, take screenshots, or control OBS | [OBS WebSocket Setup](OBS-WebSocket-Setup.md) |
| Play sounds locally or into voice chat | [Soundboard and Voice Chat](Soundboard-and-Discord-Routing.md) |
| Prevent accidental live actions | [Streaming Safety](Streaming-Safety.md) |
| Keep the app light while gaming | [Performance and Gaming](Performance-And-Gaming.md) |
| Find a setting, folder, log, or backup | [Settings and Data](Settings-And-Data.md) |
| Fix something that is not working | [Troubleshooting](Troubleshooting.md) |
| Install or publish an update | [Release and Update Flow](Release-and-Update-Flow.md) |

## What Works

- 8x8 editable grid with labels, colors, and action status
- Multiple profiles and pages
- Physical Launchpad pad presses and RGB feedback
- MIDI auto-detection, manual connection, live debug, and calibration
- Hotkeys, media keys, typed text, websites, apps, files, folders, and commands
- OBS replay clips, screenshots, recording, scenes, sources, and mute controls
- Local soundboard playback and optional voice-route playback
- HTTP requests, key-based SSH commands, delays, and action sequences
- Dangerous-action double-press confirmation
- System tray, startup launch, profile backups, logs, and checksum-verified updates

See [Actions Reference](Actions-Reference.md) for the complete list and required fields.

## Connection Status

The header tells you which mode the app is using:

- **Connected** means the selected MIDI input and output ports are open.
- **Simulation mode** means no usable Launchpad connection is active. Editing and **Test Action** still work.
- **Reconnect** asks the app to scan and open the configured or likely Launchpad ports again.

If the app says Connected but pads do nothing, open [Launchpad Mini MK3 Setup](Launchpad-Mini-MK3-Setup.md) and verify the selected Windows MIDI interface.

## Important Limitations

- The 8x8 grid is the verified macro surface. Extra side/navigation buttons are not page controls by default.
- Programmer Mode is recommended, but mappings should still be checked with MIDI Debug on real hardware.
- Voice-chat soundboard routing requires a compatible Windows audio route and the matching input selected in the chat application. No audio driver is bundled.
- OBS controls require OBS WebSocket to be enabled.
- Updates are never installed silently.
- The current installer is unsigned, so Windows may show a publisher warning.

## Your Data

Profiles, settings, backups, logs, MIDI mappings, imported assets, and downloaded updates are stored in:

```text
%APPDATA%\OpenLaunchDeck
```

Updating or reinstalling the app replaces program files, not this folder.

## Need Help?

1. Check [Troubleshooting](Troubleshooting.md).
2. Open **Help > Copy Diagnostic Info** in the app.
3. Remove passwords, tokens, and private paths.
4. Open a [bug report](https://github.com/Riqqqque/OpenLaunchDeck/issues/new/choose) with exact reproduction steps.
