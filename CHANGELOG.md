# Changelog

## 0.2.2

- Fixed tray Quit so it removes the tray icon, closes all application windows, and terminates the background process.
- Routed packaged startup smoke checks through the same complete shutdown path.

## 0.2.1

- Let Deck View use comfortable or large keycaps at typical second-monitor widths instead of unnecessarily forcing Compact sizing.
- Increased distance-view label scale and added a 1480-pixel layout regression check for all 64 pads.

## 0.2.0

- Rebuilt the 8x8 workspace as a responsive keycap surface with larger distance-readable labels, Deck View, compact editing, and unclipped layouts from 760x520 upward.
- Added configurable Programmer Mode controls for the Launchpad arrows, Session/User buttons, and eight scene buttons, with exact MIDI Debug mapping and batched edge lighting.
- Added Switch Profile, Navigate Deck, Clipboard, Window Control, Mouse Control, and Random Sound From Folder actions.
- Expanded the Basic PC starter deck with previous, next, stop, mute, volume, and Show Desktop controls.
- Fixed page-change sound handling so only clips configured to stop on page changes are interrupted.
- Moved all grid and hardware-control lighting through one coalescing background output worker.
- Replaced the application mark with a high-contrast launch-key icon rendered consistently at every Windows icon size.

## 0.1.63

- Replaced the nested card-style workspace with a flat command bar, edge-aligned side rails, and an unframed Launchpad canvas.
- Simplified pad action labels, reduced visual nesting, tightened grid spacing, and increased usable pad size.
- Reclaimed vertical space in short windows while keeping editing and Focus Grid controls accessible.

## 0.1.62

- Fixed short-window grid sizing so all 64 pads remain visible without horizontal or vertical scrollbars.
- Added height-aware single-pane editing, tighter short-window chrome, legible compact pad typography, and unclipped profile controls for second-monitor layouts.
- Removed the in-app sound search, download, import, credential, and bundled starter-sound feature while keeping local-file soundboard playback and routing.
- Reduced release size by removing the retired sound assets and related feature modules.
- Expanded visual checks to cover the 1280x640 layout that exposed the clipped bottom row.

## 0.1.61

- Rebuilt the main workspace around square pads and wide, compact, focus, and single-pane layouts so the grid and editor stay usable at every supported window size.
- Added Midnight, OLED Black, Galaxy OLED, Arctic White, Graphite, Broadcast, and High Contrast themes with immediate previews and a tabbed Settings window.
- Replaced the Sound Library tables with a responsive card browser, direct Preview and Use controls, local filtering, and a small account-free collection of original starter effects.
- Added searchable action categories, visible field guidance, color swatches, and a visual Multi-Action step editor.
- Replaced the app mark and rebuilt every PNG and Windows ICO size from one SVG source for consistent installer, shortcut, title-bar, taskbar, and repository branding.
- Added exact-size native Windows visual capture coverage for every theme at narrow, compact, and wide breakpoints, plus Focus Grid, Settings, and Sound Library views.
- Prevented sound card row overlap, enforced readable theme contrast, fit all 64 pads in the minimum-size Focus Grid view, and coalesced resize work.

## 0.1.60

- Added a native Sound Library for searching, previewing, downloading, importing, and assigning sound effects without leaving the app.
- Added popular, newest, top-rated, category, license, and duration filters with CC0 results selected by default.
- Protected personal Freesound API keys with Windows account encryption and kept downloads, metadata, and credits under AppData.
- Simplified action editing with visible guidance, conditional OBS and volume fields, clearer labels, safer defaults, and pre-dispatch validation.
- Debounced action-form edits, hardened canceled and oversized downloads, and preserved narrow-window editor usability.
- Removed unused Tcl/Tk and screenshot-automation modules from Windows release packages while keeping native Windows input handling.

## 0.1.59

- Replaced the hotkey syntax field with modifier controls and a searchable key selector covering F1-F24, navigation, media, letters, numbers, and punctuation.
- Added a current-profile page selector for Switch Page actions.
- Made action option labels readable while preserving their existing profile values.

## 0.1.58

- Rebuilt the README as a concise project overview with direct setup and support paths.
- Reorganized the public wiki around beginner setup, complete action/settings references, focused feature guides, and symptom-first troubleshooting.
- Improved issue forms, contributor guidance, package descriptions, and wiki publishing checks.

## 0.1.57

