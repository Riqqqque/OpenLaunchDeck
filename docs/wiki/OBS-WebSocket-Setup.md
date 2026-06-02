# OBS WebSocket Setup

OpenLaunchDeck can control OBS directly through OBS WebSocket. This is the recommended path for replay buffer clips and screenshots because it does not depend on games accepting synthetic hotkeys.

Use OBS WebSocket for actions that must work while a game is focused.

## Enable OBS WebSocket

1. Open OBS.
2. Go to `Tools > WebSocket Server Settings`.
3. Enable the WebSocket server.
4. Keep the default port `4455` unless you have a reason to change it.
5. If authentication is enabled, copy the OBS WebSocket password.

In OpenLaunchDeck, set the OBS WebSocket action fields:

- `Host`: `127.0.0.1`
- `Port`: `4455`
- `Password`: your OBS WebSocket password, if OBS requires one

Keep the password private. It only needs to be stored in your local OpenLaunchDeck profile/settings.

## Replay Buffer Clips

Use action type `OBS WebSocket` with operation `save_replay_buffer`.

Recommended settings:

- `Start Replay Buffer If Needed`: enabled
- `Replay Verify Timeout Ms`: `10000`
- `Timeout Ms`: `3000`

Behavior:

- If the replay buffer is stopped, the first press starts it.
- The next press saves a clip.
- OpenLaunchDeck waits for OBS to report a real replay file before reporting success.
- If OBS accepts the save request but no MP4 appears, OpenLaunchDeck reports failure so the problem is visible.

Clips save to the OBS replay buffer folder, usually:

`%USERPROFILE%\Videos`

## Recommended Clip Button

For a simple gaming setup:

- Button: `H7`
- Label: `Clip`
- Color: `purple`
- Action: `OBS WebSocket`
- Operation: `save_replay_buffer`
- Start replay buffer if needed: on
- Replay verify timeout: `10000`

This is safer than binding the pad to an OBS hotkey because it talks to OBS directly.

## Screenshots

Use action type `OBS WebSocket` with operation `save_screenshot`.

Recommended settings:

- `Screenshot Source`: leave blank to capture the current OBS program scene
- `Screenshot Folder`: leave blank for the OBS recording folder, or set a folder such as `%USERPROFILE%\Videos`
- `Screenshot Format`: `png`
- `Timeout Ms`: `3000`

OpenLaunchDeck verifies that the PNG exists before reporting success.

By default, screenshots save beside the normal OBS videos. A typical result looks like:

`%USERPROFILE%\Videos\Screenshot 2026-06-02_00-38-49.png`

## Recommended Screenshot Button

For a simple gaming setup:

- Button: `H8`
- Label: `Screen`
- Color: `cyan`
- Action: `OBS WebSocket`
- Operation: `save_screenshot`
- Screenshot source: blank
- Screenshot folder: `%USERPROFILE%\Videos`
- Screenshot format: `png`

OpenLaunchDeck reports failure if OBS does not create the image file.

## Scene and Source Controls

Supported OBS WebSocket operations include:

- `start_recording`
- `stop_recording`
- `start_streaming`
- `stop_streaming`
- `switch_scene`
- `show_source`
- `hide_source`
- `toggle_source`
- `mute_input`
- `unmute_input`
- `toggle_input_mute`
- `save_replay_buffer`
- `save_screenshot`

For `switch_scene`, set `Scene Name` to the exact OBS scene name.

For source visibility, set `Scene Name` and `Source Name` to the exact OBS names. A common camera source name is `Video Capture Device`.

For input mute actions, set `Input Name` to the exact OBS input name, such as `Mic/Aux`.

## Camera Source Toggle

To toggle a camera source:

1. In OBS, confirm the scene name.
2. Confirm the source/input name.
3. In OpenLaunchDeck, choose `OBS WebSocket`.
4. Use `show_source`, `hide_source`, or `toggle_source`.
5. Enter the exact OBS scene and source names.

Names must match OBS. Copy them from OBS if needed.

## Troubleshooting

If clips or screenshots do not work:

1. Confirm OBS is running.
2. Confirm OBS WebSocket is enabled.
3. Confirm the password in OpenLaunchDeck matches OBS.
4. Confirm replay buffer is enabled in OBS settings.
5. Press the clip button once to start replay buffer, wait a few seconds, then press again to save.
6. Check `%APPDATA%\OpenLaunchDeck\logs\openlaunchdeck.log`.
7. Check OBS logs from `Help > Log Files > View Current Log`.

If the action reports success, a file should exist. If a file does not appear, treat it as a bug and check the logs.

## Why Not Just Use Hotkeys

Hotkeys are fine for simple desktop actions. OBS WebSocket is better for streaming actions because it:

- Does not need the game to accept keyboard input.
- Can report clearer errors.
- Can verify replay and screenshot files.
- Avoids conflicts with in-game keybinds.
