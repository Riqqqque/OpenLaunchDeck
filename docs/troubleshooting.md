# Troubleshooting

## No Device Detected

Check USB connection, open `Device > MIDI Debug`, and confirm input/output ports are listed. If not, reconnect the Launchpad and press Reconnect.

## Pads Not Lighting

Confirm an output port is selected. Try Programmer Mode and press `Device > Reconnect`.

## Pad Presses Not Recognized

Open MIDI Debug and press a pad. If raw messages appear but parsed button IDs do not, run calibration.

## Wrong Pad Mapping

Use calibration and save the mapping. User mappings are stored in AppData.

## Sound Not Playing

Confirm the file exists and try `.wav` or `.mp3`. Check Windows volume mixer and the logs folder.

## Soundboard Not Heard In Discord

Route the playback device through an external virtual audio cable app. OpenLaunchDeck does not install audio drivers.

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
