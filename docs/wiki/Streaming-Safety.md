# Streaming Safety

This page is for anyone using OpenLaunchDeck with OBS while streaming, recording, or testing scenes.

The main rule: routine stream controls should be easy to press, but going live should be deliberate.

## Recommended Live Setup

For most people:

- Start the stream from OBS itself.
- Use OpenLaunchDeck for replay clips, screenshots, scene switches, camera visibility, and mute controls.
- Put any Start Stream button on a separate page, away from buttons used during gameplay.
- Keep Stop Stream dangerous too, because an accidental stop can be just as bad during a live session.

## Built-In Start Stream Guard

OBS `start_streaming` actions always require confirmation in OpenLaunchDeck.

The behavior is:

1. First press arms the button.
2. The pad shows the armed state.
3. A second deliberate press within the confirmation window starts the stream.

This guard applies even if a profile forgot to enable the Dangerous checkbox.

OpenLaunchDeck also rejects an immediate duplicate press as the confirmation press. That prevents hardware bounce or duplicate MIDI events from counting as two deliberate presses.

## Safer Button Layout

A practical streaming page:

```text
A1 Clip       A2 Screen     A3 Camera    A4 Mic
A5 Sound 1    A6 Sound 2    A7 Stop      A8 Next
```

Put Start Stream on a separate page:

```text
H7 Start Stream
H8 Stop Stream
```

Mark both as Dangerous.

## Before Going Live

Run this checklist before a stream:

1. Open OBS.
2. Confirm the correct OBS profile and scene collection are active.
3. Open OpenLaunchDeck.
4. Confirm the active profile and page are correct.
5. Confirm any Start Stream button is yellow or marked Dangerous.
6. Test replay, screenshot, camera, and mute buttons before starting the stream.
7. Start the stream only when OBS preview and audio meters look correct.

## Safe OBS Action Choices

Good Launchpad actions during a stream:

- `save_replay_buffer`
- `save_screenshot`
- `switch_scene`
- `show_source`
- `hide_source`
- `toggle_source`
- `mute_input`
- `unmute_input`
- `toggle_input_mute`

Use extra care with:

- `start_streaming`
- `stop_streaming`
- `start_recording`
- `stop_recording`

## Reviewing A Profile For Risk

To audit a profile:

1. Open the profile in OpenLaunchDeck.
2. Check every page.
3. Look for OBS WebSocket buttons.
4. Read the operation field.
5. Mark high-impact actions Dangerous.
6. Move high-impact actions away from buttons pressed during gameplay.

High-impact actions include stream start/stop, recording stop, server restart, shutdown, destructive commands, and anything that changes live output.

## If A Stream Starts Unexpectedly

Do this before changing settings:

1. Stop the stream in OBS.
2. Open `%APPDATA%\OpenLaunchDeck\logs`.
3. Check the latest `openlaunchdeck.log`.
4. Look for `Button <id>:` entries near the incident time.
5. Open OBS `Help > Log Files > View Current Log`.
6. Compare OBS's stream start time with OpenLaunchDeck button logs.
7. Inspect the active OpenLaunchDeck profile for `start_streaming`.

If no OpenLaunchDeck button result appears near the time, check OBS hotkeys, OBS Auto-Start settings, Stream Deck-style tools, Twitch dashboard controls, and any other automation running on the PC.

## Logs

OpenLaunchDeck logs successful and failed button results under:

```text
%APPDATA%\OpenLaunchDeck\logs
```

Logs do not replace OBS logs, but they help identify whether a Launchpad or Test Action triggered an OBS action.
