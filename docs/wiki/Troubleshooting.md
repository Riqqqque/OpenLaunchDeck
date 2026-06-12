# Troubleshooting

This page starts with the fastest checks first.

## First Three Checks

Before going deep, check these:

1. Is OpenLaunchDeck running the profile you think it is?
2. Is the selected button enabled?
3. Does **Test Action** work from the editor?

If Test Action works but the physical Launchpad does not, troubleshoot MIDI.

If Test Action fails too, troubleshoot the action settings.

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

## The App Says Connected But Nothing Happens

Check the exact pad path:

1. Open `Device > MIDI Debug`.
2. Press the physical pad.
3. Confirm a raw MIDI message appears.
4. Confirm the parsed button ID matches the pad, such as `A8`.
5. Open the active profile and page in the main window.
6. Select that same button ID.
7. Confirm the action is not `No Action`.
8. Confirm the button is enabled.

If raw MIDI appears but the wrong button ID appears, run calibration.

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

## Stream Started Unexpectedly

Use the safety checklist in [Streaming Safety](Streaming-Safety.md).

Immediate checks:

1. Open the active profile.
2. Look for any `OBS WebSocket` button with operation `start_streaming`.
3. Confirm it is marked Dangerous or relies on the built-in start-stream confirmation guard.
4. Move the button away from common clip, screenshot, camera, and mute buttons.
5. Check `%APPDATA%\OpenLaunchDeck\logs` for recent button results.
6. Check OBS logs from `Help > Log Files > View Current Log`.

OpenLaunchDeck requires confirmation for `start_streaming`, but profile layout still matters. Keep go-live controls separated from routine stream controls.

## Hotkey Works On Desktop But Not In Game

Try this:

1. Use OBS WebSocket instead of a game hotkey when possible.
2. Bind OBS/game shortcuts to `F13` through `F24`.
3. Make sure OpenLaunchDeck is not running with lower privileges than the game.
4. Avoid hotkeys that the game already uses.

For OBS camera, mic, stream, replay, screenshot, and scene controls, prefer the `OBS WebSocket` action over hotkeys. Direct OBS actions can verify the source or mute state after the command runs.

## Too Many Audio Outputs In The Soundboard Panel

Windows can report duplicate output endpoints with the same visible name, especially after installing audio routing software. Some drivers can also expose advanced buses that normal users do not need.

OpenLaunchDeck hides duplicate names and advanced mixer buses in the Soundboard and Settings selectors. If a hidden device was already saved, the app keeps that saved device ID instead of silently erasing it.

If Windows itself shows many duplicate outputs:

1. Reboot after installing or removing audio routing software.
2. Open Windows Sound Settings.
3. Disable unused duplicate endpoints if Windows exposes them separately.
4. Keep browser, game, and Discord playback on your real hardware output for the simple route.
5. Use one voice route for soundboard voice routing.

## Friends Or Teammates Cannot Hear Soundboard Clips

Use this exact checklist:

1. Confirm the sound plays locally first.
2. Confirm the button has `Route To Voice Chat` enabled.
3. Open `Soundboard > Open Soundboard Panel`.
4. Confirm Default Output is your real headphones, speakers, or audio interface.
5. Confirm Voice Route Output is the route playback side.
6. Confirm Route Microphone is on.
7. Confirm Microphone Input is your real mic.
8. In Discord, game chat, or another voice app, set Input Device or Microphone to the route recording side, such as `CABLE Output (VB-Audio Virtual Cable)`.
9. Keep app/game output on your real headphones, speakers, or audio interface.
10. Set Discord Noise Suppression to `None`.
11. Turn Echo Cancellation off.
12. Use Discord Mic Test, or hold game push-to-talk, while playing a routed clip.

If the input meter moves during the clip, the app is receiving the soundboard route.

If the meter does not move, the app/game is listening to the wrong input or the route is not receiving audio.

## Soundboard Audio Sounds Bad

Try this:

- Lower OpenLaunchDeck button volume to `60` to `80`.
- Set Discord noise suppression to `None`.
- Disable Discord echo cancellation.
- Disable Discord automatic gain control if the clip volume pumps up and down.
- For games, hold push-to-talk while the clip plays if push-to-talk is enabled.
- Use clean `.wav` or high-quality `.mp3` clips.
- Avoid stacking multiple loud clips with `overlap`.

## You Cannot Hear Friends Or Teammates

1. Set app/game output to `Default` or your real headphones, speakers, or audio interface.
2. Make sure Windows output is still your real hardware output.
3. Do not route app/game output back into the voice input route.
4. Restart the app/game after changing Windows audio defaults.

## Browser Shows Audio Renderer Error

1. Set Windows output to your real headphones, speakers, or audio interface.
2. In OpenLaunchDeck, set Default Output to `System default`.
3. Keep Voice Route Output separate from normal browser and Discord playback.
4. Restart the browser after changing audio routes.
5. If it still fails, restart the Windows Audio service.

## Launch At Startup Does Not Work

1. Open `Settings`.
2. Enable `Launch at startup`.
3. Save the dialog.
4. Confirm OpenLaunchDeck starts the next time you sign in to Windows.

The setting uses the current Windows user startup entry and does not require administrator rights. If you update or move the installed app, open it once after the update so it can repair the startup path.

If `Start minimized` is enabled while tray mode is off, OpenLaunchDeck starts minimized to the taskbar.

## Logs

Open logs from:

`Help > Open Logs Folder`

The main log is stored under:

`%APPDATA%\OpenLaunchDeck\logs`

## What To Send With A Bug Report

Include:

- OpenLaunchDeck version.
- Windows version.
- Whether the Launchpad is connected or Simulation mode is active.
- The action type that failed.
- The exact button ID, such as `A8`.
- The last few lines from the OpenLaunchDeck log.
- For OBS issues, the OBS WebSocket operation and OBS log.
- For soundboard issues, the selected output/input devices and whether Discord Mic Test or game push-to-talk receives the routed clip.
