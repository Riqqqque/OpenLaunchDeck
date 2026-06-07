# OpenLaunchDeck Audio Bridge

OpenLaunchDeck Audio Bridge is the planned Windows audio endpoint pair for soundboard voice chat routing:

- Playback endpoint: `OpenLaunchDeck Voice Output`
- Recording endpoint: `OpenLaunchDeck Voice Input`

OpenLaunchDeck already mixes routed soundboard clips and the selected microphone into the voice route. Discord and games still need a Windows recording endpoint to select as their microphone input. This bridge component is that endpoint pair.

## Current State

The desktop app detects and prefers this bridge when the endpoint pair exists. The bridge driver itself must be built and signed separately before Windows will load it.

Windows audio endpoints are provided by drivers. A normal desktop process cannot create a system-wide recording device that Discord can select.

## Requirements

To build and install the bridge driver package:

- Visual Studio Build Tools with C++
- Windows Driver Kit
- A driver signing path for release builds
- Administrator rights for installation

Unsigned or test-signed drivers are for development machines only. Public releases need Microsoft-accepted driver signing.

## Safety Rules

- Do not install an unsigned driver package on a normal streaming or gaming PC.
- Do not enable Windows test-signing mode on a production setup.
- Do not uninstall an existing working route until `OpenLaunchDeck Voice Input` and `OpenLaunchDeck Voice Output` both appear in Windows.
- Always verify the driver package signature before installing.

## Build And Install Scripts

`build_audio_bridge.ps1` checks for the Windows driver build environment and a checked-in bridge driver source package.

`install_audio_bridge.ps1` installs only a signed bridge driver package.

`uninstall_audio_bridge.ps1` removes an installed bridge driver package by INF name.

These scripts intentionally fail clearly when prerequisites are missing. Silent fallback installs are not used for driver work.

## App Integration

OpenLaunchDeck looks for these exact endpoint names:

- `OpenLaunchDeck Voice Output`
- `OpenLaunchDeck Voice Input`

When both exist, the Soundboard panel reports the bridge as ready and Auto Find Route prefers it over other voice routes.
