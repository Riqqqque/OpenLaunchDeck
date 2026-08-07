# Quick Start

This guide gets OpenLaunchDeck installed, explains Simulation mode, creates one safe button, and verifies the Launchpad connection.

## Before You Start

You need:

- Windows 11
- The latest OpenLaunchDeck installer
- A Novation Launchpad Mini MK3 and USB cable for physical use

The Launchpad is optional while you learn the app. Simulation mode is a normal editing mode, not an error.

## 1. Install OpenLaunchDeck

1. Open the [latest release](https://github.com/Riqqqque/OpenLaunchDeck/releases/latest).
2. Download `OpenLaunchDeckSetup-<version>.exe`.
3. Run the installer.
4. Open OpenLaunchDeck from the Start menu or desktop shortcut.

Windows may show a publisher warning because the installer is currently unsigned. Confirm that the file came from the official repository and use the provided SHA256 file when you need to verify it manually.

## 2. Choose A Starter Profile

On first launch, choose a starter profile:

- **Blank** for an empty deck
- **Basic PC** for common Windows shortcuts
- **OBS Streaming** for streaming examples
- **Discord Audio** for voice-chat hotkey examples
- **Soundboard** for audio button examples

Starter buttons are examples. Replace paths, URLs, names, hotkeys, and sound files with your own values before relying on them.

## 3. Understand Simulation Mode

Simulation mode appears when OpenLaunchDeck does not have an active Launchpad MIDI input and output connection.

You can still:

- Edit every pad
- Create profiles and pages
- Import and export profiles
- Use **Test Action**
- Configure settings
- Open MIDI Debug

Hover over the Simulation mode label to see why the app entered that mode.

## 4. Select And Edit A Button

1. Click pad `A1` in the on-screen grid.
2. Edit the label, color, enabled state, notes, and action in the right panel.
3. Choose an action type.
4. Fill in the action fields.
5. Wait briefly for autosave, or switch away from the field to commit the edit.

Clicking the grid only selects a pad. It never runs the action.

Use these editor controls deliberately:

- **Test Action** runs the selected button through the same action runner used by hardware.
- **Clear** resets the selected button.
- **Copy** copies the full button configuration.
- **Paste** replaces the selected button with the copied configuration.

## 5. Make A Safe First Button

Create a website button:

1. Select `A1`.
2. Set **Label** to `Website`.
3. Set **Color** to `green`.
4. Choose **Open URL**.
5. Enter `https://www.google.com`.
6. Leave **Open In Private Window** off for the first test.
7. Click **Test Action**.

If the browser opens, profile editing and action execution are working.

## 6. Connect The Launchpad

1. Connect the Launchpad directly to USB.
2. Put it in Programmer Mode when practical.
3. Click **Reconnect** in OpenLaunchDeck.
4. Open **Device > MIDI Debug**.
5. Confirm an input and output containing `LPMiniMK3 MIDI` are selected.
6. Press physical pad `A1`.

The on-screen `A1` pad should react and its configured action should run. If a different cell reacts, use calibration instead of manually changing scattered note values.

Windows can expose more than one Launchpad interface. OpenLaunchDeck normally prefers the second MIDI interface used for programmer control. See [Launchpad Mini MK3 Setup](Launchpad-Mini-MK3-Setup.md) if the wrong interface opens.

## 7. Add Your First Real Controls

Good next buttons are:

- A harmless hotkey such as `ctrl+c`
- **Media Control > Play/Pause**
- **Switch Page**
- **Stop Sound > all**
- An OBS screenshot after OBS WebSocket is configured

Use [Button Recipes](Button-Recipes.md) for exact field values and [Actions Reference](Actions-Reference.md) for every available action.

For sound effects, open [Sound Library](Sound-Library.md) to search, preview, import, and assign clips from inside the app.

## 8. Make It Start With Windows

Open **Settings > Settings** and enable:

- **Launch at startup** to start after Windows sign-in
- **Start minimized** if the normal app launch should begin hidden
- **Minimize to tray** to keep the Launchpad and audio routes active when the window closes

OpenLaunchDeck is single-instance. If Windows Startup and another layout utility both launch it, the second launch hands off to the existing instance and exits.

## Where Your Setup Lives

```text
%APPDATA%\OpenLaunchDeck
```

Open **Settings > Settings > Config folder** to open it. Back up this folder before major manual changes.

## Next Steps

- [Using the App](Using-The-App.md)
- [Launchpad Mini MK3 Setup](Launchpad-Mini-MK3-Setup.md)
- [Profiles, Pages, and Macros](Profiles-Pages-And-Macros.md)
- [OBS WebSocket Setup](OBS-WebSocket-Setup.md)
- [Sound Library](Sound-Library.md)
- [Soundboard and Voice Chat](Soundboard-and-Discord-Routing.md)
