# Soundboard and Discord Routing

OpenLaunchDeck can play local sound files from macro buttons.

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
- Button volume: `60` to `80`
- Global volume: `80` to `100`
- Already playing: `restart`
- Loop: off

For long sounds:

- Already playing: `toggle_stop`
- Add a Stop Sound button nearby
- Avoid `overlap` unless you want multiple copies at once

## Output Device List

Windows and virtual audio software can expose the same visible output name many times. VoiceMeeter can also expose advanced buses such as `Voicemeeter In 1` through `Voicemeeter In 5`.

OpenLaunchDeck hides duplicate names and those advanced VoiceMeeter buses in the Soundboard and Settings selectors so the list stays usable. The useful routes, such as `Voicemeeter Input`, `Voicemeeter AUX Input`, real headphones, and audio interfaces remain visible.

If a duplicate device ID was already saved, OpenLaunchDeck keeps that saved device instead of silently erasing it.

If Windows itself still shows many duplicate outputs, reboot after installing VoiceMeeter, then disable unused endpoints in Windows Sound Settings if Windows exposes them separately.

## Discord Routing

OpenLaunchDeck does not install virtual audio drivers. To let people in Discord hear soundboard clips while you still hear them, use external routing software such as Voicemeeter or another virtual audio cable setup.

Typical routing idea:

1. Send OpenLaunchDeck soundboard output to a virtual input.
2. Route that virtual input to your headphones so you can hear it.
3. Route that virtual input into Discord's microphone/input path so friends can hear it.
4. Keep your real microphone routed into Discord too.

## VoiceMeeter Banana Example

One practical setup:

- Windows output: `Voicemeeter AUX Input`
- Windows input: `Voicemeeter Out B1`
- Discord output: `Voicemeeter AUX Input`
- Discord input: `Voicemeeter Out B1`
- OpenLaunchDeck default output: `Voicemeeter AUX Input`
- OpenLaunchDeck voice-chat output: `Voicemeeter Input`
- OpenLaunchDeck monitor voice routes: off

In VoiceMeeter:

- Set Hardware Out `A1` to your real headphones or audio interface.
- Route your microphone to `B1`.
- Route `Voicemeeter Input` to `A1` and `B1`.
- Route `Voicemeeter AUX` to `A1` only.

This lets friends hear routed soundboard clips while preventing Discord from hearing itself.

If friends cannot hear clips, check Discord input device, Voicemeeter routing buttons, Windows app volume routing, and the soundboard output device in OpenLaunchDeck settings.

If the audio sounds bad, lower clip volume, avoid clipping in Voicemeeter, and make sure Discord noise suppression is not crushing the soundboard audio.

## Discord Quality Checklist

In Discord `Voice & Video`, try turning off:

- Noise suppression
- Echo cancellation
- Noise reduction
- Automatic gain control

Then use Mic Test while playing a soundboard clip.

If the clip is quiet, raise the OpenLaunchDeck button volume or the VoiceMeeter strip a little.

If the clip is distorted, lower the OpenLaunchDeck button volume or the VoiceMeeter strip.

## Common Mistakes

- Discord output goes to real headphones instead of the VoiceMeeter AUX route.
- The soundboard route goes to headphones only, not the Discord input bus.
- Discord input sensitivity is too high, so the clip does not open voice activity.
- VoiceMeeter is not running after reboot.
- Monitor voice routes is on while VoiceMeeter is already monitoring locally, causing two copies of the same clip.