- Added searchable hotkey suggestions for arrow, navigation, editing, media, letter, number, punctuation, and F1-F24 keys.
- Added natural arrow-key aliases and verified Windows extended-key handling for combinations such as `shift+left` and `shift+right`.
- Updated the Windows MIDI backend and GitHub workflow dependency floors.

## 0.1.56

- Prevented local release builds from accumulating outdated installers and portable archives.
- Ignored version-specific development environments consistently.

## 0.1.55

- Fixed restoring the main window from a background or tray instance on Windows.
- Added logging for single-instance launch commands.

## 0.1.54

- Switched browser play/pause and other media controls to Windows application commands with a keyboard fallback.
- Routed volume-key fallback through the same reliable global media-control backend.
- Tightened the main command bar, side panels, themes, and pad visuals for a cleaner workspace.
- Preserved user-adjusted splitter widths while resizing within the same layout breakpoint.
- Kept all eight pad columns visible at the minimum supported window width.

## 0.1.53

- Accepted plain website addresses in URL actions by adding HTTPS automatically while continuing to reject unsafe URL schemes.
- Added a low-frequency background MIDI port health check that reconnects stale Windows handles automatically.
- Isolated MIDI debug and application callback failures so they cannot falsely disconnect the Launchpad transport.
- Separated hotkey, media, and volume actions from slower background work so OBS, network, command, URL, and app-launch actions cannot hold up latency-sensitive buttons.
- Ignored outdated health-check results after a manual reconnect and emitted each disconnect notification only once.

## 0.1.52

- Added an `Open In Private Window` option to URL actions.
- Opened private URLs through the registered Windows default browser with native private-mode handling for Brave, Chrome, Chromium, Vivaldi, Edge, and Firefox.
- Kept private URL actions closed on unsupported browser handlers instead of silently opening a normal window.

## 0.1.51

- Fell back to the current Windows default listening device when a saved soundboard monitor endpoint disappears or receives a new device ID.
- Kept voice-chat routing strict so a missing cable endpoint cannot send routed clips to the wrong output.

## 0.1.50

- Recovered from damaged or mistyped settings without blocking startup and kept the original file in backups.
- Sanitized imported profile IDs, protected profile paths, preserved deleted profiles as backups, and stopped legacy starter refreshes from replacing customized soundboards.
- Added working profile create, duplicate, rename, and delete controls.
- Preserved the last valid multi-action while its JSON is being edited and kept nested page, lighting, and sound actions on the correct thread.
- Stopped editor refreshes from scheduling profile writes and preserved action fields that are not rendered by the current editor.
- Bounded command, delay, and HTTP action limits, capped captured command output, hardened PowerShell quoting, and enabled strict SSH host-key checks.
- Made update dialogs safe to close around worker activity and added checksum-backed GitHub Release checks when no custom manifest is configured.
- Replaced stale bundled runtime files during installer upgrades without touching AppData.
- Required a patched cryptography release after the final dependency audit.
- Added release-tag test execution and focused regression coverage for the new recovery and lifecycle paths.

## 0.1.49

- Replaced per-flash and per-blink timer threads with one shared lighting scheduler.
- Coalesced pending RGB updates so rapid pad presses cannot build an unbounded lighting queue.
- Moved file logging off action and GUI threads.
- Switched Windows text entry and media buttons to the native input path to avoid a large first-use import.
- Paused Soundboard refresh work while its panel is closed and reused one modeless panel instance.
- Debounced profile autosaves and kept the grid beside the editor in compact windows.
- Refreshed the app icon at every packaged size and made the running app use the same multi-size icon as Windows shortcuts.
- Tightened the first five seconds of priority checks so external launch tools cannot leave the app at RealTime priority during startup.

## 0.1.48

- Changed the Windows process priority guard to keep OpenLaunchDeck at Normal priority instead of AboveNormal so games keep scheduler priority.
- Reduced priority guard wakeups and microphone route checks to coarse, low-frequency timers.
- Lowered default background action concurrency to reduce CPU spikes from repeated macro presses.
- Skipped hidden-window grid/status repaints for hardware button presses and soundboard state changes.

## 0.1.47

- Added single-instance startup handling so duplicate launches activate the running app instead of opening another copy.
- Added `--show`, `--focus`, `--background`, and `--start-minimized` launch flags for startup and window-layout tools.
- Made the Windows startup entry use background mode so layout tools can control when the visible window is shown.
- Added tests for startup launch options and duplicate-launch handling.

