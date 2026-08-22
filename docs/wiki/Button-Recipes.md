# Button Recipes

This page gives exact starting values for common buttons. Use [Actions Reference](Actions-Reference.md) when you need every field or operation.

Use these as starting points. After a recipe works, rename the label, change the color, or move it to a different pad.

## Before You Test

Clicking a pad in the app selects it for editing. It does not run the action.

Use **Test Action** in the editor when you want to test from the app. Use the physical Launchpad pad when you want the real macro behavior.

## Choose A Recipe

- OBS: replay clip, screenshot, camera, microphone, or stream controls
- Hotkeys: voice chat, games, media, or extended function keys
- Soundboard: local playback, voice routing, and stop controls
- Navigation: move between pages or profiles
- Windows: websites, apps, folders, windows, mouse, clipboard, and commands

## OBS Replay Clip

Use this for instant replay clips.

- Label: `Clip`
- Color: `purple`
- Action type: `OBS WebSocket`
- Operation: `save_replay_buffer`
- Host: `127.0.0.1`
- Port: `4455`
- Password: your OBS WebSocket password if OBS requires one
- Start Replay Buffer If Needed: on
- Replay Verify Timeout Ms: `10000`
- Timeout Ms: `3000`

Test:

1. Open OBS.
2. Enable replay buffer in OBS settings.
3. Click **Test Action** once.
4. Wait a few seconds.
5. Click **Test Action** again.
6. Confirm a replay file appears in the OBS replay folder.

## OBS Start Stream

Only make this button if you really want stream start control on the deck.

- Label: `Start`
- Color: `yellow`
- Dangerous: on
- Action type: `OBS WebSocket`
- Operation: `start_streaming`
- Host: `127.0.0.1`
- Port: `4455`
- Password: your OBS WebSocket password if OBS requires one

OpenLaunchDeck requires confirmation for this operation even if the Dangerous checkbox is off. The first press arms the button. The second deliberate press starts streaming.

For most setups, keep stream start inside OBS and use the Launchpad for replay clips, screenshots, camera, mute, and scene controls.

## OBS Screenshot

Use this for screenshots that still work while a game is focused.

- Label: `Screen`
- Color: `cyan`
- Action type: `OBS WebSocket`
- Operation: `save_screenshot`
- Host: `127.0.0.1`
- Port: `4455`
- Screenshot Source: leave blank
- Screenshot Folder: `%USERPROFILE%\Videos`
- Screenshot Format: `png`
- Timeout Ms: `3000`

Blank Screenshot Source means OBS captures the current program scene.

## Hide Camera In OBS

Use this when you want one button that always hides the camera.

- Label: `Cam Off`
- Color: `red`
- Action type: `OBS WebSocket`
- Operation: `hide_source`
- Scene Name: exact OBS scene name
- Source Name: exact camera source name

Example source names might be `Video Capture Device`, `Facecam`, or `Camera`, but your OBS setup must match exactly.

## Show Camera In OBS

- Label: `Cam On`
- Color: `green`
- Action type: `OBS WebSocket`
- Operation: `show_source`
- Scene Name: exact OBS scene name
- Source Name: exact camera source name

## Toggle Camera In OBS

Use this if you prefer one button instead of separate on/off buttons.

- Label: `Camera`
- Color: `yellow`
- Action type: `OBS WebSocket`
- Operation: `toggle_source`
- Scene Name: exact OBS scene name
- Source Name: exact camera source name

## Toggle OBS Mic Mute

- Label: `Mic`
- Color: `orange`
- Action type: `OBS WebSocket`
- Operation: `toggle_input_mute`
- Input Name: exact OBS audio input name

Common OBS input names include `Mic/Aux`, but copy the real name from the OBS Audio Mixer.

## Discord Mute Hotkey

Use this if Discord is configured with a keyboard shortcut.

- Label: `Mute`
- Color: `orange`
- Action type: `Hotkey`
- Hotkey: the same keybind set in Discord

Recommended key choices:

- `F13`
- `F14`
- `F15`
- `F16`

Extended function keys are useful because most games do not use them by default.

## Load Serato Decks With Arrow Hotkeys

Serato can bind deck loading to arrow-key combinations. Create one button for each deck:

Left deck:

- Label: `Load Left`
- Action type: `Hotkey`
- Hotkey: `shift+left`

Right deck:

- Label: `Load Right`
- Action type: `Hotkey`
- Hotkey: `shift+right`

The Hotkey field is searchable and editable. You can select a suggestion or type a combination directly. Arrow keys, letters, numbers, navigation/editing keys, media keys, and `F1` through `F24` can be combined with `ctrl`, `shift`, `alt`, and `win`.

## Discord Deafen Hotkey

- Label: `Deafen`
- Color: `blue`
- Action type: `Hotkey`
- Hotkey: the same keybind set in Discord

Use a different extended function key than the mute button.

## Play Or Pause Music

- Label: `Media`
- Color: `blue`
- Action type: `Media Control`
- Control: `play_pause`

Use the Media Control action instead of binding a browser-specific key. The active browser or media application must still accept the Windows media command.

## Set Windows Volume

- Label: `Vol 40`
- Color: `blue`
- Action type: `Volume Control`
- Mode: `set_volume`
- Target Volume: `40`

