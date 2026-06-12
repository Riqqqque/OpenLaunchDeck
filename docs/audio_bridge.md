# OpenLaunchDeck Audio Bridge

OpenLaunchDeck Audio Bridge is the driver-level piece needed for a clean built-in voice chat route.

The bridge provides two Windows endpoints:

- `OpenLaunchDeck Voice Output`
- `OpenLaunchDeck Voice Input`

OpenLaunchDeck plays routed soundboard clips and the selected microphone to `OpenLaunchDeck Voice Output`. Discord, a game voice chat app, or another voice app uses `OpenLaunchDeck Voice Input` as the microphone input.

## Why This Is Separate

Windows recording devices are created by audio drivers. A desktop app can play audio, record from a mic, and mix streams, but it cannot register a real system-wide microphone endpoint that Discord or games can select.

For public installs, the bridge driver must be signed through a valid Windows driver signing path before Windows will load it.

## App Behavior

When the bridge is installed, OpenLaunchDeck:

- Detects `OpenLaunchDeck Voice Output` and `OpenLaunchDeck Voice Input`
- Prefers that pair when you click **Auto Find Route**
- Shows the bridge status in the Soundboard panel
- Lets you route the microphone into the same path as routed soundboard clips

When the bridge is missing, the Soundboard panel says the bridge is not installed and continues to support any other valid route Windows exposes.

## Build Requirements

Building the bridge driver package requires:

- Visual Studio Build Tools with C++
- Windows Driver Kit
- Driver source under `audio_bridge/driver`
- A signing process for release packages

Run:

```powershell
powershell -ExecutionPolicy Bypass -File build.ps1 -BuildAudioBridge
```

The build fails clearly if the WDK or driver source is missing.

## Install Requirements

Driver installation requires Administrator rights and a valid driver catalog signature:

```powershell
powershell -ExecutionPolicy Bypass -File audio_bridge\install_audio_bridge.ps1
```

The install script refuses unsigned packages.

## Remove The Bridge

Run PowerShell as Administrator:

```powershell
powershell -ExecutionPolicy Bypass -File audio_bridge\uninstall_audio_bridge.ps1
```

## Voice Chat Setup

After installation:

1. Open `Soundboard > Open Soundboard Panel`.
2. Click **Auto Find Route**.
3. Confirm the bridge says it is ready.
4. Enable **Route Microphone**.
5. In Discord, game chat, or another voice app, set **Input Device** or **Microphone** to `OpenLaunchDeck Voice Input`.
6. Keep app/game **Output Device** on your real headphones, speakers, or audio interface.

For games with push-to-talk, hold push-to-talk while playing a routed soundboard clip.

Do not uninstall any old working audio route until this bridge pair appears in Windows and your voice app/game can hear both your microphone and routed soundboard clips.
