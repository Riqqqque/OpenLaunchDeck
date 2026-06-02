# Soundboard and Discord Routing

OpenLaunchDeck can play local sound files from macro buttons.

Supported formats depend on Windows and QtMultimedia, but `.wav` and `.mp3` are the safest choices.

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

## Discord Routing

OpenLaunchDeck does not install virtual audio drivers. To let people in Discord hear soundboard clips while you still hear them, use external routing software such as Voicemeeter or another virtual audio cable setup.

Typical routing idea:

1. Send OpenLaunchDeck soundboard output to a virtual input.
2. Route that virtual input to your headphones so you can hear it.
3. Route that virtual input into Discord's microphone/input path so friends can hear it.
4. Keep your real microphone routed into Discord too.

If friends cannot hear clips, check Discord input device, Voicemeeter routing buttons, Windows app volume routing, and the soundboard output device in OpenLaunchDeck settings.

If the audio sounds bad, lower clip volume, avoid clipping in Voicemeeter, and make sure Discord noise suppression is not crushing the soundboard audio.
