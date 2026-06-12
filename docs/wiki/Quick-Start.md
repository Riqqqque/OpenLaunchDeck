# Quick Start

This page gets OpenLaunchDeck usable quickly. Follow it in order the first time.

## Before You Start

You need:

- Windows 10 or Windows 11.
- OpenLaunchDeck installed from GitHub Releases.
- A Novation Launchpad Mini MK3 if you want physical pad control.
- OBS only if you want streaming, clipping, screenshots, or scene controls.
- A voice chat route only if you want Discord or game chat to hear soundboard clips.
- Local `.wav` or `.mp3` files if you want soundboard buttons.

You can still use the app before the Launchpad arrives. That is what Simulation mode is for.

## 1. Install OpenLaunchDeck

1. Open the latest GitHub Release.
2. Download `OpenLaunchDeckSetup-<version>.exe`.
3. Run the installer.
4. Launch OpenLaunchDeck from the Start Menu or desktop shortcut.

Use the installer for normal use. Use the portable ZIP only when you want to test without replacing the installed copy.

## 2. Know What The Header Means

The top of the app shows the current device state.

- **Connected mode:** OpenLaunchDeck sees the Launchpad MIDI ports. Physical pad presses can run actions.
- **Simulation mode:** no active Launchpad MIDI connection is available. The app still works for editing, profile setup, and Test Action.

Simulation mode is not a crash and not a bad install. It means one of these is true:

- The Launchpad is not plugged in.
- The wrong MIDI port is selected.
- Another app has the MIDI port open.
- The device needs reconnecting.

## 3. Pick A Starter Profile

Open the profile selector on the left and choose one:

- **Basic PC:** browser, copy, paste, media, volume, and common shortcuts.
- **OBS Streaming:** recording, replay buffer, screenshots, scenes, and source examples.
- **Soundboard:** sound buttons and stop buttons.
- **Discord Audio:** mute, deafen, and voice-call style shortcuts.

Starter profiles are examples. They do not include private paths, tokens, passwords, or personal server details.

## 4. Edit A Button Without Accidentally Running It

1. Click a pad in the grid.
2. Look at the editor on the right.
3. Change the label.
4. Pick a color.
5. Choose an action type.
6. Fill in the action fields.
7. Click **Test Action** only when you want to run it.

Important: clicking a pad in the app selects it for editing. It does not run the action. Physical Launchpad presses run actions.

## 5. Make A Harmless First Button

Use a safe test before adding OBS, voice chat, or command actions.

1. Click `A1`.
2. Set label to `Google`.
3. Set color to `green`.
4. Set action type to `Open URL`.
5. Set URL to `https://www.google.com`.
6. Click **Test Action**.
7. Press `A1` on the Launchpad if the device is connected.

If the browser opens, the basic action path works.

## 6. Test The Launchpad

1. Plug the Launchpad Mini MK3 into USB.
2. Press **Reconnect** in OpenLaunchDeck.
3. Open `Device > MIDI Debug`.
4. Press the top-left physical pad.
5. Confirm a raw MIDI message appears.
6. Confirm the parsed button ID is `A1`.

If the parsed ID is wrong or blank, go to [Launchpad Mini MK3 Setup](Launchpad-Mini-MK3-Setup.md).

## 7. Make An OBS Clip Button

Use OBS WebSocket instead of a keyboard hotkey for clips. It works better while games are focused.

1. Open OBS.
2. Go to `Tools > WebSocket Server Settings`.
3. Enable the WebSocket server.
4. In OBS settings, enable Replay Buffer.
5. In OpenLaunchDeck, select a pad.
6. Set action type to `OBS WebSocket`.
7. Set operation to `save_replay_buffer`.
8. Enable `Start Replay Buffer If Needed`.
9. Click **Test Action** while OBS is open.

The first press may start the replay buffer. After it is running, pressing again saves a clip.

## 8. Make An OBS Screenshot Button

1. Select a pad.
2. Set action type to `OBS WebSocket`.
3. Set operation to `save_screenshot`.
4. Leave Screenshot Source blank to capture the current program scene.
5. Set Screenshot Folder to `%USERPROFILE%\Videos` or leave it blank for the OBS recording folder.
6. Set format to `png`.
7. Click **Test Action**.

OpenLaunchDeck reports failure if OBS does not create the image file.

## 9. Make A Soundboard Button

1. Select a pad.
2. Set action type to `Play Sound`.
3. Choose a local `.wav` or `.mp3` file.
4. Start volume at `60`.
5. Set Already Playing to `restart`.
6. Click **Test Action**.

If you hear it locally, the file and playback path work.

To make Discord or in-game voice chat hear it too, see [Soundboard And Voice Chat Routing](Soundboard-and-Discord-Routing.md).

For more common button setups, see [Button Recipes](Button-Recipes.md).

## 10. Stop Sounds

Create a safety button:

1. Select a nearby pad.
2. Set label to `Stop`.
3. Set color to `red`.
4. Set action type to `Stop Sound`.
5. Set scope to `all`.

Use it when a loop or long clip keeps playing.

## 11. Where Your Setup Is Stored

User files are stored here:

```text
%APPDATA%\OpenLaunchDeck
```

Important files and folders:

- `settings.json`
- `profiles`
- `logs`
- `backups`
- `midi_mappings`
- `imported_assets`

The installer updates app files. Your setup lives in AppData.
