# Performance And Gaming

OpenLaunchDeck is designed to stay responsive without competing with games, OBS, audio, or GPU scheduling.

## Normal Behavior

- The Windows process runs at Normal priority.
- MIDI callbacks do minimal parsing and queue events.
- Commands, OBS, HTTP, SSH, updates, and other blocking work use background workers.
- Hotkeys, text, media controls, and volume controls use focused Windows paths.
- RGB messages skip unchanged pads and coalesce rapid feedback.
- Sound files stream through QtMultimedia instead of loading whole files into memory.
- Profile writes are debounced.
- File logging uses a queue.
- Hidden/minimized windows avoid unnecessary grid and status repaints.
- MIDI Debug updates only while its window is open.
- Detailed performance logging is off by default.

## Recommended Gaming Setup

- Keep Performance logging off unless diagnosing latency.
- Close MIDI Debug after hardware setup.
- Minimize the app or use **Focus Launchpad Grid** when the editor is not needed.
- Use OBS WebSocket for replay clips and screenshots instead of relying on a game to accept a hotkey.
- Use unused extended keys such as `F13` through `F24` for global bindings.
- Avoid `overlap` for long soundboard clips unless layering is intentional.
- Keep one Stop All Sounds button available.

## Hotkeys In Games

If a desktop hotkey works but a game ignores it:

1. Confirm the physical pad reaches OpenLaunchDeck in MIDI Debug.
2. Run OpenLaunchDeck and the game at the same privilege level.
3. Try borderless fullscreen.
4. Bind an unused key such as `F15` in both places.
5. Use the target application's direct integration when available.

Some anti-cheat or input systems intentionally reject synthetic keyboard input. OpenLaunchDeck does not bypass those protections.

## Soundboard Performance

- Use short `.wav` clips for predictable low decode latency.
- Use good-quality `.mp3` files for longer audio.
- Avoid huge files for short effects.
- Prefer `restart`, `ignore`, or `toggle_stop` over uncontrolled overlap.
- Lower the button volume when a clip clips or distorts.

## Performance Logging

Enable it under **Settings > Settings > Performance logging** only while troubleshooting.

It records timings for:

- Raw MIDI receive and parsed button event
- Button press to action dispatch
- Action execution
- Lighting feedback
- Sound trigger latency
- Update checks

Turn it off after collecting the needed log so normal operation stays quiet.

## Check Resource Use

Open Windows Task Manager and observe OpenLaunchDeck while it is idle, while rapidly pressing pads, and while playing a sound. A brief change during an action is expected; sustained CPU, memory growth, repeated child processes, or constant disk activity is worth reporting.

Include diagnostic info, the active action type, and whether MIDI Debug or performance logging was open.

## Optional Native Helper

The optional native module provides focused mapping, hashing, and checksum helpers. It is not required for normal latency or correctness, and no general performance improvement is claimed without workload-specific measurement. Python fallbacks remain active when it is unavailable.
