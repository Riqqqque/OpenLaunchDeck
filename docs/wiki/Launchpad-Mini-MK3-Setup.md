# Launchpad Mini MK3 Setup

OpenLaunchDeck uses USB MIDI to receive pad presses and send RGB lighting to a Novation Launchpad Mini MK3.

## Connect The Device

1. Connect the Launchpad directly to USB.
2. Open OpenLaunchDeck.
3. Click **Reconnect** or use **Device > Connect**.
4. Check the header connection status.

**Connected** means both selected ports opened successfully. **Simulation mode** means no usable MIDI pair is active; editing and Test Action still work.

## Pick The Correct Windows Ports

Windows may expose more than one interface:

```text
LPMiniMK3 MIDI
MIDIIN2 (LPMiniMK3 MIDI)
MIDIOUT2 (LPMiniMK3 MIDI)
```

The second MIDI interface is normally used for programmer control. OpenLaunchDeck prefers it automatically.

If the app says Connected but no pad presses arrive:

1. Open **Device > MIDI Debug**.
2. Check the selected input and output names.
3. Disconnect.
4. Choose the other Launchpad MIDI pair in Settings.
5. Connect again.

## Programmer Mode

Programmer Mode gives predictable grid note messages and RGB control. OpenLaunchDeck sends the Launchpad Mini MK3 Programmer Mode command when it connects and restores Live Mode when it closes the MIDI port.

Device firmware and mode can still affect messages. Use MIDI Debug and calibration instead of assuming a note number.

## Verify The Grid

Open **Device > MIDI Debug**, then press:

| Physical pad | Expected button ID |
| --- | --- |
| Top-left | `A1` |
| Top-right | `A8` |
| Bottom-left | `H1` |
| Bottom-right | `H8` |

The debug window should show the raw MIDI message and parsed button ID. The matching GUI pad should react.

## MIDI Debug

The window shows:

- Available input and output ports
- Selected input and output
- Live incoming messages
- Logged outgoing lighting messages
- Raw status, note/control, and value data
- Parsed button ID when recognized
- Calibration state

Use **Clear Log** before a focused test and **Save Log** when a hardware report needs exact messages.

Close MIDI Debug during normal gaming or streaming. Its live display is intentionally more active than the normal background path.

## Calibrate A Custom Mapping

Use calibration when raw messages arrive but the parsed cell is wrong.

1. Open **Device > MIDI Debug**.
2. Start calibration.
3. Read the requested button ID.
4. Press that physical pad once.
5. Wait for the next requested ID.
6. Continue through the requested grid.
7. Save the mapping.
8. Reconnect and repeat the corner-pad test.

Custom mappings are stored under:

```text
%APPDATA%\OpenLaunchDeck\midi_mappings
```

Use **Restore Default Mapping** if the custom mapping is incomplete or worse than the built-in map.

## Lighting Feedback

OpenLaunchDeck can:

- Set individual pad colors
- Clear all pads
- Refresh the active page
- Flash white on press
- Flash green after success
- Flash red after failure
- Blink an armed dangerous button
- Show the active color while a sound is playing

Page refreshes send changed pads in batches and avoid resending colors that are already active.

Lighting confirms what the app attempted to send. If colors are wrong on real hardware, capture outgoing messages and device mode in MIDI Debug before changing the palette or protocol.

## Unplug And Reconnect

The MIDI callback does minimal parsing and never updates widgets directly. A low-frequency background health check detects stale Windows handles and reconnects when auto-connect is enabled.

If unplugging does not recover automatically:

1. Wait a few seconds.
2. Reconnect USB.
3. Click **Reconnect** once.
4. Confirm ports in MIDI Debug.

## Extra Hardware Buttons

Programmer Mode exposes 16 controls outside the grid. Their default assignments are:

| Hardware control | Default action |
| --- | --- |
| Left / Right | Previous / next page |
| Up / Down | Previous / next profile |
| Session | Open the profile's default page |
| User | Stop all sounds |
| Scene 1-8 | Open page 1-8 |
| Drums / Keys | Unassigned |

Open **Settings > Launchpad > Hardware Buttons** to change any assignment. Available choices include page/profile navigation, a numbered page, the default page, Stop All Sounds, and Do Nothing.

The Hardware Controls tab in MIDI Debug lists the exact Programmer Mode CC values. Press each control and confirm its parsed name before a live workflow, especially after another MIDI application has changed the Launchpad mode.

## Still Not Working?

Open [Troubleshooting](Troubleshooting.md) and use the Launchpad section. Include selected ports, mode, raw messages, parsed IDs, and whether restoring the default mapping changes the result.
