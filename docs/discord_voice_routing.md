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

- **Output device:** `Voicemeeter AUX Input`
- **Input device:** `Voicemeeter Out B1`

Do not set Windows output directly to your headphones while Discord is routed through VoiceMeeter. VoiceMeeter should own the real hardware output.

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
6. On the AUX virtual input strip, usually labeled **Voicemeeter AUX**, enable `A1` and disable `B1`.
   - This strip receives Discord and normal Windows playback.
   - `A1` lets you hear it.
   - Leaving `B1` off prevents Discord audio from looping back into Discord.

Recommended starting levels:

- Hardware Input 1 gain: `0 dB`
- Voicemeeter Input gain: `0 dB`
- Voicemeeter AUX gain: `0 dB`
- A1 bus gain: `0 dB`

If soundboard clips distort, lower the Voicemeeter Input strip by `3 dB` to `6 dB`. If friends can barely hear clips, raise the OpenLaunchDeck button volume first.

## OpenLaunchDeck Settings

Open `Soundboard > Open Soundboard Panel`.

Set:

- **Default Output Device:** `Voicemeeter AUX Input`
- **Voice Chat Output:** `Voicemeeter Input`
- **Monitor Voice Routes:** off

This keeps normal/local sounds on the AUX strip and sends routed voice-chat sounds to the main VoiceMeeter strip. VoiceMeeter handles the local monitoring, so OpenLaunchDeck does not need to play a second monitor copy.

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
- **Output Device:** `Default` or `Voicemeeter AUX Input`
- **Audio Subsystem:** `Standard`

Do not set Discord output to your real headphones while VoiceMeeter is using that device as A1. If Discord tries to open the hardware output directly, playback can fail or behave inconsistently.

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

- Confirm Discord output is `Default` or `Voicemeeter AUX Input`.
- Confirm the VoiceMeeter AUX strip has `A1` enabled.
- Confirm the VoiceMeeter AUX strip has `B1` disabled.
- Confirm Hardware Out `A1` is your real headphones or audio interface.

If your friends hear themselves:

- Confirm the VoiceMeeter AUX strip has `B1` disabled.
- Confirm Discord output is not going to the same strip that feeds `B1`.

## Working Example

Example device choices from a typical setup:

- Hardware Out A1: `Headphones (USB DAC)`
- Hardware Input 1: `Microphone (USB audio interface)`
- Windows output: `Voicemeeter AUX Input`
- Windows input: `Voicemeeter Out B1`
- Discord output: `Voicemeeter AUX Input`
- Discord input: `Voicemeeter Out B1`
- OpenLaunchDeck default output: `Voicemeeter AUX Input`
- OpenLaunchDeck voice-chat output: `Voicemeeter Input`

Your device names may be different. Match the role of each device, not only the exact name.
