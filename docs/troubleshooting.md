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

## Soundboard Not Heard In Voice Chat

Open `Soundboard > Open Soundboard Panel` and click `Auto Find Route`. If OpenLaunchDeck shows `Voice chat input: ...`, set Discord, game chat, or another voice app to that input and make sure each sound button has `Route To Voice Chat` enabled.

If Auto Find Route cannot find a route, Windows does not currently expose a playback-to-recording bridge for voice chat. Add a simple audio bridge endpoint or use hardware loopback from an audio interface, then run Auto Find Route again. OpenLaunchDeck does not install audio drivers.

For games with push-to-talk, hold push-to-talk while playing the routed soundboard clip. The game transmits the route only while push-to-talk is active.

See [Voice Chat Routing](discord_voice_routing.md) for the full step-by-step setup.

## Soundboard Sounds Bad In Voice Chat

If friends or teammates say routed soundboard clips are muffled, crunchy, or underwater, the voice app/game may be processing the clip like microphone noise. In Discord, try turning off noise suppression, echo cancellation, noise reduction, and automatic gain control. Use `.wav` or high-quality `.mp3` files where possible.

If friends can barely hear clips, raise the per-button volume in OpenLaunchDeck first. Start around `60` to `80`. Also check voice app/game input volume, Discord input sensitivity, and the Windows volume mixer for the route.

## Browser Shows Audio Renderer Error

Keep Windows output set to a real hardware device, then restart the browser. In OpenLaunchDeck, use `System default` for the normal sound output device and reserve the voice route output only for buttons that enable `Route To Voice Chat`.

## Command Action Not Working

Enable `wait` on the command action to capture an exit code. Check the working directory and logs.

## App Will Not Start

Run from a terminal with:

```powershell
python -m openlaunchdeck.main
```

Then check `%APPDATA%\OpenLaunchDeck\logs`.

## Launch At Startup Does Not Work

Open `Settings` and enable `Launch at startup`, then save the dialog. OpenLaunchDeck writes a current-user Windows startup entry named `OpenLaunchDeck`.

If the app still does not start after signing in, check these items:

- Confirm the installed app still exists at the path shown in the Windows startup entry.
- Open OpenLaunchDeck once after an app update; the packaged app repairs stale startup paths.
- The installed startup entry uses background mode. If a window-layout tool should position the window, have that tool launch `OpenLaunchDeck.exe --show` after sign-in.
- Keep `Start minimized` on only if you want direct app launches to start in the background. If tray mode is off, it starts minimized to the taskbar.
- Check `%APPDATA%\OpenLaunchDeck\logs` for startup registration errors.

## Update Check Fails

Confirm the update manifest URL is configured and reachable. The manifest must include a valid 64-character SHA256 checksum.

## Installer Update Fails

Download the installer manually. User data remains in AppData.

## App Feels Slow

Enable performance logging in Settings, reproduce the issue, and inspect the logs.
