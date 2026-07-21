# Hardware Notes

OpenLaunchDeck targets the Novation Launchpad Mini MK3. The device communicates over USB MIDI and exposes input messages for pad presses plus output messages for RGB pad lighting.

For source builds on Windows, Python 3.11-3.13 is recommended for hardware MIDI work because the real-time MIDI backend is most likely to install from a prebuilt wheel. Newer Python versions can still run simulation mode, but may need a local C++ toolchain for the MIDI backend.

On Windows, the device may appear as `LPMiniMK3 MIDI`, `MIDIIN2 (LPMiniMK3 MIDI)`, and `MIDIOUT2 (LPMiniMK3 MIDI)`. The first interface is the DAW/session interface. OpenLaunchDeck prefers the second MIDI interface for macro control and lighting because the Launchpad Mini MK3 reference manual identifies that interface for Custom modes, Lighting Custom Modes, and Programmer Mode.

The Launchpad Mini MK3 has 64 RGB pads plus extra navigation and scene-launch buttons around the grid. OpenLaunchDeck currently treats the 8x8 pad grid as the supported macro surface. Use grid pads with the Switch Page action for OpenLaunchDeck page changes. The extra hardware buttons can be inspected in MIDI Debug, but they are not assigned to previous/next OpenLaunchDeck pages by default until their exact messages are verified on hardware.

## Programmer Mode

Programmer Mode is recommended because it gives a predictable MIDI layout for pad messages. If pad presses or lighting do not match the grid, open `Device > MIDI Debug`, press pads, and verify the raw messages.

OpenLaunchDeck sends the documented Programmer Mode SysEx message when it connects. If another music app changes the device mode afterward, press Reconnect or put the device back into Programmer Mode from the hardware setup menu.

## Testing Raw MIDI

Use the MIDI debug window to view:

- Available input ports
- Available output ports
- Incoming messages
- Outgoing lighting messages
- Parsed A1-H8 button IDs
- Current mapping table
- Calibration raw message captures

If the parsed button ID is wrong or missing, use calibration and save the mapping.

## Calibration

Calibration asks for each pad from A1 through H8 and records the incoming note/control address plus raw MIDI data. The saved mapping lives in `%APPDATA%\OpenLaunchDeck\midi_mappings`.

The MIDI Debug window also has a Restore Default Mapping button. Use it to return to the built-in Programmer Mode preset.

## Reconnect And Unplug Handling

Connect, reconnect, and port health checks run outside the GUI thread. While auto-connect is enabled, the app checks the open handles and Windows MIDI port list on a low-frequency timer. A stale, closed, or missing port is marked disconnected and reopened automatically without requiring an app restart.

If the device disappears during a lighting send, the app disarms dangerous buttons, stops warning blinks, and returns to simulation mode while reconnecting. Failures in the MIDI Debug window or another application callback are logged without tearing down an otherwise healthy hardware connection.

## RGB Lighting Verification

OpenLaunchDeck can set individual pad colors, clear all pads, refresh a full page, flash press/success/error colors, blink armed dangerous buttons, and show sound playing state. These features use a Programmer Mode palette preset until the exact device/mode behavior is verified on hardware.

Use MIDI Debug to confirm outgoing messages before relying on lighting behavior during a live workflow.
