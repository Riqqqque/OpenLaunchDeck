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

The default preset follows the Launchpad Mini MK3 Programmer Mode note layout, with A1-A8 on notes 81-88 and H1-H8 on notes 11-18. Verify this with MIDI Debug because device mode and driver naming can affect behavior.

The extra Programmer Mode controls use fixed CC addresses:

| Control | CC | Default OpenLaunchDeck assignment |
| --- | ---: | --- |
| Up | 91 | Previous profile |
| Down | 92 | Next profile |
| Left | 93 | Previous page |
| Right | 94 | Next page |
| Session | 95 | Default page |
| Drums | 96 | Do nothing |
| Keys | 97 | Do nothing |
| User | 98 | Stop all sounds |
| Scene 1-8 | 89, 79, 69, 59, 49, 39, 29, 19 | Open page 1-8 |

Change these assignments under **Settings > Launchpad > Hardware Buttons**. Grid calibration does not rewrite these fixed Programmer Mode CCs.

User mappings are saved as JSON in:

`%APPDATA%\OpenLaunchDeck\midi_mappings`

## Editing And Verification

Open `Device > MIDI Debug` to see the current mapping table. The Pad Mapping tab shows each A1-H8 button, message type, MIDI number, and channel. The Hardware Controls tab shows every fixed CC and current button name.

Use this flow for hardware verification:

1. Put the Launchpad Mini MK3 into Programmer Mode.
2. Open `Device > MIDI Debug`.
3. Press A1, A2, A3, and a few bottom-row pads.
4. Confirm incoming raw messages match the parsed button IDs.
5. If the mapping is wrong, run calibration and press each requested pad once.
6. Save the mapping.
7. Use Restore Default Mapping if the saved mapping should be reset.

Press the four arrows and Scene 1-8 while the Live Messages tab is open. The Parsed field should name the hardware control. If it does not, confirm Programmer Mode and the selected second MIDI interface before reporting a mapping problem.

Calibration stores raw message text and MIDI byte data in the debug log so contributors can compare reports without guessing.

## Lighting Output

Lighting uses the documented Programmer Mode palette values. Hardware behavior can vary by mode, so use MIDI Debug to verify incoming and outgoing messages before relying on a custom mapping live.

Single changes use the pad's note or control address. Multi-pad refreshes use one Programmer Mode lighting SysEx containing changed LED/color pairs. The lighting service caches the last sent state and skips colors that have not changed.

To update the built-in mapping, adjust `build_programmer_mode_mapping()` and include raw MIDI evidence from the debug window.
