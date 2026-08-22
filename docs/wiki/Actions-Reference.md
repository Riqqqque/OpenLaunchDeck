# Actions Reference

Choose an action in the Button Editor, fill in its fields, then use **Test Action** before relying on the physical pad.

## Quick List

| Action | Use it for |
| --- | --- |
| No Action | Leave a pad intentionally empty |
| Switch Page | Move to another page in the current profile |
| Switch Profile | Open a specific profile |
| Navigate Deck | Move to adjacent pages or profiles |
| Open URL | Open a website normally or in a private window |
| Open Path/App | Open a local file, folder, or application |
| Clipboard | Copy reusable text or clear the clipboard |
| Run Command | Start a Windows command |
| PowerShell Command | Run PowerShell without loading a user profile |
| Hotkey | Send a keyboard combination |
| Type Text | Type configured text into the focused application |
| Media Control | Play, pause, skip, stop, or change media volume |
| Volume Control | Change the default Windows playback endpoint |
| Window Control | Control the active window or show the desktop |
| Mouse Control | Click or scroll at the current pointer position |
| HTTP Request | Call a local service, webhook, or web API |
| Play Sound | Play a local soundboard file |
| Random Sound From Folder | Play one randomly selected local clip |
| Stop Sound | Stop one button, one page, or all sounds |
| Delay | Pause inside a multi-action sequence |
| Multi-Action | Run multiple actions in order |
| SSH Command | Run a remote command with key-based authentication |
| OBS WebSocket | Control OBS directly |

## No Action

Does nothing and returns a successful result. Use it for blank or decorative pads.

## Switch Page

**Field:** Page ID

Switches to another page in the active profile and refreshes the on-screen grid and Launchpad lighting. The ID must match the destination page ID, not only its display name.

The Launchpad's Left and Right hardware buttons also move between pages by default. Their assignments are configurable under **Settings > Launchpad**.

## Switch Profile

**Field:** Profile

Opens the selected profile and its default page. The profile list comes from the profiles currently loaded by OpenLaunchDeck, so profile IDs do not need to be typed manually.

## Navigate Deck

**Fields:** Move To, Wrap At The End

Moves to the previous, next, first, last, or default page without hard-coding a page ID. It can also move to the previous or next profile. With wrapping enabled, moving past the final item returns to the first item.

## Open URL

**Fields:** URL, Open In Private Window

Opens an HTTP or HTTPS address. Plain website addresses receive `https://` automatically. Other URL schemes are rejected.

Private-window mode supports the registered Windows default browser when it is Brave, Chrome, Chromium, Vivaldi, Edge, or Firefox. If the browser cannot be identified, the action fails instead of quietly opening a normal window.

## Open Path/App

**Field:** Path

Opens an existing file, folder, or executable with Windows. Environment variables such as `%USERPROFILE%` are supported.

The action fails clearly when the path does not exist.

## Clipboard

**Fields:** Operation, Text

Copies reusable text to the Windows clipboard without typing it into the focused application, or clears the clipboard. This is useful when a macro should prepare text for a later manual paste. Text is stored in the profile, so do not put secrets into profiles that may be exported.

## Run Command

**Fields:** Command, Working Directory, Run Hidden, Wait For Completion, Wait Timeout

Runs a local command through the Windows shell.

- Leave **Wait For Completion** off for long-running programs or scripts.
- Turn it on when a later multi-action step depends on the command finishing.
- **Run Hidden** avoids opening a console window when Windows supports it.
- Mark destructive or system-changing commands as **Dangerous** in the button settings.

Waited commands have a bounded execution time and return captured output. Non-waited commands return after the process starts.

## PowerShell Command

Uses the same fields as Run Command. The command is passed to `powershell.exe` with `-NoProfile` and `-NonInteractive`.

Mark commands that stop services, change files, restart systems, or remove data as **Dangerous**.

## Hotkey

**Controls:** Ctrl, Alt, Shift, Win, Key

Select any needed modifiers, then choose the main key from the searchable drop-down. The list includes letters, numbers, navigation and editing keys, punctuation, media keys, and `F1` through `F24`. Typing into the key list filters it; you do not need to type the complete shortcut syntax.

Examples of the resulting shortcuts:

```text
ctrl+c
win+shift+s
shift+left
ctrl+alt+k
f15
```

Some elevated applications and games reject input from a non-elevated app. Run both applications at the same privilege level when that happens.

## Type Text

**Fields:** Text, Interval

Types text into the currently focused application. Interval controls the pause between characters; use `0` for normal fast entry.

This action sends text wherever keyboard focus currently is. Do not assign secrets or destructive console commands to unattended buttons.

## Media Control

**Field:** Control

Available controls:

- `play_pause`
- `next`
- `previous`
- `stop`
- `volume_up`
- `volume_down`
- `mute`

On Windows, the action uses an application media command first and a keyboard media-key fallback second. The active browser or media application still decides whether it accepts the command.

## Volume Control

**Fields:** Mode, Target Volume

Available modes:

