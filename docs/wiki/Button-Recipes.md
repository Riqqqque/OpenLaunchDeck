# Button Recipes

This page gives exact button setups for common streaming, gaming, and soundboard actions.

Use these as starting points. After a recipe works, rename the label, change the color, or move it to a different pad.

## Before You Test

Clicking a pad in the app selects it for editing. It does not run the action.

Use **Test Action** in the editor when you want to test from the app. Use the physical Launchpad pad when you want the real macro behavior.

## OBS Replay Clip

Use this for instant replay clips.

- Label: `Clip`
- Color: `purple`
- Action type: `OBS WebSocket`
- Operation: `save_replay_buffer`
- Host: `127.0.0.1`
- Port: `4455`
- Password: your OBS WebSocket password if OBS requires one
- Start Replay Buffer If Needed: on
- Replay Verify Timeout Ms: `10000`
- Timeout Ms: `3000`

Test:

1. Open OBS.
2. Enable replay buffer in OBS settings.
3. Click **Test Action** once.
4. Wait a few seconds.
5. Click **Test Action** again.
6. Confirm a replay file appears in the OBS replay folder.

## OBS Screenshot

Use this for screenshots that still work while a game is focused.

- Label: `Screen`
- Color: `cyan`
- Action type: `OBS WebSocket`
- Operation: `save_screenshot`
- Host: `127.0.0.1`
- Port: `4455`
- Screenshot Source: leave blank
- Screenshot Folder: `%USERPROFILE%\Videos`
- Screenshot Format: `png`
- Timeout Ms: `3000`

Blank Screenshot Source means OBS captures the current program scene.

## Hide Camera In OBS

Use this when you want one button that always hides the camera.

- Label: `Cam Off`
- Color: `red`
- Action type: `OBS WebSocket`
- Operation: `hide_source`
- Scene Name: exact OBS scene name
- Source Name: exact camera source name

Example source names might be `Video Capture Device`, `Facecam`, or `Camera`, but your OBS setup must match exactly.

## Show Camera In OBS

- Label: `Cam On`
- Color: `green`
- Action type: `OBS WebSocket`
- Operation: `show_source`
- Scene Name: exact OBS scene name
- Source Name: exact camera source name

## Toggle Camera In OBS

Use this if you prefer one button instead of separate on/off buttons.

- Label: `Camera`
- Color: `yellow`
- Action type: `OBS WebSocket`
- Operation: `toggle_source`
- Scene Name: exact OBS scene name
- Source Name: exact camera source name

## Toggle OBS Mic Mute

- Label: `Mic`
- Color: `orange`
- Action type: `OBS WebSocket`
- Operation: `toggle_input_mute`
- Input Name: exact OBS audio input name

Common OBS input names include `Mic/Aux`, but copy the real name from the OBS Audio Mixer.

## Discord Mute Hotkey

Use this if Discord is configured with a keyboard shortcut.

- Label: `Mute`
- Color: `orange`
- Action type: `Hotkey`
- Hotkey: the same keybind set in Discord

Recommended key choices:

- `F13`
- `F14`
- `F15`
- `F16`

Extended function keys are useful because most games do not use them by default.

## Discord Deafen Hotkey

- Label: `Deafen`
- Color: `blue`
- Action type: `Hotkey`
- Hotkey: the same keybind set in Discord

Use a different extended function key than the mute button.

## Play A Soundboard Clip Locally

- Label: short clip name
- Color: `purple`
- Action type: `Play Sound`
- File Path: choose a local `.wav` or `.mp3`
- Volume: start at `60`
- Loop: off
- Already Playing: `restart`
- Route To Voice Chat: off

If you do not hear it locally, fix local playback before changing Discord settings.

## Play A Soundboard Clip In Discord

First make local playback work. Then use:

- Action type: `Play Sound`
- Route To Voice Chat: on
- Volume: start at `50` to `70`
- Already Playing: `restart`

Then set Discord input to the route recording device. See [Soundboard And Discord Routing](Soundboard-and-Discord-Routing.md) for the full checklist.

## Stop All Sounds

Always keep one of these near soundboard buttons.

- Label: `Stop`
- Color: `red`
- Action type: `Stop Sound`
- Scope: `all`

## Switch Page

Use this for page navigation on the 8x8 grid.

- Label: `Next`
- Color: `blue`
- Action type: `Switch Page`
- Target Page: the page you want to open

The Launchpad Mini MK3 has extra buttons around the grid, but OpenLaunchDeck uses the 8x8 grid as the reliable macro surface unless extra button mappings are verified in MIDI Debug.

## Open A Website

- Label: `Dash`
- Color: `green`
- Action type: `Open URL`
- URL: the site you want to open

Example:

```text
https://dashboard.twitch.tv
```

## Open A Folder Or App

- Label: `Folder`
- Color: `blue`
- Action type: `Open Path`
- Path: a folder, file, or app path

Examples:

```text
%USERPROFILE%\Videos
C:\Program Files\obs-studio\bin\64bit\obs64.exe
```

## Run A Local Command

Only use command buttons when you understand what the command does.

- Label: short command name
- Color: `yellow`
- Action type: `Run Command`
- Command: command to run
- Wait For Completion: off for long-running commands
- Dangerous: on if the command stops, deletes, restarts, or changes something important

Dangerous buttons require a second press inside the arm window.

## Good First Layout

A simple first streaming page:

```text
A1 Clip       A2 Screen     A3 Camera    A4 Mic
A5 Sound 1    A6 Sound 2    A7 Stop      A8 Next
```

Keep the first page simple. Move advanced commands to page 2 after the basics work.
