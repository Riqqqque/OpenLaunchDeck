# Streaming Safety

Live controls should be fast, but going live, stopping a stream, and running destructive commands should always be deliberate.

## Recommended Layout

Keep routine controls on the main page:

```text
A1 Clip       A2 Screen     A3 Camera    A4 Mic
A5 Sound 1    A6 Sound 2    A7 Stop      A8 Next
```

Put stream start/stop on a separate page and mark both buttons Dangerous.

For the safest workflow, start the stream from OBS and use OpenLaunchDeck for replay clips, screenshots, scenes, sources, and mute controls.

## Dangerous Confirmation

For a Dangerous button:

1. First press arms it for five seconds.
2. GUI and Launchpad lighting show the warning state.
3. Second deliberate press executes it.
4. Timeout, page switch, or device disconnect cancels the armed state.

Immediate duplicate MIDI events cannot count as the second press.

OBS `start_streaming` always uses this confirmation, even if the profile forgot to mark the button Dangerous.

## Actions That Should Be Dangerous

- Start streaming
- Stop streaming
- Stop recording when losing footage would matter
- Shutdown, logoff, or restart
- Stop or restart a server
- Delete, overwrite, or move important data
- High-impact HTTP, SSH, command, or PowerShell operations

## Before Going Live

1. Confirm the correct OBS profile and scene collection.
2. Confirm the active OpenLaunchDeck profile and page.
3. Test replay, screenshot, camera, scene, and mute controls.
4. Confirm start/stop stream buttons are separated and guarded.
5. Check OBS preview, recording path, replay buffer, and audio meters.
6. Start streaming only after the live state is intentional.

## Safer OBS Controls

Good main-page operations:

- `save_replay_buffer`
- `save_screenshot`
- `switch_scene`
- `show_source`
- `hide_source`
- `toggle_source`
- `mute_input`
- `unmute_input`
- `toggle_input_mute`

Review start/stop stream and record operations before every profile import.

## Audit A Profile

1. Check every page.
2. Find OBS, HTTP, SSH, command, PowerShell, and multi-action buttons.
3. Read the actual operation or command.
4. Mark high-impact buttons Dangerous.
5. Move them away from frequently pressed pads.
6. Test only in a safe environment.

Exported profiles are readable JSON. Review them before importing or sharing.

## If Something Starts Unexpectedly

1. Stop the activity from its owning application, such as OBS.
2. Do not immediately edit or delete logs.
3. Open `%APPDATA%\OpenLaunchDeck\logs`.
4. Find button-result entries near the incident time.
5. Compare them with the owning application's logs.
6. Inspect the active profile for the relevant action.
7. Check other hotkey, startup, dashboard, and automation tools on the computer.

If no matching OpenLaunchDeck action appears at that time, keep investigating other control paths instead of assuming a Launchpad press occurred.

## Credentials

OBS passwords, webhook headers, and server details can be present in local profiles. Do not publish raw profiles or logs without reviewing them.
