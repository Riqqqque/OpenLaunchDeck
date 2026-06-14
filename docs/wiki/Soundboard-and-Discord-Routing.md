# Soundboard And Voice Chat Routing

This page explains how to make a soundboard clip play for you and for people in Discord, in-game voice chat, or another app that can use a Windows recording device as its microphone input.

Start with local playback. Do not touch voice chat routing until the sound plays through your own headphones first.

## What Has To Happen

Voice chat apps and games can only hear a Windows recording device. A normal speaker output is not enough.

The working route looks like this:

```text
OpenLaunchDeck soundboard clip
  -> your headphones or audio interface so you can hear it
  -> voice route playback device
  -> matching Windows recording device
  -> Discord, game chat, or another voice app input device
  -> your call, party, lobby, or team chat
```

Your microphone also needs to go into that same route if the app or game is listening to the route instead of directly listening to your mic.

## Supported File Types

Use these first:

- `.wav`
- `.mp3`

Other formats may work depending on Windows and QtMultimedia, but `.wav` and `.mp3` are the safest choices.

## Step 1: Make Local Playback Work

1. Select a pad.
2. Set action type to `Play Sound`.
3. Choose a local `.wav` or `.mp3` file.
4. Set volume to `60`.
5. Set Already Playing to `restart`.
6. Leave `Route To Voice Chat` off for the first test.
7. Click **Test Action**.

If you do not hear it locally:

- Confirm the file exists.
- Try a different `.wav` or `.mp3`.
- Check Windows volume mixer.
- Check OpenLaunchDeck global soundboard volume.
- Confirm Default Output points to your real headphones, speakers, or audio interface.

## Step 2: Add A Stop Button

Before routing to voice chat, create a stop button:

1. Select a nearby pad.
2. Set label to `Stop`.
3. Set color to `red`.
4. Set action type to `Stop Sound`.
5. Set scope to `all`.

This makes testing safer if a clip loops or gets loud.

## Step 3: Pick The Voice Route

Open `Soundboard > Open Soundboard Panel`.

Recommended settings:

- **Default Output:** your real headphones, speakers, or audio interface.
- **Monitor Voice Routes:** on.
- **Voice Route Output:** the playback side of the route.
- **Microphone Input:** your real microphone.
- **Route Microphone:** on.
- **Microphone Volume:** start at `100`.
- **Global Volume:** start at `100`.

For a common cable-style route, Windows may show:

- Playback side: `Speakers (VB-Audio Virtual Cable)`
- Recording side: `CABLE Output (VB-Audio Virtual Cable)`

OpenLaunchDeck sends routed clips and the selected microphone to the playback side. Discord or a game listens to the recording side.

If a dedicated OpenLaunchDeck route endpoint exists, Auto Find Route prefers:

- `OpenLaunchDeck Voice Output`
- `OpenLaunchDeck Voice Input`

## Step 4: Enable Routing On The Button

For each clip voice chat should hear:

1. Select the soundboard pad.
2. Confirm action type is `Play Sound`.
3. Enable `Route To Voice Chat`.
4. Keep `Monitor Voice Routes` enabled in the Soundboard panel if you also want to hear it.
5. Start button volume around `50` to `70`.
6. Test again.

OpenLaunchDeck uses the same effective gain for the voice route and monitor route. If it is loud for your friends, it should be loud for you too.

## Step 5: Set The Voice Chat Input

In Discord, open `User Settings > Voice & Video`.

Set:

- **Input Device:** the route recording side, such as `CABLE Output (VB-Audio Virtual Cable)`.
- **Output Device:** your real headphones, speakers, or audio interface.
- **Input Profile:** `Custom` or `Studio`.
- **Noise Suppression:** `None`.
- **Echo Cancellation:** off.
- **Automatic Gain Control:** off if clips pump, get quiet, or sound crushed.
- **Bypass System Audio Input Processing:** on if available.

Do not set Discord output to the same route input. That can create feedback or make other app audio unstable.

Keep OpenLaunchDeck running while Discord or a game is using the route. When Route Microphone is enabled, closing the main window keeps OpenLaunchDeck alive in the tray and the app periodically restarts the microphone route if it is not running. Use `File > Quit` or the tray `Quit` action only when you intentionally want to stop the route.

For games with voice chat, set the game's microphone/input device to the same route recording side. If the game uses push-to-talk, hold push-to-talk while playing the routed soundboard clip. The game transmits whatever is in the route while push-to-talk is active, including your mic and routed soundboard clips.

## Step 6: Test The Route

Discord test:

1. Stay in Discord `Voice & Video`.
2. Start Mic Test.
3. Play a routed soundboard clip from OpenLaunchDeck.
4. Watch Discord's input meter.
5. Speak into your mic.
6. Confirm the meter moves for both your voice and the clip.

If the meter moves, Discord is receiving the route.

Game chat test:

1. Set the game's voice input/microphone to the route recording device.
2. Join a party, custom match, lobby, or other safe test channel.
3. Hold the game's push-to-talk key if push-to-talk is enabled.
4. Play a routed soundboard clip.
5. Ask someone to confirm they hear both your mic and the clip.

If other people still do not hear it, check whether you are muted, server-muted, push-to-talk is enabled, the game has voice chat disabled, or the app/game is using a different input device.

## Good Starting Volumes

Use this as a starting point:

- OpenLaunchDeck global soundboard volume: `100`
- Sound button volume: `50` to `70`
- Microphone route volume: `100`
- Windows route endpoint volume: `100`
- Voice chat input volume: `100`

If clips distort, lower the button volume first.

If clips are too quiet, raise the button volume before raising Windows endpoint volume.

## Repeated Press Behavior

Choose based on the sound:

- `restart`: best for short clips and memes.
- `toggle_stop`: best for music beds, loops, or long sounds.
- `ignore`: prevents spam when a clip is already playing.
- `overlap`: allows multiple copies at once. Use carefully.

## Sound Quality Fixes

If friends or teammates say the clip is bad, crushed, or barely audible:

1. Set the app/game input to the route recording device, not your mic.
2. In Discord, set Noise Suppression to `None`.
3. In Discord, turn Echo Cancellation off.
4. In Discord, turn Automatic Gain Control off if volume pumps up and down.
5. Use a clean `.wav` or high-quality `.mp3`.
6. Keep button volume below clipping.
7. Avoid using `overlap` with loud clips.

## Common Mistakes

- The button does not have `Route To Voice Chat` enabled.
- The app or game is still using the real microphone directly.
- OpenLaunchDeck Route Microphone is off.
- App/game output is accidentally routed into the input route.
- Noise suppression is set to Krisp or another aggressive mode.
- Push-to-talk is enabled and no push-to-talk key is being held.
- The wrong duplicate audio device was selected.
- The route playback endpoint exists, but the matching recording endpoint does not.

## Duplicate Audio Devices

Windows and audio drivers can expose duplicate output names. OpenLaunchDeck hides duplicate names and advanced mixer buses in the Soundboard and Settings selectors so the list stays usable.

If a saved device was already selected, OpenLaunchDeck keeps it instead of silently erasing it.
