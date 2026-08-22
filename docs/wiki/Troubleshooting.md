# Troubleshooting

Start with the section that matches the symptom. Do not change MIDI, OBS, and audio settings all at once; confirm one layer at a time.

## First Three Checks

1. Confirm OpenLaunchDeck is the latest version under **Help > About OpenLaunchDeck**.
2. Read the status bar after reproducing the problem.
3. Use **Help > Copy Diagnostic Info** and **Help > Open Logs Folder**.

Remove passwords, tokens, and private paths before posting diagnostics.

## App And Window

### The App Will Not Open

OpenLaunchDeck is single-instance and may already be in the system tray.

1. Double-click the tray icon.
2. Use the tray **Open OpenLaunchDeck** command.
3. Launch the installed executable with `--show`.
4. Open Task Manager and check for one OpenLaunchDeck process.
5. If it is unresponsive, end that process once and relaunch.

If no process starts, open `%APPDATA%\OpenLaunchDeck\logs` and check the newest log.

### The Window Is Off Screen Or Hidden

Use `OpenLaunchDeck.exe --show`. The existing instance should restore and move the window into a visible work area when needed.

External window-layout tools should use `--show` when they need to position the window and `--background` when they only need to ensure the app is running.

### Launch At Startup Does Not Work

1. Open Settings and enable **Launch at startup**.
2. Close Settings with **OK**.
3. Restart OpenLaunchDeck once.
4. Check Task Manager's Startup Apps page.

The setting uses the current user's Windows Run entry. If another startup manager removes it, enable the setting again. Do not configure several tools to launch independent copies; OpenLaunchDeck is single-instance.

## Launchpad And MIDI

### Why Am I In Simulation Mode?

Simulation mode means no usable Launchpad input/output pair is open. The editor and Test Action still work.

1. Confirm USB power and cable connection.
2. Click **Reconnect**.
3. Open **Device > MIDI Debug**.
4. Check input and output port names.
5. Try the second `LPMiniMK3 MIDI` interface.

### It Says Connected But Pads Do Nothing

1. Open MIDI Debug.
2. Press a pad.
3. If no raw message appears, change the input port.
4. If a raw message appears without a button ID, restore the default mapping or calibrate.
5. If the correct button ID appears, check whether the configured button is enabled and has an action.

### The Wrong GUI Pad Reacts

Run calibration and press only the requested physical pad at each step. Save, reconnect, and verify all four corners.

Custom mappings are under `%APPDATA%\OpenLaunchDeck\midi_mappings`. Use **Restore Default Mapping** when a custom mapping is incomplete.

### Pads Do Not Light Or Show Wrong Colors

1. Confirm the output port is the programmer-control interface.
2. Confirm Programmer Mode in MIDI Debug.
3. Refresh the page or reconnect.
4. Watch outgoing messages in MIDI Debug.
5. Record device mode and raw output before reporting a palette mismatch.

An outgoing log proves what the app sent, not that a particular firmware/mode interpreted it identically.

### Unplug/Replug Does Not Recover

Wait a few seconds for the background health check, then click **Reconnect** once. Reopen MIDI Debug only if automatic recovery fails.

## Button Actions

### Clicking A Grid Pad Does Not Run It

That is intentional. Grid clicks select pads for editing. Use **Test Action** or press the physical Launchpad pad.

### A Button Is Armed But Does Not Run

Dangerous buttons require a second deliberate press within five seconds. An immediate duplicate press is ignored. Page changes and disconnects cancel the armed state.

### Hotkey Works On Desktop But Not In A Game

1. Confirm the pad is reaching OpenLaunchDeck.
2. Run the game and OpenLaunchDeck at the same privilege level.
3. Try borderless fullscreen.
4. Bind an unused extended key such as `F15`.
5. Prefer a direct integration such as OBS WebSocket when available.

Some games intentionally reject synthetic input. OpenLaunchDeck does not bypass anti-cheat or input protections.

### Media Play/Pause Does Nothing

1. Make sure the action is **Media Control**, not a normal Hotkey.
2. Start playback once in the browser or media app.
3. Focus that app and test again.
4. Check whether another media application is consuming Windows media commands.

### Command Or PowerShell Fails

- Run the exact command manually first.
- Verify the working directory.
- Use absolute paths or valid environment variables.
- Turn off **Run Hidden** temporarily when visible output helps.
- Check the action result and log.
- Match application privilege levels when the command needs elevation.

## OBS

### OBS WebSocket Cannot Connect

Check that OBS is open, the server is enabled, host is `127.0.0.1`, port is normally `4455`, and the password matches.

### Replay Buffer Does Not Save

