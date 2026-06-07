# Soundboard and Discord Routing

OpenLaunchDeck can play local sound files from macro buttons and route selected clips toward Discord or a game voice chat.

Supported formats depend on Windows and QtMultimedia, but `.wav` and `.mp3` are the safest choices.

Start with local playback first. After local playback works, add Discord routing.

## Add a Sound Button

1. Select a pad.
2. Set action type to `Play Sound`.
3. Choose a local `.wav` or `.mp3` file.
4. Set volume.
5. Choose behavior for repeated presses:
   - `restart`
   - `overlap`
   - `ignore`
   - `toggle_stop`

Use `Stop Sound` to stop one button, the current page, or all sounds.

## Recommended Sound Settings

For short stream sounds:

- Format: `.wav` or high-quality `.mp3`
- Button volume: start around `60` to `80`
- Global volume: start around `80` to `100`
- Already playing: `restart`
- Loop: off

For long sounds:

- Already playing: `toggle_stop`
- Add a Stop Sound button nearby
- Avoid `overlap` unless you want multiple copies at once

OpenLaunchDeck uses the same effective gain for the Discord route and your local monitor route.

## Simple Voice Route

OpenLaunchDeck handles the routing split itself:

1. Routed soundboard buttons play to **Voice Route Output**.
2. If **Monitor Voice Routes** is enabled, the same clip also plays to your normal output.
3. If **Route Microphone** is enabled, your selected mic also plays into the voice route.
4. The routed and monitored copies use the same OpenLaunchDeck volume.
5. The Soundboard panel checks whether Discord has a matching recording input to use.

Discord can only receive audio through a Windows recording device. OpenLaunchDeck can mix and play your mic and routed clips, but Windows still needs a playback-to-recording bridge endpoint or hardware loopback.

For a simple signed cable endpoint pair, Windows may show:

- Playback: `Speakers (VB-Audio Virtual Cable)`
- Recording: `CABLE Output (VB-Audio Virtual Cable)`

In that setup, OpenLaunchDeck sends routed clips and the selected microphone to the playback side. Discord uses the recording side as its input.

OpenLaunchDeck now looks for a dedicated bridge pair:

- `OpenLaunchDeck Voice Output`
- `OpenLaunchDeck Voice Input`

When both endpoints exist, Auto Find Route prefers them.

## Set Up Discord

Open `Soundboard > Open Soundboard Panel`.

1. Keep **Default Output** on `System default`.
2. Leave **Monitor Voice Routes** enabled.
3. Click **Auto Find Route**.
4. If the panel shows `Discord input: ...`, click **Copy Discord Input**.
5. Set **Microphone Input** to your real mic, or leave it on `System default microphone`.
6. Enable **Route Microphone**.
7. Start **Microphone Volume** around `100`, then lower it if Discord clips.
8. Open Discord `User Settings > Voice & Video`.
9. Set **Input Device** to the copied device.
10. Keep **Output Device** on your real headphones, speakers, or audio interface.

For each soundboard button Discord should hear:

1. Select the button.
2. Set action type to `Play Sound`.
3. Choose the local audio file.
4. Enable `Route To Voice Chat`.
5. Start with volume around `60` to `80`.
6. Use `toggle_stop` if you want a second press to stop the sound.

## Discord Quality Checklist

In Discord `Voice & Video`, try turning off:

- Noise suppression
- Echo cancellation
- Noise reduction
- Automatic gain control

Then use Mic Test while playing a routed soundboard clip.

If the clip is quiet, raise the OpenLaunchDeck button volume or lower Discord input sensitivity.

If the clip is distorted, lower the OpenLaunchDeck button volume and use a cleaner `.wav` or high-quality `.mp3` file.

## Common Mistakes

- The button does not have `Route To Voice Chat` enabled.
- Discord input does not match the input shown by OpenLaunchDeck.
- **Route Microphone** is off while Discord is listening to the route input.
- Discord output is routed back into the same input Discord is using.
- Discord input sensitivity is too high, so the clip does not open voice activity.
- Windows does not currently expose a matching recording endpoint for the selected voice route.

## Output Device List

Windows and audio drivers can expose duplicate output names. OpenLaunchDeck hides duplicate names and advanced mixer buses in the Soundboard and Settings selectors so the list stays usable.

If a duplicate device ID was already saved, OpenLaunchDeck keeps that saved device instead of silently erasing it.
