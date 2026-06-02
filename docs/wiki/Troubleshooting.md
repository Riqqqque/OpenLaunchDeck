# Troubleshooting

This page starts with the fastest checks first.

## App Opens In Simulation Mode

Simulation mode means no active Launchpad MIDI connection is available.

Try this:

1. Confirm the Launchpad Mini MK3 is plugged in.
2. Use a direct USB port instead of a hub when testing.
3. Press **Reconnect**.
4. Open `Device > MIDI Debug`.
5. Check whether Launchpad input and output ports are listed.
6. If multiple Launchpad ports exist, choose the `LPMiniMK3 MIDI` style port rather than the DAW/session port.

Simulation mode is not an error. It lets you configure profiles without hardware.

## Connected But Pads Do Nothing

1. Open `Device > MIDI Debug`.
2. Press a physical pad.
3. If no raw message appears, the wrong input port is selected or another app may own the device.
4. If raw messages appear but no button ID appears, run calibration.
5. If the wrong button ID appears, save a custom mapping.

## Pads Light Wrong Or Do Not Light

1. Confirm the output MIDI port is selected.
2. Press Reconnect so OpenLaunchDeck sends Programmer Mode again.
3. Use MIDI Debug to inspect outgoing messages.
4. Run `Clear Pads` from MIDI Debug, then refresh the page.

Lighting depends on the device mode. Programmer Mode is recommended.

## OBS Replay Buffer Does Not Save

1. Confirm OBS is open.
2. Enable OBS WebSocket from `Tools > WebSocket Server Settings`.
3. Confirm the port is `4455`.
4. Confirm the password in OpenLaunchDeck matches OBS if authentication is on.
5. In OBS settings, enable Replay Buffer.
6. Press the replay button once to start replay buffer.
7. Wait a few seconds.
8. Press it again to save.

If OpenLaunchDeck reports success, an MP4 should exist in the OBS replay folder.

## OBS Screenshot Does Not Save

1. Use OBS WebSocket operation `save_screenshot`.
2. Leave source blank to capture the current program scene.
3. Set Screenshot Folder to a real folder, or leave it blank for the OBS recording folder.
4. Use `png` first.

OpenLaunchDeck verifies the image exists before reporting success.

## Hotkey Works On Desktop But Not In Game

Try this:

1. Use OBS WebSocket instead of a game hotkey when possible.
2. Bind OBS/game shortcuts to `F13` through `F24`.
3. Make sure OpenLaunchDeck is not running with lower privileges than the game.
4. Avoid hotkeys that the game already uses.

## Too Many Audio Outputs In The Soundboard Panel

Windows can report duplicate output endpoints with the same visible name, especially after installing virtual audio software. VoiceMeeter can also expose advanced buses such as `Voicemeeter In 1` through `Voicemeeter In 5`.

OpenLaunchDeck hides duplicate names and advanced VoiceMeeter buses in the Soundboard and Settings selectors. If a hidden device was already saved, the app keeps that saved device ID instead of silently erasing it.

If Windows itself shows many duplicate outputs:

1. Reboot after installing VoiceMeeter or other virtual audio software.
2. Open Windows Sound Settings.
3. Disable unused duplicate endpoints if Windows exposes them separately.
4. Keep one clear route for headphones, one for Discord playback, and one for soundboard voice routing.

## Friends Cannot Hear Soundboard Clips

1. Confirm the button has `Route To Voice Chat` enabled.
2. Confirm OpenLaunchDeck Voice Chat Output points to the virtual cable playback device.
3. Confirm Discord Input points to the matching virtual cable recording device.
4. In VoiceMeeter, make sure the soundboard strip routes to the bus Discord uses.
5. In Discord, use Mic Test while playing a clip.

## Soundboard Audio Sounds Bad

Try this:

- Lower OpenLaunchDeck button volume to `60` to `80`.
- Lower the VoiceMeeter strip by `3 dB` to `6 dB`.
- Disable Discord noise suppression, echo cancellation, noise reduction, and automatic gain control.
- Use clean `.wav` or high-quality `.mp3` clips.
- Avoid stacking multiple loud clips with `overlap`.

## You Cannot Hear Friends In Discord

1. Set Discord output to `Default` or the VoiceMeeter AUX playback route.
2. Make sure VoiceMeeter AUX routes to `A1`.
3. Make sure Hardware Out `A1` is your real headphones or audio interface.
4. Do not route Discord output back into the Discord input bus.

## Logs

Open logs from:

`Help > Open Logs Folder`

The main log is stored under:

`%APPDATA%\OpenLaunchDeck\logs`
