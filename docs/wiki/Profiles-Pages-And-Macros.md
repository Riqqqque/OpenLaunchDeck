# Profiles, Pages, And Macros

OpenLaunchDeck organizes the Launchpad like a physical macro deck.

## The Four Building Blocks

- A **profile** is a complete deck setup, such as Streaming, Gaming, or Editing.
- A **page** is one 8x8 layout inside a profile.
- A **button** is one pad from `A1` through `H8` on one page.
- An **action** is what that button does.

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

## Profiles

Use separate profiles when the whole purpose of the deck changes.

Examples:

- Streaming
- Everyday PC
- Soundboard
- Video editing
- Server administration

The profile selector changes the active profile. The Profile Manager creates, renames, duplicates, imports, exports, and deletes profiles.

## Pages

Use pages to keep one profile organized without duplicating shared setup.

A clear streaming profile might use:

1. **Main** for replay, screenshot, camera, mic, and scenes
2. **Soundboard** for clips and stop controls
3. **Utilities** for media, folders, websites, and launchers
4. **Admin** for guarded commands

Page switching updates the GUI and Launchpad lights together.

## Physical Page Navigation

Assign **Switch Page** to a grid pad:

- Label: `Next`, `Back`, or the destination name
- Color: `blue`
- Action: **Switch Page**
- Page ID: exact destination page ID

The Launchpad's Left and Right buttons change pages by default in Programmer Mode, and Scene 1-8 open numbered pages. Change those assignments under **Settings > Launchpad** and verify the parsed controls in MIDI Debug after changing device modes.

## Editing A Button

1. Click a grid pad to select it.
2. Set a short label and clear color.
3. Choose an action.
4. Fill in the action fields.
5. Use **Test Action**.
6. Press the physical pad after the test succeeds.

Clicking the on-screen grid never runs the action.

## Consistent Labels And Colors

Suggested color language:

| Color | Meaning |
| --- | --- |
| Green | Start, enable, open, or safe success action |
| Red | Stop, disable, destructive, or high-risk action |
| Yellow | Warning, armed, or attention needed |
| Blue | Navigation and general utilities |
| Purple or cyan | OBS, soundboard, and streaming controls |

Keep labels short enough to scan quickly: `Clip`, `Screen`, `Mic`, `Cam`, `BRB`, `Stop`, `Next`.

## Dangerous Buttons

Enable **Dangerous** whenever an accidental press has a serious result.

Good candidates:

- Start streaming
- Stop or restart a server
- Shutdown or logoff
- Delete or overwrite data
- Run a destructive command

The first press arms the button for five seconds. The second press executes. Timeout, page change, or device disconnect cancels the armed state.

## Copy, Duplicate, And Reuse

- Use **Copy Button Config** and **Paste Button Config** for individual buttons.
- Duplicate a page before making a variation.
- Export a profile to move or share a complete setup.

Review exported JSON before sharing it. Profiles can contain OBS passwords, webhook headers, server information, commands, and local file paths.

## Autosave And Backups

Profile edits are debounced so typing does not write the file after every keystroke. Automatic backups can be enabled in Settings.

Profile files are stored in:

```text
%APPDATA%\OpenLaunchDeck\profiles
```

Backups are stored in:

```text
%APPDATA%\OpenLaunchDeck\backups
```

See [Settings and Data](Settings-And-Data.md) for a complete folder map and manual backup procedure.

## Portable Profile Checklist

Before using a profile on another computer:

- Copy referenced sound files and scripts separately.
- Replace machine-specific paths.
- Check MIDI and audio device selections.
- Re-enter private OBS or service credentials locally.
- Test every action before live use.

For the JSON structure, see [Profile Format](https://github.com/Riqqqque/OpenLaunchDeck/blob/main/docs/profile_format.md).