This changes the default Windows playback endpoint, not an individual application's mixer slider.

## Play A Soundboard Clip Locally

- Label: short clip name
- Color: `purple`
- Action type: `Play Sound`
- File Path: choose a local `.wav` or `.mp3`
- Volume: start at `60`
- Loop: off
- Already Playing: `restart`
- Route To Voice Chat: off

If you do not hear it locally, fix local playback before changing voice chat settings.

## Play A Soundboard Clip In Voice Chat

First make local playback work. Then use:

- Action type: `Play Sound`
- Route To Voice Chat: on
- Volume: start at `50` to `70`
- Already Playing: `restart`

Then set Discord, your game, or another voice app input to the route recording device. For games with push-to-talk, hold push-to-talk while playing the soundboard clip. See [Soundboard And Voice Chat Routing](Soundboard-and-Discord-Routing.md) for the full checklist.

## Stop All Sounds

Always keep one of these near soundboard buttons.

- Label: `Stop`
- Color: `red`
- Action type: `Stop Sound`
- Scope: `all`

## Switch Page

Use this for page navigation on the 8x8 grid.

- Label: `Next`
- Color: `blue`
- Action type: `Switch Page`
- Target Page: the page you want to open

Use **Navigate Deck** instead when the same button should always move to the previous or next page.

## Previous And Next Page

Create two grid buttons:

- Action type: `Navigate Deck`
- Move To: `Previous Page` or `Next Page`
- Wrap At The End: on

The Launchpad's physical left and right arrow buttons use these operations by default. Change any top or scene-button assignment under `Settings > Launchpad Controls`.

## Previous And Next Profile

- Action type: `Navigate Deck`
- Move To: `Previous Profile` or `Next Profile`
- Wrap At The End: on

The physical up and down arrow buttons use these operations by default. Use **Switch Profile** when a pad should always open one named profile instead.

## Launchpad Scene Buttons

The eight buttons down the right side open pages 1 through 8 by default. If a profile has fewer pages, an unavailable scene button does nothing and reports the reason in the status bar. Assign different behavior under `Settings > Launchpad Controls`.

Useful defaults:

- Left/Right: previous/next page
- Up/Down: previous/next profile
- Session: default page
- User: stop all sounds
- Scene 1-8: open page 1-8

## Open A Website

- Label: `Dash`
- Color: `green`
- Action type: `Open URL`
- URL: the site you want to open
- Open In Private Window: optional; opens the URL using the registered default browser's private mode

Private-window launching supports Brave, Chrome, Chromium, Vivaldi, Edge, and Firefox on Windows. If the registered handler is unsupported or its executable cannot be resolved, the action reports an error instead of opening the URL in a normal window. Browser or organization policy can disable private browsing; OpenLaunchDeck does not bypass that policy.

Example:

```text
https://dashboard.twitch.tv
```

## Open A Folder Or App

- Label: `Folder`
- Color: `blue`
- Action type: `Open Path`
- Path: a folder, file, or app path

Examples:

```text
%USERPROFILE%\Videos
C:\Program Files\obs-studio\bin\64bit\obs64.exe
```

## Window Controls

Use **Window Control** for the currently focused app:

- Minimize Active Window
- Maximize Active Window
- Restore Active Window
- Close Active Window
- Show Desktop

Mark **Close Active Window** as dangerous. OpenLaunchDeck refuses to close itself through this action.

## Mouse Controls

Use **Mouse Control** to click at the current pointer location, double-click, right-click, middle-click, or scroll. Scroll actions expose a `Scroll Steps` control. These actions never move the pointer.

## Copy Reusable Text

- Label: `Reply`
- Action type: `Clipboard`
- Operation: `Copy Configured Text`
- Text: the text you want ready to paste

This copies text without typing into the currently focused window. Use **Type Text** when the button should type immediately.

## Random Sound From A Folder

- Action type: `Random Sound From Folder`
- Sound Folder: a local folder containing `.wav`, `.mp3`, or `.ogg` files
- Include Subfolders: optional
- Clip Volume: start around `60`
- When Pressed Again: `restart`

The folder is scanned in a background action worker only when pressed. A bounded one-pass selection avoids loading audio files or a large filename list into memory.

## Run A Local Command

Only use command buttons when you understand what the command does.

- Label: short command name
- Color: `yellow`
- Action type: `Run Command`
- Command: command to run
- Wait For Completion: off for long-running commands
- Dangerous: on if the command stops, deletes, restarts, or changes something important

Dangerous buttons require a second press inside the arm window.

## Multi-Action With A Delay

Use this when one pad should run actions in order.

- Label: `Ready`
- Color: `cyan`
- Action type: `Multi-Action`
- Continue On Error: off

Steps:

```json
[
  {
    "type": "hotkey",
    "config": {
      "hotkey": "f15"
    }
  },
  {
    "type": "delay",
    "config": {
      "milliseconds": 500
    }
  },
  {
    "type": "media_control",
    "config": {
      "control": "play_pause"
    }
  }
]
```

Test each step by itself before combining them.

## Good First Layout

A simple first streaming page:

```text
A1 Clip       A2 Screen     A3 Camera    A4 Mic
A5 Sound 1    A6 Sound 2    A7 Stop      A8 Next
```

Keep the first page simple. Move advanced commands to page 2 after the basics work.
