# Voice Chat Routing

OpenLaunchDeck handles the soundboard split itself. You do not need a separate mixer app for normal use: routed sounds can play to a voice route and to your headphones at the same time.

OpenLaunchDeck can also route your selected microphone into that same voice route. There is one Windows requirement: Discord, a game, or another voice app must be able to select a recording device that receives the routed playback. OpenLaunchDeck can detect that route, but it cannot create a Windows recording endpoint without an audio driver.

## Goal

- Your microphone is heard in Discord or game voice chat.
- Routed OpenLaunchDeck soundboard clips are heard in Discord or game voice chat.
- You still hear Discord, game audio, and soundboard clips through your normal output.
- App/game audio does not loop back into the voice input.

## OpenLaunchDeck Setup

Open `Soundboard > Open Soundboard Panel`.

1. Set **Default Output** to `System default`.
2. Leave **Monitor Voice Routes** enabled.
3. Click **Auto Find Route**.
4. If the panel shows `Voice chat input: ...`, click **Copy Voice Chat Input**.
5. Set **Microphone Input** to your mic, or leave it on `System default microphone`.
6. Enable **Route Microphone**.
7. Start **Microphone Volume** at `100`, then lower it if voice chat clips or distorts.
8. For each soundboard button voice chat should hear:
   - Select the button.
   - Set action type to `Play Sound`.
   - Choose the local audio file.
   - Enable `Route To Voice Chat`.
   - Start with volume around `60` to `80`.

If Auto Find Route cannot find a route, Windows does not currently expose a matching playback-to-recording bridge. Use one signed cable endpoint pair, a hardware loopback input from an audio interface, or a signed OpenLaunchDeck Audio Bridge package when that package is available. Then run Auto Find Route again.

A common lightweight cable setup appears as:

- Playback: `Speakers (VB-Audio Virtual Cable)`
- Recording: `CABLE Output (VB-Audio Virtual Cable)`

OpenLaunchDeck sends routed clips and the selected microphone to the playback side. Discord or a game uses the recording side as its input.

## OpenLaunchDeck Audio Bridge

When installed, the bridge appears as:

- Playback: `OpenLaunchDeck Voice Output`
- Recording: `OpenLaunchDeck Voice Input`

OpenLaunchDeck prefers this pair automatically. Set your voice chat input to `OpenLaunchDeck Voice Input`, keep voice chat output on your real listening device, and enable **Route Microphone** in the Soundboard panel.

See [audio_bridge.md](audio_bridge.md) for driver build and install requirements.

## Discord Settings

Open `User Settings > Voice & Video`.

Set:

- **Input Device:** the device shown by OpenLaunchDeck as `Voice chat input`
- **Output Device:** your real headphones, speakers, or audio interface
- **Audio Subsystem:** Standard

Keep Discord output on your real listening device. Do not route Discord output back into the same input Discord is using, or your friends may hear themselves.

If **Route Microphone** is enabled in OpenLaunchDeck, do not set Discord input to your real microphone. Discord should listen to the route input shown by OpenLaunchDeck, because that input contains both your mic and routed clips.

For better soundboard quality, turn off:

- Noise Suppression / Krisp
- Echo Cancellation
- Noise Reduction
- Automatic Gain Control

If Discord voice activity does not trigger when a clip plays, lower Discord's input sensitivity or use push-to-talk while testing.

## Game Voice Chat Settings

In games with built-in voice chat:

1. Open the game's audio or voice chat settings.
2. Set microphone/input device to the route recording device shown by OpenLaunchDeck.
3. Keep game output on your real headphones, speakers, or audio interface.
4. If the game uses push-to-talk, hold push-to-talk while pressing a routed soundboard button.
5. Test in a party, custom lobby, or other safe channel first.

When push-to-talk is held, the game transmits the route. That route contains your selected microphone and any soundboard clip with `Route To Voice Chat` enabled.

## Test Checklist

1. In Windows, play a normal system sound.
   - You should hear it through your headphones.
2. In Discord or a game, join a safe test call, party, or lobby.
   - You should hear other people through your real output.
3. Use Discord **Mic Test** or ask someone to confirm your microphone is audible.
4. In OpenLaunchDeck, press a routed soundboard button.
   - You should hear the clip.
   - Your friends should hear the clip.
5. Ask your friends whether the clip is too quiet, distorted, or muffled.

If friends cannot hear clips:

- Confirm the button has `Route To Voice Chat` enabled.
- Confirm OpenLaunchDeck says the voice route is ready.
- Confirm app/game input matches the input name shown in the Soundboard panel.
- Confirm Discord input sensitivity opens when the clip plays, or hold push-to-talk in games that require it.

If friends can hear clips but not your voice:

- Confirm **Route Microphone** is enabled in OpenLaunchDeck.
- Confirm **Microphone Input** points to your real mic or system default mic.
- Confirm **Microphone Volume** is not set to `0`.
- Confirm app/game input is the route input shown by OpenLaunchDeck, not your real mic.

If clips sound muffled, crunchy, or underwater:

- Turn off Discord noise suppression and automatic gain control.
- Use `.wav` or high-quality `.mp3` files.
- Lower the button volume slightly if the clip is clipping.
- Keep app/game output on your real headphones, speakers, or audio interface.

If you cannot hear your friends:

- Confirm app/game output is your real listening device.
- Confirm Windows output is your real listening device.
- Confirm OpenLaunchDeck Default Output is `System default`.

## Notes

OpenLaunchDeck does not install or bundle audio drivers. The app owns the soundboard routing logic, monitoring, volume, and diagnostics; Windows still owns audio endpoints.