1. Enable Replay Buffer under OBS Output settings.
2. Confirm the recording folder is writable.
3. Use `save_replay_buffer` with **Start Replay Buffer If Needed** on.
4. First press may only start the buffer; wait, then press again.
5. Restart the OBS replay buffer if no file appears.

OpenLaunchDeck reports failure when OBS accepts the command but no replay file can be verified.

### Screenshot Does Not Save

1. Use `save_screenshot`.
2. Leave Screenshot Source blank for the current program scene.
3. Choose a writable folder.
4. Try `png`.
5. Confirm the exact source name if one is configured.

### Scene, Source, Or Input Is Not Found

Copy the name exactly from OBS. Sources belong to scenes; confirm the configured scene contains that source. Input Name comes from the Audio Mixer.

### A Stream Started Unexpectedly

Stop it in OBS, preserve both applications' logs, and follow [Streaming Safety](Streaming-Safety.md). Compare times before deciding which control path caused it.

## Soundboard And Voice Chat

### Local Sound Does Not Play

1. Confirm the file exists.
2. Try a short `.wav` or `.mp3`.
3. Set the normal output to System default or your real headphones/interface.
4. Set global and button volume to audible values.
5. Check the Windows volume mixer.

### Other People Cannot Hear The Clip

1. Confirm local playback works first.
2. Enable **Route To Voice Chat** on the button.
3. Select the route playback endpoint in OpenLaunchDeck.
4. Select its matching recording endpoint as the voice application's input.
5. Watch the voice application's input meter while the clip plays.
6. Hold push-to-talk in games that require it.

### The Clip Works But My Microphone Does Not

Enable **Route Microphone**, select the real microphone, and verify the input meter moves when you speak. Keep OpenLaunchDeck running in the tray while the voice app uses the combined route.

### My Voice Or Clips Are Very Quiet

Start with global volume `100`, microphone route volume `100`, route endpoint volume `100`, and button volume `50` to `70`. Adjust button volume first for clips.

Disable aggressive noise suppression, echo cancellation, or automatic gain control when those features crush non-speech audio. Re-test microphone quality afterward.

### Audio Is Duplicated Or Echoing

- Send Discord/game output to your headphones, not the voice route.
- Use only one microphone-forwarding path.
- Disable Windows "Listen to this device" unless it is intentionally required.
- Keep only one monitor path active.
- Check streaming/capture software for a second monitor source.

### Too Many Or Duplicate Audio Devices

OpenLaunchDeck hides duplicate display names and advanced mixer buses in normal selectors. If a saved device is unavailable, reselect the current endpoint after reconnecting or updating USB audio hardware.

### Browser Shows Audio Renderer Error

This usually means Windows changed or lost an output device while the browser was playing.

1. Re-select the browser's output in Windows Volume Mixer.
2. Reload the page.
3. Restart only the affected browser if needed.
4. Check for duplicate monitoring or audio-route loops.

Avoid restarting every audio device while live applications are running.

## Profiles And Data

### A Profile Will Not Load

Open the logs for the parse error. Move the broken JSON out of the profiles folder, start the app, and restore from `%APPDATA%\OpenLaunchDeck\backups` if available.

Do not overwrite the only copy while repairing JSON.

### A Sound Or App Path Broke On Another Computer

Profile export does not copy external files. Move the required assets separately and update machine-specific paths after import.

## Updates And Installer

### Update Check Fails

Check internet access, system date/time, the optional custom manifest URL, and the log. Leave the custom URL empty for normal GitHub release checks.

### Downloaded Update Will Not Install

OpenLaunchDeck will not run an installer whose SHA256 does not match. Download again from the official release. Quit the tray instance before a manual install if Windows cannot replace files.

User data should remain under AppData. See [Release and Update Flow](Release-and-Update-Flow.md).

## Performance

### The App Feels Slow Or A Game Feels Different

1. Close MIDI Debug.
2. Turn off performance logging after diagnosis.
3. Minimize the app or use Deck View.
4. Stop overlapping/looping sounds.
5. Check Task Manager for sustained CPU, memory growth, repeated child processes, or disk activity.
6. Identify the exact action that causes the change.

OpenLaunchDeck should run at Normal priority. Report sustained resource use with diagnostics and reproduction steps.

## What To Include In A Bug Report

- OpenLaunchDeck version
- Windows version
- Simulation or connected state
- Selected MIDI ports when hardware is involved
- Exact action type and fields with secrets removed
- Short reproduction steps
- User-facing result
- Relevant log excerpt
- Screenshot when the problem is visual

Use the [issue chooser](https://github.com/Riqqqque/OpenLaunchDeck/issues/new/choose).
