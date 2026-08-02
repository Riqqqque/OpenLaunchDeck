# OBS WebSocket Setup

OBS WebSocket lets OpenLaunchDeck control OBS directly. It is more reliable than sending game hotkeys for replay clips, screenshots, scenes, source visibility, and mute state.

## 1. Enable OBS WebSocket

In OBS Studio:

1. Open **Tools > WebSocket Server Settings**.
2. Enable the WebSocket server.
3. Keep the default port `4455` unless another application already uses it.
4. Enable authentication for normal use.
5. Save or copy the password.
6. Leave OBS running.

OpenLaunchDeck defaults:

```text
Host: 127.0.0.1
Port: 4455
Timeout Ms: 3000
```

Use `127.0.0.1` when OBS is on the same computer. Do not expose OBS WebSocket to the internet.

## 2. Create A Connection Test

Use a harmless OBS operation first:

- Label: `Screen`
- Action: **OBS WebSocket**
- Operation: `save_screenshot`
- Host: `127.0.0.1`
- Port: `4455`
- Password: the OBS WebSocket password
- Screenshot Source: blank
- Screenshot Folder: `%USERPROFILE%\Videos`
- Screenshot Format: `png`

Click **Test Action**. A successful test proves the host, port, password, and basic request path work.

## 3. Use Exact OBS Names

OBS names are case-sensitive and must match what OBS displays.

| OpenLaunchDeck field | Where to find it in OBS |
| --- | --- |
| Scene Name | Scenes panel |
| Source Name | Sources panel inside the scene |
| Input Name | Audio Mixer name |
| Screenshot Source | Scene or source to capture; leave blank for the current program scene |

If a camera appears in several scenes, configure the scene that contains the source you want to change.

## Operations

| Operation | Result |
| --- | --- |
| `save_replay_buffer` | Saves a replay; can start the buffer on the first press |
| `start_replay_buffer` | Starts the replay buffer |
| `stop_replay_buffer` | Stops the replay buffer |
| `save_screenshot` | Saves the chosen source or current program scene |
| `start_recording` | Starts recording |
| `stop_recording` | Stops recording |
| `start_streaming` | Starts streaming after mandatory confirmation |
| `stop_streaming` | Stops streaming |
| `switch_scene` | Changes the program scene |
| `show_source` | Makes a source visible |
| `hide_source` | Hides a source |
| `toggle_source` | Reverses source visibility |
| `mute_input` | Mutes an OBS input |
| `unmute_input` | Unmutes an OBS input |
| `toggle_input_mute` | Reverses mute state |

## Replay Buffer Clips

Before testing:

1. Open **Settings > Output > Replay Buffer** in OBS.
2. Enable the replay buffer.
3. Configure replay length and recording path.
4. Apply settings.

Recommended button:

- Label: `Clip`
- Color: `purple`
- Operation: `save_replay_buffer`
- Start Replay Buffer If Needed: on
- Replay Verify Timeout Ms: `10000`

Behavior:

- If the buffer is stopped, the first press starts it and reports that result.
- If the buffer is active, the press requests a save.
- OpenLaunchDeck waits for OBS to report a real replay file before showing success.

If OBS accepts the request but no file appears, restart the replay buffer and verify the OBS recording path.

## Screenshots

Recommended button:

- Label: `Screen`
- Color: `cyan`
- Operation: `save_screenshot`
- Screenshot Source: blank
- Screenshot Folder: `%USERPROFILE%\Videos`
- Screenshot Format: `png`

A blank source captures the current program scene. A blank folder uses the OBS recording directory when OBS reports one, then falls back to the Windows Videos folder.

## Scenes And Sources

Switch scene:

- Operation: `switch_scene`
- Scene Name: exact destination scene

Toggle a camera or overlay:

- Operation: `toggle_source`
- Scene Name: scene containing the source
- Source Name: exact source name

Use `show_source` and `hide_source` when separate on/off buttons are clearer than a toggle.

## OBS Audio Inputs

Toggle an OBS microphone or desktop-audio input:

- Operation: `toggle_input_mute`
- Input Name: exact Audio Mixer name

Use `mute_input` and `unmute_input` when you need separate state-setting buttons.

These actions control OBS input state. They do not mute the microphone globally in Windows or another voice application.

## Streaming Safety

`start_streaming` always requires a deliberate second press, even if the button's Dangerous option was not enabled. Immediate duplicate hardware messages cannot count as the confirmation press.

Still mark both start and stop stream buttons Dangerous, place them on a separate page, and test them only when going live is safe.

See [Streaming Safety](Streaming-Safety.md).

## Password Storage

The password field is masked in the editor, but the value is stored in the local profile JSON so the button can reconnect. Treat exported profiles containing a password as sensitive.

## Common Errors

| Error | Check |
| --- | --- |
| Connection refused | OBS is open, WebSocket is enabled, host and port match |
| Authentication failed | Password matches current OBS WebSocket settings |
| Scene/source not found | Exact spelling and correct scene |
| Input not found | Exact Audio Mixer name |
| Replay did not appear | Replay buffer active, recording path writable, verify timeout long enough |
| Screenshot did not appear | Source exists and destination folder is writable |

For more, open [Troubleshooting](Troubleshooting.md).
