# MIDI Mapping

The Launchpad grid is addressed as:

```text
A1 A2 A3 A4 A5 A6 A7 A8
B1 B2 B3 B4 B5 B6 B7 B8
C1 C2 C3 C4 C5 C6 C7 C8
D1 D2 D3 D4 D5 D6 D7 D8
E1 E2 E3 E4 E5 E6 E7 E8
F1 F2 F3 F4 F5 F6 F7 F8
G1 G2 G3 G4 G5 G6 G7 G8
H1 H2 H3 H4 H5 H6 H7 H8
```

Mapping code is isolated in `openlaunchdeck/devices/midi_mapping.py`. Device code asks the mapping for a button ID instead of hardcoding note numbers.

The default preset follows the common Launchpad Mini MK3 Programmer Mode note layout, with A1-A8 on notes 81-88 and H1-H8 on notes 11-18. Verify this with MIDI Debug because device mode and driver naming can affect behavior.

The Launchpad Mini MK3 also has navigation and scene-launch buttons outside the 8x8 grid. In Programmer Mode, those controls can send MIDI messages too, but OpenLaunchDeck does not bind them to previous/next page actions by default yet. Capture their raw messages in MIDI Debug before adding a built-in mapping.

User mappings are saved as JSON in:

`%APPDATA%\OpenLaunchDeck\midi_mappings`

## Editing And Verification

Open `Device > MIDI Debug` to see the current mapping table. The table shows each A1-H8 button, message type, MIDI number, and channel.

Use this flow for hardware verification:

1. Put the Launchpad Mini MK3 into Programmer Mode.
2. Open `Device > MIDI Debug`.
3. Press A1, A2, A3, and a few bottom-row pads.
4. Confirm incoming raw messages match the parsed button IDs.
5. If the mapping is wrong, run calibration and press each requested pad once.
6. Save the mapping.
7. Use Restore Default Mapping if the saved mapping should be reset.

Calibration stores raw message text and MIDI byte data in the debug log so contributors can compare reports without guessing.

## Lighting Output

The MVP uses note/control color values from a Programmer Mode palette preset. Exact Launchpad Mini MK3 RGB/SysEx behavior should be verified with hardware before a release claims full RGB certification.

Lighting updates are sent through `LaunchpadMiniMk3.set_many_pad_colors()` so page refreshes can be logged and batched. The lighting service skips refreshes when the computed page colors have not changed.

To update the built-in mapping, adjust `build_programmer_mode_mapping()` and include raw MIDI evidence from the debug window.
