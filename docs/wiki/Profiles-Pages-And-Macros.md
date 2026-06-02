# Profiles, Pages, And Macros

OpenLaunchDeck is organized like a physical macro deck.

## Main Terms

- **Profile:** a full deck setup, such as Basic PC, Streaming, or Minecraft Server.
- **Page:** one 8x8 grid inside a profile.
- **Button:** one pad on the grid, such as `A1` or `H8`.
- **Action:** what a button does when pressed.

The Launchpad Mini MK3 grid uses this layout:

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

## Editing Without Running Buttons

Clicking a pad in the app selects it for editing. It does not run the button.

Use **Test Action** in the editor when you want to run a button from the app. Physical Launchpad pad presses run actions directly.

## Good Profile Patterns

For streaming:

- Page 1: OBS basics and clips
- Page 2: scenes and source toggles
- Page 3: soundboard
- Page 4: utility shortcuts

For gaming:

- Page 1: OBS replay, screenshot, mute, deafen
- Page 2: game-specific shortcuts
- Page 3: soundboard
- Page 4: server/admin tools

## Recommended Button Choices

Use colors consistently:

- Green: start, enable, open, safe action
- Red: stop, disable, dangerous action
- Yellow: warning, armed action, needs attention
- Blue: utility, navigation, edit-related
- Purple or cyan: soundboard and streaming

Keep labels short. A good label is usually one or two words:

- `Clip`
- `Screen`
- `Mute`
- `Camera`
- `BRB`
- `Sound 1`

## Switch Page Buttons

OpenLaunchDeck pages can be changed with the `Switch Page` action.

The Launchpad Mini MK3 has extra navigation-style buttons around the grid, but the current app uses the 8x8 grid as the reliable macro surface. Extra hardware buttons can be inspected in MIDI Debug and added later when their messages are verified.

## Dangerous Buttons

Mark a button dangerous when a mis-press could cause a problem.

Examples:

- Stop server
- Restart server
- Shutdown
- Delete
- Run destructive command

Dangerous buttons require two presses within the arm window. If the timer expires, the button disarms.

## Profile Files

Profiles are JSON files stored in:

`%APPDATA%\OpenLaunchDeck\profiles`

The app writes readable JSON so profiles can be backed up, exported, reviewed, and fixed by hand if needed.
