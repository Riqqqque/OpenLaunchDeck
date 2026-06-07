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

Use `System default` for normal monitoring unless you have a specific reason to pin a hardware output. OpenLaunchDeck applies the same gain to every copy of a sound: local monitor playback and voice-routed playback stay matched.

Windows can expose duplicate output names. OpenLaunchDeck hides duplicates and advanced mixer buses in the normal selectors so the list stays readable. If a hidden device ID was already saved, the app keeps that saved ID instead of silently changing it.

Global soundboard volume is combined with each button's per-sound volume, then applied with a quieter curve so low values stay low. For example, 50% global volume and 80% button volume combine to a 40% raw setting and play at about 16% output gain. A button set to 0% stays silent.

## Simple Voice Route

OpenLaunchDeck has its own lightweight voice-route behavior:

1. A routed sound plays to the selected **Voice Route Output**.
2. If **Monitor Voice Routes** is enabled, the same sound also plays to your normal output so you hear it.
3. The routed and monitored copies use the same effective volume.
4. The Soundboard panel checks whether Windows exposes a matching recording input for Discord.

Discord and most games can only receive microphone audio from a Windows recording device. OpenLaunchDeck can mix and play the soundboard route itself, but Windows still needs a playback-to-recording bridge endpoint for Discord to select. The app does not install audio drivers.

Open `Soundboard > Open Soundboard Panel`:

1. Leave **Default Output** on `System default`.
2. Click **Auto Find Route**.
3. If a route is ready, OpenLaunchDeck shows `Discord input: ...`.
4. Click **Copy Discord Input**.
5. Set **Microphone Input** to your mic, or leave it on `System default microphone`.
6. Enable **Route Microphone**.
7. Set **Microphone Volume** so your voice is clear without clipping.
8. In Discord, open `User Settings > Voice & Video`.
9. Set **Input Device** to the copied device name.
10. Keep **Output Device** on your real headphones, speakers, or audio interface.
11. On each sound button Discord should hear, enable `Route To Voice Chat`.

If Auto Find Route says no route is ready, Windows does not currently expose a recording input that can receive OpenLaunchDeck's routed playback. Install a signed OpenLaunchDeck Audio Bridge package or use hardware loopback from an audio interface, then reopen the Soundboard panel and run Auto Find Route again.

## Microphone Route

The microphone route sends your selected mic into the same voice route output used by routed soundboard clips. This lets OpenLaunchDeck handle the voice mix directly:

- Your mic goes to the voice route.
- Routed clips go to the same voice route.
- Discord listens to the matching recording input.
- Discord output stays on your real headphones or speakers.

Only enable the microphone route when Discord is using the matching input shown by the Soundboard panel. If you leave Discord on your real microphone while also routing the mic through OpenLaunchDeck, Discord can receive the wrong source or duplicate audio.

## OpenLaunchDeck Audio Bridge

The Soundboard panel checks for `OpenLaunchDeck Voice Output` and `OpenLaunchDeck Voice Input`. When both endpoints exist, Auto Find Route prefers them.

The bridge is a driver-level component, so it is not installed by the normal app installer until a signed driver package is available. See [audio_bridge.md](audio_bridge.md).

## Discord Quality

For better soundboard quality in Discord, try turning off:

- Noise suppression
- Echo cancellation
- Noise reduction
- Automatic gain control

Use `.wav` or high-quality `.mp3` files where possible. Start button volume around `60` to `80` and adjust from there.

## Troubleshooting

If sound does not play, confirm the file exists, try `.wav` or `.mp3`, check Windows volume mixer, check the selected output device, and open the logs folder from the Help menu.