- `volume_up`
- `volume_down`
- `set_volume`
- `mute`
- `unmute`
- `toggle_mute`

This controls the default Windows playback endpoint. It does not replace per-application mixer sliders. **Target Volume** is only used by `set_volume`.

## Window Control

**Field:** Window Action

Minimizes, maximizes, restores, or closes the active Windows application, or shows the desktop. Closing a window is treated as dangerous and requires the normal two-press confirmation. OpenLaunchDeck refuses to close its own active window through this action.

## Mouse Control

**Fields:** Mouse Action, Scroll Amount

Clicks at the current pointer position with the left, right, or middle button; double-clicks; or scrolls up and down. Mouse actions run through the action worker so they do not block the interface.

## HTTP Request

**Fields:** Method, URL, Headers JSON, Body, Timeout

Supported methods are `GET`, `POST`, `PUT`, `PATCH`, and `DELETE`.

Headers must be a JSON object:

```json
{
  "Content-Type": "application/json"
}
```

Timeout must be between 1 and 60 seconds. HTTP status codes 400 and higher return a failed action result.

Do not put private API keys or webhook credentials into profiles you plan to export or share.

## Play Sound

**Fields:** Sound File, Clip Volume, Also Send To Voice Chat, Loop Until Stopped, When Pressed Again, Playing Color, Stop When Page Changes

Supported baseline formats are `.wav` and `.mp3`. `.ogg` depends on the codecs available to QtMultimedia on the computer.

Already Playing choices:

- `restart` restarts the current button sound.
- `overlap` starts another copy.
- `ignore` keeps the existing copy playing.
- `toggle_stop` stops the sound on the next press.

Click **Browse** beside Sound File to select a local clip. OpenLaunchDeck keeps the path in the profile, so keep the file in a stable location. See [Soundboard and Voice Chat](Soundboard-and-Discord-Routing.md) for output routing and quality setup.

## Random Sound From Folder

**Fields:** Sound Folder, Include Subfolders, Clip Volume, Loop, When Pressed Again, Playing Color, Stop When Page Changes

Selects one supported local file from a folder and plays it through the normal soundboard engine. The folder scan runs in the background, uses bounded memory, and supports `.wav`, `.mp3`, and `.ogg` where the installed media codecs allow them. No files are downloaded or copied.

## Stop Sound

**Field:** Sounds To Stop

Scopes:

- `this_button` stops sounds associated with the pressed button.
- `current_page` stops sounds started from the active page.
- `all` stops every sound.

Keep a **Stop All Sounds** button near loops and overlap-enabled clips.

## Delay

**Field:** Milliseconds

Waits from 0 through 60,000 milliseconds. Delay is primarily intended for Multi-Action sequences and runs away from the GUI thread.

## Multi-Action

**Fields:** Steps, Continue On Error

Runs actions in order. Use **Add Step** to choose an action through the normal guided editor. Double-click a step or use **Edit** to change it. **Move Up**, **Move Down**, and **Remove** organize the sequence without editing profile JSON.

A common sequence is Hotkey, Delay, then Play Sound. Add a Delay step when the receiving application needs time before the next action.

When **Continue On Error** is off, the sequence stops at the first failed step. Nested multi-actions are limited to prevent runaway recursion.

## SSH Command

**Fields:** Host, Port, Username, Private Key, Command

Uses Paramiko and key-based authentication. The action loads known host keys and rejects unknown hosts instead of automatically trusting them.

Passwords are not stored by this action. Test SSH access from a terminal first, and never bundle a private key with an exported profile.

## OBS WebSocket

**Common fields:** Operation, OBS Host, OBS Port, OBS Password, Connection Timeout

Default connection:

```text
Host: 127.0.0.1
Port: 4455
```

Available operations:

| Operation | Additional fields |
| --- | --- |
| `save_replay_buffer` | Start Replay Buffer If Needed, Replay Verify Timeout Ms |
| `start_replay_buffer` | None |
| `stop_replay_buffer` | None |
| `save_screenshot` | Screenshot Source, Screenshot Folder, Screenshot Format |
| `start_recording` | None |
| `stop_recording` | None |
| `start_streaming` | None; always mark the button Dangerous |
| `stop_streaming` | None |
| `switch_scene` | Scene Name |
| `show_source` | Scene Name, Source Name |
| `hide_source` | Scene Name, Source Name |
| `toggle_source` | Scene Name, Source Name |
| `mute_input` | Input Name |
| `unmute_input` | Input Name |
| `toggle_input_mute` | Input Name |

Scene, source, and input names must match OBS exactly. See [OBS WebSocket Setup](OBS-WebSocket-Setup.md) for complete setup and testing.

## Dangerous Confirmation

Dangerous is a button setting, not a separate action.

1. First press arms the button for five seconds.
2. The GUI and Launchpad show a warning state.
3. A second press inside the window executes the action.
4. Timeout, page change, or device disconnect cancels the armed state.

Use it for start streaming, stop/restart server commands, shutdown operations, destructive scripts, and anything expensive to trigger accidentally.
