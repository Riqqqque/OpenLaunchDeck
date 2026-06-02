# Changelog

## 0.1.27

- Added a direct OBS WebSocket screenshot action so screenshots do not depend on injected hotkeys.

## 0.1.26

- Fixed packaged OBS WebSocket actions by bundling the WebSocket client dependency into the Windows build.

## 0.1.25

- Added working OBS WebSocket actions for replay buffer, recording, streaming, scene switching, and input mute toggles.
- Fixed the Windows native hotkey sender so `SendInput` events are accepted correctly on 64-bit Windows.

## 0.1.24

- Switched hotkey actions to a Windows native keyboard path first for better in-game and OBS shortcut reliability.
- Added troubleshooting notes for game hotkeys, elevated games, and F13-F24 bindings.

## 0.1.23

- Added hotkey autocomplete with common shortcuts and F1-F24 options, including extended streaming keys like F15.
- Added step-by-step Discord and VoiceMeeter soundboard routing docs.

## 0.1.22

- Added per-sound voice chat routing with local monitoring for soundboard buttons.
- Added Soundboard panel controls for the voice chat output device and monitoring behavior.

## 0.1.21

- Corrected stale saved Launchpad port settings when a better second MIDI interface is available.

## 0.1.20

- Preferred the Launchpad Mini MK3 MIDI interface instead of the DAW/session interface on Windows.
- Switched the Launchpad into Programmer Mode on connect so pad presses send the expected MIDI messages.

## 0.1.19

- Fixed Launchpad Mini MK3 auto-detection on Windows when the device appears as `LPMiniMK3 MIDI`.
- Added regression tests for the primary and secondary Windows MIDI port names.

## 0.1.18

- Rebuilt every Windows icon size from the same desktop artwork.
- Updated the runtime window icon to use the desktop artwork source instead of the old 48px asset.

## 0.1.17

- Installed a standalone icon file beside the EXE so Windows shortcuts do not depend on stale EXE icon cache entries.
- Updated installer shortcuts and uninstall metadata to use the standalone icon.

## 0.1.16

- Reduced normal action logging so rapid button presses do not write to disk unless there is a warning or debug logging is enabled.
- Kept performance timing quiet by default to avoid extra work during normal use.
- Moved Launchpad lighting output onto a single background worker so MIDI lighting sends do not stall the UI.
- Disabled live MIDI debug UI callbacks while the MIDI Debug window is closed.
- Added a small action queue limit to prevent runaway background tasks from piling up.
- Reset the cached lighting state on disconnect so reconnects refresh pads cleanly.

## 0.1.15

- Made the desktop icon artwork the source for taskbar-sized icon layers.
- Updated the runtime window icon to use the same desktop icon artwork.
- Rebuilt the ICO so pinned shortcuts and the running taskbar icon use the same visual source.
- Aligned the Windows app identity used by the running app and installer shortcuts.

## 0.1.14

- Reworked the small Windows icon layers used by the taskbar and pinned shortcuts.
- Kept the outer shape as a clean white edge with transparent corners.
- Rebuilt the ICO asset with taskbar-sized artwork instead of relying on scaled-down large icons.

## 0.1.13

- Cleaned up the app icon edge so the white outline is the outer visible shape.
- Removed the header icon from the main window for a cleaner workspace header.
- Added hover text explaining why simulation mode is active.
- Added a Focus Launchpad Grid view that hides side panels and gives the grid more room.

## 0.1.12

- Improved window resizing with a splitter-based workspace layout.
- Added responsive narrow-window behavior that keeps the full 8-column Launchpad grid visible.
- Put the Launchpad grid inside a scrollable deck area for shorter windows.
- Styled workspace scrollbars so compact windows feel cleaner.

## 0.1.11

- Added Windows EXE version metadata so Explorer shows OpenLaunchDeck product and file version details.
- Refresh Windows shell icons after installer upgrades so desktop and taskbar icons update more reliably.

## 0.1.10

- Lowered and slightly scaled the grid action chips so `Volume` and `No Action` labels have more breathing room.
- Tightened the grid button title area so action chips no longer crowd the button name.
- Refreshed dark and light screenshots.

## 0.1.9

- Reworked the app icon again with a clearer small-size design for desktop and taskbar use.
- Restored the app icon in the main header with cleaner sizing.
- Improved Launchpad grid label fitting, spacing, and compact text handling.
- Refreshed dark and light screenshots.

## 0.1.8

- Reworked the app icon and regenerated Windows icon assets.
- Removed the header icon from the main window title area.
- Improved Launchpad grid pad sizing, shading, and label fitting.
- Made small action labels on pads easier to read.

## 0.1.7

- Made app grid clicks select pads for editing without running their actions.
- Kept action execution behind the selected button's Test control or real MIDI pad presses.
- Made the update dialog auto-check when opened from the app.
- Polished the header bar, mode indicator, update button, and dark theme label styling.

## 0.1.6

- Shortened the tagged release build path used by GitHub Actions.
- Added faster ZIP packaging for release builds.
- Let the installer script use faster compression settings in automated releases.
- Added build step timing output so slow release steps are easier to spot.

## 0.1.5

- Redesigned the main window with a cleaner header, workspace panels, and quick actions.
- Reworked grid pads into custom-rendered tiles with clearer labels, action tags, and state badges.
- Added configurable grid density for compact, comfortable, and large layouts.
- Improved dark and light themes and kept the system theme setting styled.

## 0.1.4

- Refreshed the grid, sidebar, status bar, and lighting after Switch Page actions.
- Documented that extra Launchpad navigation buttons are not bound to app page navigation until verified on hardware.

## 0.1.3

- Kept disabled grid buttons selectable so users can edit or re-enable them.
- Added a regression test for disabled button editing.

## 0.1.2

- Fixed installer shortcut icon metadata for Start Menu and Desktop shortcuts.
- Ensured installer-created shortcuts use the OpenLaunchDeck executable icon explicitly.

## 0.1.1

- Added OpenLaunchDeck logo and Windows icon assets.
- Wired the icon into the desktop window, system tray, PyInstaller executable, and installer.
- Added release support documents and dependency update checks for repository maintenance.
- Updated package metadata so icon assets are included with the application.

## 0.1.0

- Initial public MVP application structure.
- Added PySide6 desktop UI with editable 8x8 grid and button editor.
- Added profile/page models, JSON load/save, starter profiles, and AppData storage.
- Added simulation mode and action runner.
- Added core actions for URLs, paths, commands, hotkeys, delays, multi-actions, and soundboard playback.
- Added MIDI manager, Launchpad Mini MK3 device wrapper, mapping isolation, debug window, and calibration structure.
- Added page lighting refresh, changed-pad batching, press/success/error flashes, armed warning blink, and sound-playing state.
- Added soundboard panel, local file checks, per-sound volume, global volume, loop behavior, and stop controls.
- Added update manifest parsing, version comparison, download, checksum verification, and installer launch confirmation.
- Added performance timing helpers and optional native mapping/hash/checksum helper with Python fallback.
- Added build script, PyInstaller spec, installer script, docs, and tests.
