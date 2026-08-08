# Using The App

OpenLaunchDeck keeps editing, testing, and live hardware use separate so configuring a pad does not accidentally trigger it.

## Main Window

| Area | Purpose |
| --- | --- |
| Header | Shows the active profile/page, connection state, and shortcuts for reconnect, MIDI Debug, soundboard, and updates |
| Deck Library | Selects profiles and pages; creates, duplicates, deletes, imports, and exports them |
| Launchpad Grid | Displays the active 8x8 page and selects a pad for editing |
| Button Editor | Changes the selected pad's label, color, state, notes, action, and action settings |
| Status Bar | Shows device state, current profile/page, last pad, last result, Simulation mode, and update state |

## Selecting Is Not Running

- Click an on-screen pad to **select** it.
- Press the physical Launchpad pad to **run** it.
- Click **Test Action** to intentionally run the selected button from the editor.

Physical presses and **Test Action** use the same action runner, confirmation rules, result handling, and lighting feedback.

## Button Editor

Every button has:

- ID from `A1` through `H8`
- Label
- Color
- Enabled state
- Dangerous confirmation option
- Notes
- Action type and action-specific settings; fixed option sets use drop-downs
- Optional icon reference
- Optional active, success, and error colors in the profile format

Disabled buttons stay visible in the editor but do not run. Dangerous buttons need a second press within five seconds.

The action picker is searchable and labels actions by purpose, such as Essentials, Windows, Media, Soundboard, Streaming, and Network. The editor shows field guidance and hides settings that do not apply to the current operation. The Hotkey action uses modifier controls plus a searchable key drop-down. Switch Page lists pages in the current profile. Multi-Action uses a step list with Add, Edit, Move, and Remove controls. Names that come from an external system, such as an OBS scene or source, remain text fields because they must match that external application exactly.

### Editor Commands

- **Test Action** runs the selected button.
- **Clear** replaces it with an empty button.
- **Copy** stores its full configuration in the app clipboard.
- **Paste** applies the copied configuration to the selected pad.

## Grid Display

Each pad can show its ID, label, action name, configured color, disabled state, dangerous armed state, and sound-playing state.

Pads remain square and resize as one grid. Choose the largest grid density in Settings:

- **Compact** for smaller windows
- **Comfortable** for normal editing
- **Large** for a bigger second-monitor view

Use **View > Focus Launchpad Grid** to hide the editor and sidebar and give the grid more room. This is an in-app focus view, not exclusive monitor fullscreen.

At narrow window sizes, OpenLaunchDeck shows one workspace at a time instead of squeezing the grid beside the editor. Select a pad, click **Edit A1**, make the change in the full-width editor, then use **Back to Grid**.

### Themes

Open **Settings > Settings > Appearance** to choose:

- **Midnight** for balanced charcoal and teal
- **OLED Black** for true-black displays
- **Galaxy OLED** for black, violet, and cyan
- **Arctic White** for a bright workspace
- **Graphite** for neutral gray and lime
- **Broadcast** for studio charcoal and signal red
- **High Contrast** for maximum control separation

## Profiles And Pages

- A **profile** is a complete deck setup.
- A **page** is one 8x8 layout inside a profile.
- A **button** is one pad configuration on one page.

Changing the active page updates the on-screen grid and refreshes Launchpad lighting. Use a **Switch Page** action on a grid pad for physical page navigation.

See [Profiles, Pages, and Macros](Profiles-Pages-And-Macros.md) for safe organization patterns.

## Menus

### File

- Import Profile
- Export Profile
- Quit

### Edit

- Copy Button Config
- Paste Button Config
- Clear Button

### View

- Focus Launchpad Grid

### Device

- Connect
- Disconnect
- Reconnect
- MIDI Debug

### Profiles

- Profile Manager

### Soundboard

- Browse Sound Library
- Open Soundboard Panel
- Stop All Sounds

### Settings

- Settings

### Help

- Check for Updates
- Open Logs Folder
- Copy Diagnostic Info
- About OpenLaunchDeck

## Soundboard Panel

The Sound Library searches and organizes clips, while the Soundboard panel manages playback and routing. The panel shows active sounds, the selected output route, global volume, and stop controls. Use **Stop All Sounds** when a loop or overlapping clip needs to end immediately.

## System Tray And Background Use

When **Minimize to tray** is enabled, closing the window can keep OpenLaunchDeck running so hardware, sound playback, and microphone routing stay available.

The tray menu can reopen the window, show the current profile/page, reconnect MIDI, stop all sounds, check for updates, or quit.

Use **File > Quit** or the tray **Quit** command when you want the process to stop completely.

## Startup And External Layout Tools

OpenLaunchDeck is single-instance and supports these launch flags:

```text
OpenLaunchDeck.exe --show
OpenLaunchDeck.exe --background
```

- `--show` or `--focus` asks the existing instance to display and restore its window.
- `--background` or `--start-minimized` starts without taking foreground space.

External startup or window-layout utilities should use one of these explicit modes rather than starting multiple independent copies.

## Status Messages

The status bar reports the last action result. A failure there is meant to be actionable; open the logs when more technical detail is needed.

Use **Help > Copy Diagnostic Info** before filing a report. Review the copied text and remove sensitive information.

## Next Pages

- [Actions Reference](Actions-Reference.md)
- [Settings and Data](Settings-And-Data.md)
- [Button Recipes](Button-Recipes.md)
- [Troubleshooting](Troubleshooting.md)
