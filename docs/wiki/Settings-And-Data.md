# Settings And Data

Open **Settings > Settings** to change application, MIDI, soundboard, update, and performance behavior.

## Appearance

| Setting | Meaning |
| --- | --- |
| Theme | Midnight, OLED Black, Galaxy OLED, Arctic White, Graphite, Broadcast, High Contrast, or Follow Windows |
| Grid density | Compact, comfortable, or large pad sizing |
| Open in Deck View | Start with the grid using nearly the entire app window |

Theme changes preview immediately and revert when Settings is canceled. Use Compact for a narrow utility window and Large when the grid is the main second-monitor view. The grid still fits all 64 pads within the available width and height.

Settings are organized into **Appearance**, **Launchpad**, **Soundboard**, **App**, and **Advanced** tabs so unrelated controls do not compete for space.

## Window And Startup

| Setting | Meaning |
| --- | --- |
| Start minimized | Normal launches begin without showing the main window |
| Minimize to tray | Closing/minimizing can keep the background process active |
| Launch at startup | Adds a current-user Windows startup entry |

The startup entry uses background mode and does not require administrator rights. OpenLaunchDeck repairs its startup command when the installed path changes.

Use **File > Quit** or the tray **Quit** action when you need to stop hardware handling and audio routing completely.

## MIDI

| Setting | Meaning |
| --- | --- |
| Auto-connect | Scan and connect to the saved or likely Launchpad ports |
| MIDI input port | Saved input port name |
| MIDI output port | Saved output port name |
| MIDI debug logging | Write detailed MIDI traffic to logs |
| Hardware Buttons | Assign the arrows, mode controls, and Scene 1-8 in Programmer Mode |

Leave the port fields empty for automatic selection. Use exact port names only when automatic selection chooses the wrong Windows interface.

MIDI debug logging can be noisy. Enable it while diagnosing a mapping or lighting problem, then turn it off.

Hardware-button choices include adjacent page/profile navigation, numbered pages, the default page, Stop All Sounds, and Do Nothing. These assignments do not change the A1-H8 custom calibration map.

## Profiles

| Setting | Meaning |
| --- | --- |
| Profile autosave | Save profile edits automatically after a short debounce |
| Automatic backups | Copy profiles into the backups folder before update-sensitive work |

Profiles are human-readable JSON. Importing and exporting does not move external sound files or applications referenced by a profile.

## Soundboard And Voice Routing

| Setting | Meaning |
| --- | --- |
| Sound output device | Local listening output; system default is recommended |
| Voice route output device | Output that feeds the recording route used by chat |
| Voice route microphone | Microphone mixed into the route |
| Route microphone to voice | Starts/stops microphone forwarding into the voice route |
| Voice microphone volume | Gain applied to the routed microphone |
| Monitor voice routes | Also play voice-routed clips to the normal listening output |
| Soundboard volume | Global gain applied with each button's volume |
| Stop sounds on exit | Stop active sounds during a complete application exit |

Duplicate Windows output names and advanced mixer buses may be hidden from selectors. A saved device that is temporarily unavailable remains visible as unavailable so the setting is not silently lost.

See [Soundboard and Voice Chat](Soundboard-and-Discord-Routing.md) before changing voice-route settings.

## Updates

| Setting | Meaning |
| --- | --- |
| Check updates on startup | Run a quiet background check after launch |
| Update channel | Stable or beta manifest channel |
| Update manifest URL | Optional custom manifest; leave empty for normal GitHub releases |

Startup failures are logged without interrupting normal startup. Manual checks under **Help > Check for Updates** show full results.

Do not use a custom manifest URL unless you control and trust it.

## Performance

| Setting | Meaning |
| --- | --- |
| Performance logging | Record detailed latency timings for troubleshooting |
| Native acceleration | Use the optional native helper when it is installed |

Both are off by default. Performance logging adds log traffic and should be disabled after diagnosis. Native acceleration is optional; Python fallbacks provide the same behavior.

## User Data Folder

Open the folder from the **Config folder** button in Settings:

```text
%APPDATA%\OpenLaunchDeck
```

| Path | Contents |
| --- | --- |
| `settings.json` | Application settings |
| `profiles` | User profile JSON files |
| `logs` | Application logs |
| `backups` | Automatic profile backups |
| `midi_mappings` | Saved calibration mappings |
| `imported_assets` | Assets imported by supported workflows; local sound buttons normally keep their original file paths |
| `updates` | Downloaded update files and metadata |

Program files belong in the install folder. User data never needs to be placed there.

## Backup And Restore

To make a complete manual backup:

1. Quit OpenLaunchDeck from the tray.
2. Copy `%APPDATA%\OpenLaunchDeck` to a safe location.
3. Restart the app.

To restore, quit the app and replace the affected files with known-good copies. Keep an extra copy before editing JSON manually.

## Moving A Profile To Another Computer

1. Export the profile from the source computer.
2. Copy any sound files, scripts, or applications it references separately.
3. Import the profile on the destination computer.
4. Update machine-specific paths and device selections.
5. Test every action before live use.

Profile exports can contain OBS passwords, webhook headers, server addresses, commands, and file paths. Review the JSON before sharing it.

## Logs And Diagnostics

Use:

- **Help > Open Logs Folder** for technical logs
- **Help > Copy Diagnostic Info** for version, Windows, MIDI, profile, mode, paths, install type, and native-helper status

Remove sensitive values before posting diagnostics publicly.
