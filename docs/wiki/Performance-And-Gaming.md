# Performance And Gaming

OpenLaunchDeck is designed to stay light while games, OBS, Discord, and audio routing software are running.

## What The App Does To Stay Responsive

- MIDI callbacks do minimal work.
- Actions run through a worker queue when they may block.
- Hotkeys, text entry, and media keys use the lightweight Windows input path.
- OBS and network operations use timeouts.
- Lighting updates skip pads that did not change.
- Rapid lighting changes are coalesced and flashes share one scheduler.
- Sound playback uses QtMultimedia instead of loading whole files into memory.
- File logging runs through a background queue instead of blocking button dispatch.
- Profile edits are saved in short batches instead of writing JSON for every keystroke.
- The Windows process stays at Normal priority so games keep scheduler priority.
- Hidden or minimized windows skip unnecessary grid/status repaints.
- Background health checks use coarse, low-frequency timers.
- Performance logs are quiet by default.

## Best Settings For Gaming

Recommended starting point:

- Keep performance logging off unless troubleshooting.
- Keep the app minimized or use Focus Grid while playing if you do not need the editor visible.
- Use OBS WebSocket for clips and screenshots instead of game hotkeys when possible.
- Use `F13` through `F24` for hotkeys that should not conflict with normal keyboard keys.
- Avoid huge sound files for short soundboard clips.
- Keep duplicate or looping sounds under control with `toggle_stop` or `ignore`.

## In-Game Hotkeys

Some games block synthetic keyboard input, especially if the game runs elevated or uses strict input handling.

If a game hotkey is unreliable:

1. Run OpenLaunchDeck and the game at the same privilege level.
2. Try an extended key such as `F15`.
3. Bind the game or OBS action to that key.
4. Prefer OBS WebSocket for replay buffer clips and screenshots.

For OBS replay buffer, use operation `save_replay_buffer`.

For OBS screenshots, use operation `save_screenshot`.

## Soundboard Performance

Good soundboard habits:

- Use `.wav` for lowest decoding overhead when file size is reasonable.
- Use high-quality `.mp3` for longer clips.
- Keep clip volume below clipping.
- Do not enable `overlap` on long clips unless you really need layered playback.
- Use Stop All Sounds if a test gets messy.

## When To Enable Performance Logging

Enable performance logging only while troubleshooting.

It helps measure:

- MIDI receive timing
- Button press to action dispatch
- Action duration
- Lighting refresh duration
- Sound trigger latency
- Update check duration

After testing, turn it off again so normal logs stay clean.
