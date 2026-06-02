# Discord Voice Chat Routing

This guide routes OpenLaunchDeck soundboard buttons into Discord while still letting you hear Discord, your microphone, and the soundboard locally.

The setup below uses VoiceMeeter Banana. Other virtual audio mixers can work, but the device names and routing buttons will be different.

## Goal

- Your microphone is heard in Discord.
- OpenLaunchDeck soundboard clips can be heard in Discord when `Route To Voice Chat` is enabled.
- You still hear Discord and routed soundboard clips through your headphones.
- Discord audio does not loop back into Discord.

## Install VoiceMeeter Banana

1. Install VoiceMeeter Banana from VB-Audio or with Windows Package Manager:

   ```powershell
   winget install --id VB-Audio.Voicemeeter.Banana --exact
   ```

2. Reboot Windows after installing the audio driver.
3. Open VoiceMeeter Banana.

VoiceMeeter must be running for this route to work. Add it to Windows startup if you want the route to survive reboots.

## Windows Sound Defaults

Open Windows sound settings and set:

- **Output device:** your real headphones, speakers, or audio interface
- **Input device:** `Voicemeeter Out B1`

This keeps normal browser, game, and system audio on the real Windows output instead of making YouTube, games, and Discord depend on the virtual mixer. If you want VoiceMeeter to manage all system audio, use the advanced full-mixer setup below after the simple route is working.

## VoiceMeeter Banana Routing

In VoiceMeeter Banana:

1. Set **Hardware Out A1** to your real headphones or audio interface output.
   - Example: `Headphones (USB DAC)`
2. Set **Hardware Input 1** to your microphone.
   - Example: `Microphone (USB audio interface)`
3. On **Hardware Input 1**, enable `B1`.
4. On **Hardware Input 1**, leave `A1` off unless you want to hear your microphone locally.
5. On the main virtual input strip, usually labeled **Voicemeeter Input**, enable `A1` and `B1`.
   - This strip receives routed OpenLaunchDeck soundboard audio.
   - `A1` lets you hear it.
   - `B1` sends it to Discord.
6. Leave the AUX virtual input strip unused unless you choose the advanced full-mixer setup.

Recommended starting levels:

- Hardware Input 1 gain: `0 dB`
- Voicemeeter Input gain: `0 dB`
- Voicemeeter AUX gain: `0 dB`
- A1 bus gain: `0 dB`

If soundboard clips distort, lower the Voicemeeter Input strip by `3 dB` to `6 dB`. If friends can barely hear clips, raise the OpenLaunchDeck button volume first.

## OpenLaunchDeck Settings

Open `Soundboard > Open Soundboard Panel`.

Set:

- **Default Output Device:** `System default`
- **Voice Chat Output:** `Voicemeeter Input`
- **Monitor Voice Routes:** on

This sends routed soundboard clips to VoiceMeeter for Discord and also plays a monitor copy through your normal Windows output so you hear the clip locally.

If Windows reports the same VoiceMeeter output name many times, OpenLaunchDeck hides duplicate names in its Soundboard and Settings selectors. It also hides advanced VoiceMeeter buses such as `Voicemeeter In 1` through `Voicemeeter In 5` for normal users. The Windows tray can still show more entries than OpenLaunchDeck because Windows exposes the raw endpoint list.

For each soundboard button that Discord should hear:

1. Select the button.
2. Set action type to `Play Sound`.
3. Choose the local audio file.
4. Enable `Route To Voice Chat`.
5. Start with volume around `60` to `80`.
6. Use `toggle_stop` if you want a second press to stop the sound.

Avoid setting every clip to `100` unless the file is naturally quiet. Very loud files can clip before Discord receives them.

## Discord Voice Settings

Open `User Settings > Voice & Video`.

Set:

- **Input Device:** `Default` or `Voicemeeter Out B1`
- **Output Device:** `Default` or your real headphones, speakers, or audio interface
- **Audio Subsystem:** `Standard`

Keep Discord output off the VoiceMeeter strip that feeds `B1`. That prevents friends from hearing themselves.

For better soundboard quality, turn off:

- Noise Suppression / Krisp
- Echo Cancellation
- Noise Reduction
- Automatic Gain Control

If Discord voice activity does not trigger when a clip plays, lower Discord's input sensitivity or use push-to-talk while testing.

## Test Checklist

1. In Windows, play a normal system sound.
   - You should hear it through your headphones.
2. In Discord, join a call.
   - You should hear your friends.
3. In Discord, use **Mic Test** or ask a friend to confirm your microphone is audible.
4. In OpenLaunchDeck, press a routed soundboard button.
   - You should hear the clip.
   - Your friends should hear the clip.
5. Ask your friends whether the clip is too quiet, distorted, or muffled.

If the clip is too quiet:

- Raise the button volume in OpenLaunchDeck.
- Make sure the VoiceMeeter Input strip is not turned down.
- Lower Discord input sensitivity if voice activity is not opening.

If the clip sounds muffled, crunchy, or underwater:

- Turn off Discord noise suppression and automatic gain control.
- Use `.wav` or high-quality `.mp3` files.
- Lower the button volume slightly if the clip is clipping.

If you cannot hear your friends:

- Confirm Discord output is `Default` or your real headphones, speakers, or audio interface.
- Confirm Windows output is still your real headphones, speakers, or audio interface.
- Restart VoiceMeeter if Discord input is still routed through it.

If your friends hear themselves:

- Confirm Discord output is not going to `Voicemeeter Input`, which feeds `B1`.
- Confirm only your microphone and the routed OpenLaunchDeck soundboard strip feed `B1`.

## Working Example

Example device choices from a typical setup:

- Hardware Out A1: `Headphones (USB DAC)`
- Hardware Input 1: `Microphone (USB audio interface)`
- Windows output: `Headphones (USB DAC)`
- Windows input: `Voicemeeter Out B1`
- Discord output: `Headphones (USB DAC)` or `Default`
- Discord input: `Voicemeeter Out B1`
- OpenLaunchDeck default output: `System default`
- OpenLaunchDeck voice-chat output: `Voicemeeter Input`

Your device names may be different. Match the role of each device, not only the exact name.

## Advanced Full-Mixer Setup

If you want VoiceMeeter to manage all Windows audio, set Windows output and Discord output to `Voicemeeter AUX Input`, set OpenLaunchDeck default output to `Voicemeeter AUX Input`, and turn `Monitor Voice Routes` off. In VoiceMeeter, route `Voicemeeter AUX` to `A1` only, and route `Voicemeeter Input` to `A1` and `B1`.

Only use this route if the simple setup is stable. If YouTube shows `Audio renderer error`, Discord stops playing, or games lose audio after a device change, go back to the simple setup and keep Windows output on the real hardware device.
