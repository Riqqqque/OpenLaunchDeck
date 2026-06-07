# Discord Voice Chat Routing

OpenLaunchDeck handles the soundboard split itself. You do not need a separate mixer app for normal use: routed sounds can play to a voice route and to your headphones at the same time.

There is one Windows requirement: Discord must be able to select a recording device that receives the routed soundboard playback. OpenLaunchDeck can detect that route, but it cannot create a Windows recording endpoint without an audio driver.

## Goal

- Your microphone is heard in Discord.
- Routed OpenLaunchDeck soundboard clips are heard in Discord.
- You still hear Discord and soundboard clips through your normal output.
- Discord audio does not loop back into Discord.

## OpenLaunchDeck Setup

Open `Soundboard > Open Soundboard Panel`.

1. Set **Default Output** to `System default`.
2. Leave **Monitor Voice Routes** enabled.
3. Click **Auto Find Route**.
4. If the panel shows `Discord input: ...`, click **Copy Discord Input**.
5. For each soundboard button Discord should hear:
   - Select the button.
   - Set action type to `Play Sound`.
   - Choose the local audio file.
   - Enable `Route To Voice Chat`.
   - Start with volume around `60` to `80`.

If Auto Find Route cannot find a route, Windows does not currently expose a matching playback-to-recording bridge. Add a simple audio bridge endpoint or use hardware loopback from an audio interface, then run Auto Find Route again.

## Discord Settings

Open `User Settings > Voice & Video`.

Set:

- **Input Device:** the device shown by OpenLaunchDeck as `Discord input`
- **Output Device:** your real headphones, speakers, or audio interface
- **Audio Subsystem:** Standard

Keep Discord output on your real listening device. Do not route Discord output back into the same input Discord is using, or your friends may hear themselves.

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

If friends cannot hear clips:

- Confirm the button has `Route To Voice Chat` enabled.
- Confirm OpenLaunchDeck says the voice route is ready.
- Confirm Discord input matches the input name shown in the Soundboard panel.
- Confirm Discord input sensitivity opens when the clip plays.

If clips sound muffled, crunchy, or underwater:

- Turn off Discord noise suppression and automatic gain control.
- Use `.wav` or high-quality `.mp3` files.
- Lower the button volume slightly if the clip is clipping.
- Keep Discord output on your real headphones, speakers, or audio interface.

If you cannot hear your friends:

- Confirm Discord output is your real listening device.
- Confirm Windows output is your real listening device.
- Confirm OpenLaunchDeck Default Output is `System default`.

## Notes

OpenLaunchDeck does not install or bundle audio drivers. The app owns the soundboard routing logic, monitoring, volume, and diagnostics; Windows still owns audio endpoints.
