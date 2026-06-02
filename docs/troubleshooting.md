# Troubleshooting

## No Device Detected

Check USB connection, open `Device > MIDI Debug`, and confirm input/output ports are listed. On Windows, look for names like `LPMiniMK3 MIDI`, `MIDIIN2 (LPMiniMK3 MIDI)`, or `MIDIOUT2 (LPMiniMK3 MIDI)`. If no ports appear, reconnect the Launchpad and press Reconnect.

## Pads Not Lighting

Confirm an output port is selected. Try Programmer Mode and press `Device > Reconnect`.

## Pad Presses Not Recognized

Open MIDI Debug and press a pad. If raw messages appear but parsed button IDs do not, run calibration. If no raw messages appear but the app says connected, reconnect after closing other MIDI apps and make sure the selected input is the second Launchpad MIDI interface, such as `MIDIIN2 (LPMiniMK3 MIDI)` or `LPMiniMK3 MIDI 1`.

## Wrong Pad Mapping

Use calibration and save the mapping. User mappings are stored in AppData.

## Sound Not Playing

Confirm the file exists and try `.wav` or `.mp3`. Check Windows volume mixer and the logs folder.

## Soundboard Not Heard In Discord

Route the playback device through an external virtual audio cable app. OpenLaunchDeck does not install audio drivers.

For Discord with VoiceMeeter Banana, use this baseline route:

- Windows output: `Voicemeeter AUX Input`
- Windows input: `Voicemeeter Out B1`
- Discord output: `Default` or `Voicemeeter AUX Input`
- Discord input: `Default` or `Voicemeeter Out B1`
- OpenLaunchDeck voice-chat output: `Voicemeeter Input`

In VoiceMeeter, route the main virtual input strip to `A1` and `B1`, and route the AUX strip to `A1` only. If Discord output is sent directly to the real headphones while VoiceMeeter is using that device as `A1`, Discord playback may fail or friends may not be audible.

See [Discord Voice Chat Routing](discord_voice_routing.md) for the full step-by-step setup.

## Soundboard Sounds Bad In Discord

If friends say routed soundboard clips are muffled, crunchy, or underwater, Discord is usually processing the clip like microphone noise. In `User Settings > Voice & Video`, try turning off noise suppression, echo cancellation, noise reduction, and automatic gain control. Use `.wav` or high-quality `.mp3` files where possible.

If friends can barely hear clips, raise the per-button volume in OpenLaunchDeck first. Start around `60` to `80`. Also check that the VoiceMeeter strip carrying soundboard audio is near `0 dB`.

## Command Action Not Working

Enable `wait` on the command action to capture an exit code. Check the working directory and logs.

## App Will Not Start

Run from a terminal with:

```powershell
python -m openlaunchdeck.main
```

Then check `%APPDATA%\OpenLaunchDeck\logs`.

## Update Check Fails

Confirm the update manifest URL is configured and reachable. The manifest must include a valid 64-character SHA256 checksum.

## Installer Update Fails

Download the installer manually. User data remains in AppData.

## App Feels Slow

Enable performance logging in Settings, reproduce the issue, and inspect the logs.
