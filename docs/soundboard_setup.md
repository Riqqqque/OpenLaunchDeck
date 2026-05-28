# Soundboard Setup

OpenLaunchDeck uses QtMultimedia when available. Supported formats depend on Windows codecs and the installed Qt backend, but `.wav` and `.mp3` are the safest choices. `.ogg` is accepted and may work when the platform backend supports it.

Each play sound button supports:

- File path
- Volume
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

## Output Device

The Soundboard panel lists QtMultimedia output devices when Windows exposes them. If a selected device cannot be used, playback falls back to the system default output.

Global soundboard volume is combined with each button's per-sound volume. For example, 50% global volume and 80% button volume play at 40% effective output.

## Soundboard Panel

Open `Soundboard > Open Soundboard Panel` to view currently playing sounds, stop all sounds, select the default output device, adjust global volume, refresh the list, or open this setup document.

## Discord And Game Chat

To let Discord or a game hear soundboard playback, route audio through external virtual audio cable software and select that cable as the output device. OpenLaunchDeck does not install or bundle audio drivers, and it does not make Discord/game voice routing work automatically.

## Troubleshooting

If sound does not play, confirm the file exists, try a `.wav` or `.mp3`, check Windows volume mixer, check the selected output device, and open the logs folder from the Help menu.
