# Launchpad Mini MK3 Setup

OpenLaunchDeck targets the Novation Launchpad Mini MK3 over USB MIDI.

The important idea: the Launchpad sends MIDI messages when pads are pressed, and OpenLaunchDeck sends MIDI messages back to light pads.

## Connect the Device

1. Plug the Launchpad Mini MK3 into USB.
2. Start OpenLaunchDeck.
3. Use `Device > Connect` or the `Reconnect` button if it does not connect automatically.
4. The header should show `Connected mode`.

When no Launchpad is connected, OpenLaunchDeck runs in simulation mode. Simulation mode is normal for editing profiles without hardware.

## Windows Port Names

On Windows, the device may expose more than one MIDI port. Common names include:

- `LPMiniMK3 MIDI`
- `MIDIIN2 (LPMiniMK3 MIDI)`
- `MIDIOUT2 (LPMiniMK3 MIDI)`

The second MIDI interface is usually the correct path for macro control and lighting. OpenLaunchDeck tries to prefer that interface automatically.

If the app says connected but pad presses do nothing, use MIDI Debug and try the other Launchpad port.

## Programmer Mode

OpenLaunchDeck uses the Launchpad Mini MK3 Programmer Mode path for predictable pad input and RGB output. The app sends the Programmer Mode SysEx command when it connects and restores Live Mode when closing the MIDI port.

If pad input or lighting looks wrong, use MIDI Debug and calibration before assuming the hardware is broken.

## First Hardware Test

Use a harmless test before assigning real actions.

1. Open `Device > MIDI Debug`.
2. Press the top-left pad on the Launchpad.
3. The debug window should show a raw MIDI message.
4. The parsed button should be `A1`.
5. Press the top-right pad.
6. The parsed button should be `A8`.
7. Press the bottom-left pad.
8. The parsed button should be `H1`.

If those are correct, the main grid mapping is probably good.

## MIDI Debug

Open `Device > MIDI Debug`.

Use it to check:

- Available MIDI input ports
- Available MIDI output ports
- Incoming MIDI messages
- Outgoing MIDI messages
- Parsed button IDs
- Raw note/control data

The debug window is safe to leave open while testing, but close it during normal gaming if you want the quietest possible runtime.

## Calibration

Use calibration if a pad reports the wrong button ID.

The default grid labels are:

`A1` through `A8` on the top row, down to `H1` through `H8` on the bottom row.

The current default mapping is isolated in:

`openlaunchdeck/devices/midi_mapping.py`

Custom mappings are stored in:

`%APPDATA%\OpenLaunchDeck\midi_mappings`

Calibration flow:

1. Open `Device > MIDI Debug`.
2. Start calibration.
3. Press the requested pad.
4. Wait for the next requested pad.
5. Continue until the app has enough mappings.
6. Save the mapping.
7. Reconnect the device.

Use restore default mapping if a custom mapping makes things worse.

## Lighting

OpenLaunchDeck can:

- Set individual pad colors.
- Clear all pads.
- Refresh the active page.
- Flash press feedback.
- Flash success and error feedback.
- Blink dangerous armed buttons.
- Show active soundboard buttons.

Lighting is batched where practical so page switches do not send unnecessary duplicate color messages.

## Button Behavior

Physical Launchpad presses and editor Test actions both go through the action runner. Clicking a pad in the UI selects it for editing; it does not run the action.

## Extra Launchpad Buttons

The Launchpad Mini MK3 has buttons around the 8x8 grid. OpenLaunchDeck currently treats the 8x8 grid as the supported macro surface.

To change pages today, assign a grid pad to the `Switch Page` action.

Extra hardware buttons can be inspected in MIDI Debug. They should not be wired into app page navigation until their messages are verified for the device mode being used.
