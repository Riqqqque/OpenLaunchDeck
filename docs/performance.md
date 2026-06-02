# Performance

The app is designed so button presses feel instant.

Key rules:

- MIDI callbacks only parse and emit lightweight events.
- MIDI callbacks do not update Qt widgets directly; they emit into Qt signals.
- MIDI connect and reconnect work runs outside the GUI thread.
- Blocking actions run through the action runner worker pool.
- The action runner limits queued background work so repeated presses cannot build an unlimited backlog.
- GUI updates happen on the Qt thread.
- Network calls use timeouts.
- Update checks and verified downloads run on Qt worker threads.
- Sound playback is started through non-blocking QtMultimedia APIs.
- Profile JSON stays small and human-readable.
- Page lighting refreshes are batched through the lighting service and sent through a single background output worker.
- Lighting refreshes skip redundant pad updates when the page state has not changed.
- Grid cells skip text and stylesheet updates when their visible state has not changed.
- Normal successful button presses do not write action logs at the default logging level.
- Live MIDI debug UI callbacks stay disabled until the MIDI Debug window is opened.
- Performance logging can be enabled in Settings when troubleshooting latency.

## Performance Monitor

`PerformanceMonitor` is a lightweight timing helper used across the app. It records recent timing samples only when performance logging is enabled. When disabled, it avoids sample storage and only emits debug-level timing logs if debug logging is actually enabled.

Current timing points include:

- App startup and main window creation
- Raw MIDI receive and message parsing
- Button press to action dispatch
- Action execution duration
- Lighting refresh and flash duration
- Sound playback trigger latency
- Update manifest fetch and download/checksum timing

## MIDI Timing Logs

MIDI and lighting timing details are logged at debug level or when debug logging is enabled:

- Raw MIDI receive timestamp
- Parsed button event time
- Action dispatch time
- Lighting feedback and page refresh time

Normal usage keeps these logs quiet. Enable MIDI debug logging or performance logging only while diagnosing latency.

The MIDI Debug window is also treated as an on-demand diagnostic tool. Incoming and outgoing MIDI messages are not forwarded into the debug UI while the window is closed, which keeps background MIDI handling small during a game or stream.

## Game And Stream Use

Recommended low-impact defaults:

- Leave performance logging off unless diagnosing a problem.
- Leave MIDI debug logging off unless calibrating or troubleshooting hardware.
- Leave startup update checks off while streaming if you want the quietest launch path.
- Keep long command, HTTP, SSH, or script actions configured with timeouts.
- Prefer short macros and avoid stacking many slow actions on one pad.

OpenLaunchDeck should stay idle most of the time: no hardware means simulation mode with no MIDI polling, connected hardware uses MIDI callbacks instead of polling loops, and update checks only run when enabled or requested.

## Update Performance

Manual and startup update checks use worker threads so startup and the main window stay responsive. Installer downloads stream to `%APPDATA%\OpenLaunchDeck\updates` in chunks, then checksum verification runs before the installer is made available.

## Soundboard Performance

Sound playback is started through QtMultimedia and does not load entire sound files into Python memory. The audio engine performs lightweight file checks and caches metadata such as name, extension, size, and modified time when a sound is played.

Sound action start latency is logged at debug level, or at info level when performance logging is enabled. The Soundboard panel refreshes the current playback list on a lightweight timer and can be refreshed manually.

Per-sound volume and global soundboard volume are combined before playback. Existing playback instances are tracked by button and page so Stop Sound can stop one button, one page, or all sounds without scanning profile files. Voice-chat routing starts a second playback instance only for sounds that explicitly enable `Route To Voice Chat`.

## Native Acceleration

The app runs without Rust. The `native/` folder contains an optional PyO3/maturin helper for small CPU-bound utilities:

- `validate_button_id`
- `button_id_to_index`
- `index_to_button_id`
- `calculate_profile_hash`
- `verify_sha256`

The Python wrapper in `openlaunchdeck/native_acceleration.py` always provides fallback implementations. If the native module is missing, disabled, or cannot be imported, OpenLaunchDeck keeps running with Python code.

To build the native helper for local testing:

```powershell
powershell -ExecutionPolicy Bypass -File build.ps1 -BuildNative
```

The default build does not require Rust:

```powershell
powershell -ExecutionPolicy Bypass -File build.ps1
```

Use native acceleration only for focused helpers where it measurably helps. The GUI, MIDI orchestration, actions, audio, updates, and profile editing stay in Python/PySide6.
