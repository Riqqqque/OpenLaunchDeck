# Quick Start

This page gets OpenLaunchDeck usable quickly without assuming you already know MIDI, OBS WebSocket, or audio routing.

## 1. Install OpenLaunchDeck

1. Go to the latest GitHub Release.
2. Download `OpenLaunchDeckSetup-<version>.exe`.
3. Run the installer.
4. Launch OpenLaunchDeck from the Start Menu or desktop shortcut.

Use the installer for normal use. The portable ZIP is for testing.

## 2. Understand The Two Modes

OpenLaunchDeck always opens, even without hardware.

- **Connected mode:** a Launchpad Mini MK3 is connected and physical pad presses can run actions.
- **Simulation mode:** no Launchpad MIDI connection is active. You can still edit profiles and test actions from the button editor.

If you see Simulation mode, it usually means the Launchpad is not connected yet, the wrong MIDI port is selected, or the device needs reconnecting.

## 3. Pick A Starter Profile

Starter profiles are ready-made starting points. They avoid private paths, server details, and account-specific secrets.

Good first choices:

- **Basic PC:** browser, copy, paste, media, volume, and common shortcuts.
- **OBS Streaming:** recording, replay, scenes, and source-control examples.
- **Soundboard:** play and stop local sound files.

## 4. Edit A Button

1. Click a pad in the grid.
2. Edit the label, color, enabled state, and action on the right.
3. Choose an action type.
4. Fill in the action fields.
5. Press **Test Action** when you want to run it from the app.

Clicking the grid selects a button for editing. It does not run the action.

## 5. Use The Launchpad

When the Launchpad is connected, pressing a physical pad runs the assigned action.

Recommended first hardware test:

1. Open `Device > MIDI Debug`.
2. Press `A1` on the Launchpad.
3. Confirm a raw MIDI message appears.
4. Confirm the parsed button ID says `A1`.
5. Assign `A1` to a harmless action, such as `No Action` or `Open URL`.

## 6. Make A Safe OBS Clip Button

Use OBS WebSocket instead of a game hotkey for replay buffer clips.

1. Enable OBS WebSocket in OBS.
2. In OpenLaunchDeck, choose a button.
3. Set action type to `OBS WebSocket`.
4. Set operation to `save_replay_buffer`.
5. Enable `Start Replay Buffer If Needed`.
6. Test it while OBS is open.

The first press may start the replay buffer. A later press saves a clip.

## 7. Make A Soundboard Button

1. Choose a pad.
2. Set action type to `Play Sound`.
3. Pick a local `.wav` or `.mp3` file.
4. Start volume around `60` to `80`.
5. Set already-playing behavior:
   - `restart` for short clips
   - `toggle_stop` for long clips
   - `ignore` for one-at-a-time sounds
   - `overlap` for layered effects

To make Discord hear the sound, see [Soundboard And Discord Routing](Soundboard-and-Discord-Routing.md).

## 8. Where Files Live

User files are stored here:

`%APPDATA%\OpenLaunchDeck`

Important folders:

- `profiles`
- `settings.json`
- `logs`
- `backups`
- `midi_mappings`
- `imported_assets`

The installer updates the app. AppData stores your setup.
