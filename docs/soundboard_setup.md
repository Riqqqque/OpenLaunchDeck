# Soundboard Setup

OpenLaunchDeck uses QtMultimedia when available. Supported formats depend on Windows codecs and the installed Qt backend, but `.wav` and `.mp3` are the safest choices. `.ogg` is accepted and may work when the platform backend supports it.

Each play sound button supports:

- File path
- Volume
- Voice chat routing
- Looping
- Already-playing behavior
- Active lighting color
- Stop on page change

Missing files are reported before playback starts. Unknown file extensions are rejected with a clear error instead of being sent to the audio backend.

## Already Playing Behavior

`behavior_when_already_playing` controls what happens when a sound assigned to the same button is already active:

- `restart`: stop the current instance and start it again.
- `overlap`: start another instance.
- `ignore`: keep the current sound running.
- `toggle_stop`: stop the current sound.

## Stopping Sounds

The Stop Sound action supports:

- `this_button`
- `current_page`
- `all`

The Soundboard panel also has a Stop All Sounds button.

## Output Devices

The Soundboard panel lists QtMultimedia output devices when Windows exposes them. If a selected device cannot be used, playback fails with a clear message instead of silently playing through the wrong output.

Use `System default` for normal soundboard monitoring unless you have a specific reason to pin a hardware device. Use the voice-chat output selector for virtual mixer routes such as `Voicemeeter Input`.

Windows and virtual audio software can expose multiple outputs with the exact same visible name. VoiceMeeter can also expose advanced virtual buses such as `Voicemeeter In 1` through `Voicemeeter In 5`.

OpenLaunchDeck hides duplicate names and those advanced VoiceMeeter buses in the Soundboard and Settings selectors so normal setups stay readable. The useful routes, such as `Voicemeeter Input`, `Voicemeeter AUX Input`, real headphones, and audio interfaces remain visible. If a hidden device ID was already saved, the app keeps the saved ID instead of silently changing it.

Global soundboard volume is combined with each button's per-sound volume, then applied with a quieter curve so low values stay low. For example, 50% global volume and 80% button volume combine to a 40% raw setting and play at about 16% output gain. A button set to 0% stays silent.

When `Route To Voice Chat` is enabled, OpenLaunchDeck applies the same effective gain to the voice-chat output and the local monitor output. If Discord is louder or quieter than your local monitor after that, check the virtual mixer strip level, Discord input processing, and the Windows volume mixer.

## Soundboard Panel

Open `Soundboard > Open Soundboard Panel` to view currently playing sounds, stop all sounds, select the default output device, select the voice chat output device, choose whether routed sounds are monitored locally, adjust global volume, refresh the list, or open this setup document.

## Discord And Game Chat

To let Discord or a game hear soundboard playback, use external virtual audio cable software. OpenLaunchDeck does not install or bundle audio drivers.

Typical setup:

1. Install a virtual audio cable app.
2. Keep Windows output on your real headphones, speakers, or audio interface.
3. In OpenLaunchDeck, open the Soundboard panel and leave `Default Output` on `System default`.
4. Set `Voice Chat Output` to the virtual cable playback device.
5. Leave `Monitor Voice Routes` enabled if you still want to hear routed sounds through your normal output.
6. In Discord or the game, set the microphone/input device to the matching virtual cable recording device.
7. On each sound button that should be heard in voice chat, enable `Route To Voice Chat`.

If no virtual cable output is selected, routed sound buttons show a clear error and do not play to the wrong device.

For a complete VoiceMeeter Banana setup that routes OpenLaunchDeck soundboard clips into Discord while still letting you hear your friends, see [Discord Voice Chat Routing](discord_voice_routing.md).

## Troubleshooting

If sound does not play, confirm the file exists, try a `.wav` or `.mp3`, check Windows volume mixer, check the selected output device, and open the logs folder from the Help menu.
