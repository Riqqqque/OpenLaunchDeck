# Soundboard And Voice Chat

OpenLaunchDeck can play a clip through your normal listening device and optionally send the same clip into Discord, a game, or another voice application through a Windows audio route.

Set up **local playback first**. Add voice routing only after you can hear the clip yourself.

## Supported Audio

- `.wav` is the most predictable choice for short clips.
- `.mp3` is supported through QtMultimedia on normal Windows installs.
- `.ogg` depends on codecs available to QtMultimedia on the computer.

No copyrighted sounds are bundled.

Use [Sound Library](Sound-Library.md) to find, preview, import, and assign clips. Return here after local playback works when you want output routing or voice-chat setup.

## 1. Make Local Playback Work

Create a button:

- Action: **Play Sound**
- Sound File: a local `.wav` or `.mp3`, or a downloaded library sound
- Clip Volume: `60`
- Also Send To Voice Chat: off
- Loop Until Stopped: off
- When Pressed Again: `restart`

Click **Test Action**.

If you hear nothing:

1. Confirm the file still exists.
2. Try a short `.wav` file.
3. Open **Soundboard > Open Soundboard Panel**.
4. Set Default Output to **System default** or your actual headphones/interface.
5. Set global volume to `100` temporarily.
6. Check the Windows volume mixer.

## 2. Add A Stop Button

Keep this near sound buttons:

- Label: `Stop`
- Color: `red`
- Action: **Stop Sound**
- Scope: `all`

The Soundboard menu and panel also have **Stop All Sounds**.

## 3. Understand Voice Routing

A voice application listens to a Windows **recording input**, not a speaker output. A working route looks like:

```text
Soundboard clip + optional microphone
  -> voice-route playback endpoint
  -> matching recording endpoint
  -> Discord, game chat, or another voice application
```

OpenLaunchDeck does not install an audio driver. The endpoint pair must already exist. This can come from compatible external virtual-audio software or a separately installed OpenLaunchDeck Audio Bridge build.

## 4. Configure The Soundboard Panel

Open **Soundboard > Open Soundboard Panel**.

Recommended starting values:

| Setting | Value |
| --- | --- |
| Default Output | Your real headphones/interface or System default |
| Voice Route Output | Playback side of the route |
| Monitor Voice Routes | On, so you also hear routed clips |
| Microphone Input | Your real microphone |
| Route Microphone | On when the voice app listens to the combined route |
| Microphone Volume | `100` |
| Global Volume | `100` |

Use **Auto Find Route** when a compatible endpoint pair is already installed. Confirm the displayed recording input before changing Discord or game settings.

## 5. Enable A Button For Voice Chat

On each clip other people should hear:

1. Enable **Route To Voice Chat**.
2. Start button volume around `50` to `70`.
3. Keep **Monitor Voice Routes** on if you also want local playback.
4. Click **Test Action**.

The button and global volume combine into one effective gain used for both monitor and voice-route playback.

## 6. Select The Recording Input

In Discord or a game:

- Input Device: the **recording side** paired with the voice-route playback output
- Output Device: your normal headphones or audio interface

Do not send the voice application's output back into the voice route. That can duplicate other people's voices, create feedback, or destabilize audio playback.

For push-to-talk games, hold push-to-talk while playing the routed clip.

## 7. Test Both Voice And Clips

1. Open the voice application's microphone test or a private test channel.
2. Speak into your microphone.
3. Confirm its input meter moves.
4. Play a routed clip.
5. Confirm the same input meter moves.
6. Confirm you can still hear the clip locally.

If the clip works but your voice does not, enable Route Microphone and select the real microphone in the Soundboard panel.

If your voice works but the clip does not, confirm Route To Voice Chat on that button and verify the output/input endpoint pair.

## Volume And Quality

Good starting values:

- Global soundboard volume: `100`
- Button volume: `50` to `70`
- Routed microphone volume: `100`
- Windows route endpoint volume: `100`

If clips distort, lower the button volume first. If clips are quiet, raise the button volume before adding gain elsewhere.

Voice-processing features can damage music and effects. For a soundboard route, disable aggressive noise suppression, echo cancellation, and automatic gain control when the voice application allows it. Test your real microphone afterward.

## Repeated Press Behavior

| Setting | Best use |
| --- | --- |
| `restart` | Short clips that should start over |
| `toggle_stop` | Long clips, loops, and music beds |
| `ignore` | Prevent repeated presses while playing |
| `overlap` | Layer multiple copies; use carefully |

## Page And Exit Behavior

- **Stop On Page Change** ends that button's active sounds when leaving its page.
- **Stop sounds on exit** ends playback during a complete application exit.
- Closing to the tray can keep microphone routing active.
- Use **File > Quit** when you intentionally want all OpenLaunchDeck background behavior to stop.

## Avoid Duplicate Audio

- Voice application output must go to your headphones, not the input route.
- Only one microphone-forwarding path should be active.
- Do not enable Windows "Listen to this device" for the route unless you understand the extra monitor path.
- Keep only the intended voice-route playback/recording pair selected.
- Use OpenLaunchDeck monitoring instead of creating a second Windows monitoring loop.

## Missing Or Duplicate Devices

OpenLaunchDeck hides duplicate output names and advanced mixer buses from normal selectors. A saved but unavailable device appears as unavailable instead of being erased.

USB audio devices can receive a new Windows ID after reconnecting or updating. Re-select the device if local or voice-route playback stops after hardware changes.

## Still Not Working?

Use the Soundboard section in [Troubleshooting](Troubleshooting.md). Include the file type, local output, route output, voice input, microphone selection, and whether the input meter moves for voice and clips.
