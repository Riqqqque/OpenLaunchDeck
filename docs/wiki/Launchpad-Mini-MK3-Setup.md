# Launchpad Mini MK3 Setup

OpenLaunchDeck targets the Novation Launchpad Mini MK3 over USB MIDI.

## Connect the Device

1. Plug the Launchpad Mini MK3 into USB.
2. Start OpenLaunchDeck.
3. Use `Device > Connect` or the `Reconnect` button if it does not connect automatically.
4. The header should show `Connected mode`.

When no Launchpad is connected, OpenLaunchDeck runs in simulation mode. Simulation mode is normal for editing profiles without hardware.

## Programmer Mode

OpenLaunchDeck uses the Launchpad Mini MK3 Programmer Mode path for predictable pad input and RGB output. The app sends the Programmer Mode SysEx command when it connects and restores Live Mode when closing the MIDI port.

If pad input or lighting looks wrong, use MIDI Debug and calibration before assuming the hardware is broken.

## MIDI Debug

Open `Device > MIDI Debug`.

Use it to check:

- Available MIDI input ports
- Available MIDI output ports
- Incoming MIDI messages
- Outgoing MIDI messages
- Parsed button IDs
- Raw note/control data

## Calibration

Use calibration if a pad reports the wrong button ID.

The default grid labels are:

`A1` through `A8` on the top row, down to `H1` through `H8` on the bottom row.

The current default mapping is isolated in:

`openlaunchdeck/devices/midi_mapping.py`

Custom mappings are stored in:

`%APPDATA%\OpenLaunchDeck\midi_mappings`

## Button Behavior

Physical Launchpad presses and editor Test actions both go through the action runner. Clicking a pad in the UI selects it for editing; it does not run the action.