## 0.1.46

- Normalized the Windows process priority to AboveNormal during startup and added a low-frequency guard so the app cannot remain at RealTime priority.
- Reduced startup work when OpenLaunchDeck starts minimized into the tray by skipping the full window show path.
- Added tests for minimized startup behavior.
- Kept installer version metadata aligned with the app version.

## 0.1.45

- Kept OpenLaunchDeck running in the tray when the microphone voice route is enabled, even if normal tray mode is off.
- Added a lightweight microphone route guard that restarts the route if it is not running.
- Documented that `File > Quit` intentionally stops the voice route.

## 0.1.44

- Renamed soundboard route UI from Discord-specific wording to voice chat wording.
- Documented routed soundboard support for game voice chat and push-to-talk workflows.
- Kept Discord setup guidance as a common example instead of the only supported route.

## 0.1.43

- Added mandatory confirmation for OBS start-stream actions.
- Added a short confirmation delay so duplicate hardware events cannot confirm a dangerous action instantly.
- Restored normal action completion logging so button results are easier to audit.

## 0.1.42

- Detected the Windows names used by the lightweight virtual cable route.
- Updated Discord routing docs for the simple cable endpoint pair.

## 0.1.41

- Added OpenLaunchDeck Audio Bridge endpoint detection and route preference.
- Added bridge driver package scripts with WDK and signature safety checks.
- Added bridge setup docs for the dedicated voice input/output route.

## 0.1.40

- Added microphone routing into the selected soundboard voice route.
- Added microphone route controls to the Soundboard panel and Settings.
- Cleaned legacy mixer detection so route warnings stay generic.

## 0.1.39

- Added OpenLaunchDeck voice-route detection for soundboard audio.
- Added Soundboard panel controls to auto-find a clean voice route and copy the matching Discord input name.
- Updated soundboard and Discord routing docs around the new simple route.

## 0.1.38

- Made compact windows stack the button editor under the Launchpad grid so controls stay visible.
- Made the button editor wrap fields and controls correctly in narrow windows.

## 0.1.37

- Made the whole Launchpad grid cell respond when selecting buttons in the editor.
- Repaired pasted button configs so they use the target pad ID instead of keeping the original pad ID.

## 0.1.36

- Fixed soundboard volume handling so 0% stays silent and low values do not play like full volume.
- Matched routed voice-chat playback and local monitor playback to the same effective soundboard gain.
- Added 0-100 editor bounds for soundboard and Windows volume controls.

## 0.1.35

- Made left-click and double-click on the system tray icon restore the main window.
- Made the tray menu Open action restore, raise, and activate the window instead of only showing it.

## 0.1.34

- Added real Windows endpoint volume control for set volume, mute, unmute, toggle mute, and volume steps.
- Removed server-specific starter profiles that required user-only host and command values.
- Updated the soundboard starter profile to use real Windows system sounds.
- Moved old unconfigured server starter profiles into backups instead of loading replacement commands.
- Cleaned public docs and update examples so release guidance uses real asset URLs and checksums.

## 0.1.33

- Made Launch at startup write the Windows user startup entry instead of only saving the setting.
- Repaired stale startup commands automatically in the packaged app after updates.
- Made Start minimized fall back to the taskbar when tray mode is off.

## 0.1.32

- Cleaned up partially started soundboard routes when a second output device is unavailable.

## 0.1.31

- Kept normal soundboard monitoring on the Windows system default route by default.
- Made stale selected soundboard outputs fail clearly instead of falling back to the wrong output.
- Allowed settings and profile JSON files with a UTF-8 BOM so Windows-edited files do not crash startup.
- Updated Discord routing docs to use the safer split route for browser, game, and Discord playback.

## 0.1.30

- Added verified OBS WebSocket actions for showing/hiding scene sources and muting/unmuting inputs.
- Updated blocking actions so the UI and lighting only report the real completed result, not the initial dispatch.
- Sent F13-F24 hotkeys as Windows virtual-key events for better extended-key compatibility.

## 0.1.29

- Hid duplicate Windows audio outputs with identical names in Soundboard and Settings device selectors.
- Added GitHub Wiki setup pages for beginner-friendly OBS, Launchpad, soundboard, and update workflows.

## 0.1.28

- Made OBS screenshots save to the normal OBS/Videos folder by default and verify the image file before reporting success.

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
- Added step-by-step Discord soundboard routing docs.

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

- Initial public application structure.
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
