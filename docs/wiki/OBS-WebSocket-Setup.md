# OBS WebSocket Setup

OpenLaunchDeck can control OBS directly through OBS WebSocket. This is the recommended path for replay buffer clips and screenshots because it does not depend on games accepting synthetic hotkeys.

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

## Scene and Source Controls

Supported OBS WebSocket operations include:

- `start_recording`
- `stop_recording`
- `start_streaming`
- `stop_streaming`
- `switch_scene`
- `toggle_input_mute`
- `save_replay_buffer`
- `save_screenshot`

For `switch_scene`, set `Scene Name` to the exact OBS scene name.

For `toggle_input_mute`, set `Input Name` to the exact OBS input name, such as `Mic/Aux`.

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
