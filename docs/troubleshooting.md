# Troubleshooting

## No Device Detected

Check USB connection, open `Device > MIDI Debug`, and confirm input/output ports are listed. On Windows, look for names like `LPMiniMK3 MIDI`, `MIDIIN2 (LPMiniMK3 MIDI)`, or `MIDIOUT2 (LPMiniMK3 MIDI)`. If no ports appear, reconnect the Launchpad and press Reconnect.

## Pads Not Lighting

Confirm an output port is selected. Try Programmer Mode and press `Device > Reconnect`.

## Pad Presses Not Recognized

Open MIDI Debug and press a pad. If raw messages appear but parsed button IDs do not, run calibration. If no raw messages appear but the app says connected, reconnect after closing other MIDI apps and make sure the selected input is the second Launchpad MIDI interface, such as `MIDIIN2 (LPMiniMK3 MIDI)` or `LPMiniMK3 MIDI 1`.

## Wrong Pad Mapping

Use calibration and save the mapping. User mappings are stored in AppData.

## Hotkeys Do Not Work In Game

OpenLaunchDeck sends hotkeys through a Windows native keyboard path first, which is the best fit for game and OBS shortcuts. Use unused keys such as `F13` through `F24` for game-facing actions so they do not conflict with normal keyboard controls.

If a pad press works on the desktop but not in a game, check these items:

- Make sure the button action is `Hotkey`, not `No Action`.
- In the game or OBS, bind the same key shown in OpenLaunchDeck, such as `F14`.
- If the game is running as administrator, run OpenLaunchDeck as administrator too. Windows can block keyboard events from a normal app into an elevated game.
- Try borderless fullscreen if exclusive fullscreen ignores synthetic keyboard input.
- Open `Device > MIDI Debug` and press the pad. If MIDI events appear instantly, the Launchpad path is working and the issue is the target app accepting the hotkey.

## OBS Clip Button Does Not Save

Use the `OBS WebSocket` action with `save_replay_buffer` for clipping. It is more reliable than a hotkey while gaming because it talks to OBS directly.

In OBS, enable `Tools > WebSocket Server Settings > Enable WebSocket server`. If authentication is enabled, copy the OBS WebSocket password into the button's password field. When the replay buffer is stopped, the first press starts it and the next press saves a clip.

OpenLaunchDeck waits for OBS to report a real replay file. If OBS accepts the save command but no MP4 appears, the action returns a failure instead of pretending the clip was saved. Restart the OBS replay buffer or restart OBS, then press the clip button again.

For screenshots, use the `OBS WebSocket` action with `save_screenshot`. It saves the current OBS program scene directly and does not require the game to accept a keyboard shortcut. By default, screenshots go to the OBS recording folder, usually your Videos folder.

For camera visibility and microphone mute buttons, use OBS WebSocket operations such as `show_source`, `hide_source`, `mute_input`, and `unmute_input`. They verify the OBS state after running, which is more reliable than sending F-key hotkeys into OBS.

## Sound Not Playing

Confirm the file exists and try `.wav` or `.mp3`. Check Windows volume mixer and the logs folder.

## Soundboard Not Heard In Discord

Route the playback device through an external virtual audio cable app. OpenLaunchDeck does not install audio drivers.

For Discord with VoiceMeeter Banana, use this baseline route:

- Windows output: `Voicemeeter AUX Input`
- Windows input: `Voicemeeter Out B1`
- Discord output: `Default` or `Voicemeeter AUX Input`
- Discord input: `Default` or `Voicemeeter Out B1`
- OpenLaunchDeck voice-chat output: `Voicemeeter Input`

In VoiceMeeter, route the main virtual input strip to `A1` and `B1`, and route the AUX strip to `A1` only. If Discord output is sent directly to the real headphones while VoiceMeeter is using that device as `A1`, Discord playback may fail or friends may not be audible.

See [Discord Voice Chat Routing](discord_voice_routing.md) for the full step-by-step setup.

## Soundboard Sounds Bad In Discord

If friends say routed soundboard clips are muffled, crunchy, or underwater, Discord is usually processing the clip like microphone noise. In `User Settings > Voice & Video`, try turning off noise suppression, echo cancellation, noise reduction, and automatic gain control. Use `.wav` or high-quality `.mp3` files where possible.

If friends can barely hear clips, raise the per-button volume in OpenLaunchDeck first. Start around `60` to `80`. Also check that the VoiceMeeter strip carrying soundboard audio is near `0 dB`.

## Command Action Not Working

Enable `wait` on the command action to capture an exit code. Check the working directory and logs.

## App Will Not Start

Run from a terminal with:

```powershell
python -m openlaunchdeck.main
```

Then check `%APPDATA%\OpenLaunchDeck\logs`.

## Update Check Fails

Confirm the update manifest URL is configured and reachable. The manifest must include a valid 64-character SHA256 checksum.

## Installer Update Fails

Download the installer manually. User data remains in AppData.

## App Feels Slow

Enable performance logging in Settings, reproduce the issue, and inspect the logs.
