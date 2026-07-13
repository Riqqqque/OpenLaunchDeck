# Release Checklist

## Version And Notes

- Update `openlaunchdeck/version.py`.
- Update `pyproject.toml` if publishing a Python package.
- Update `CHANGELOG.md`.
- Confirm README and installer references match the release version.

## Tests

- Run `pytest`.
- Launch the app from source with `python -m openlaunchdeck.main`.
- Verify simulation mode without hardware.
- Verify grid clicks select buttons for editing without running actions.
- Verify the selected button's Test control reaches the action runner.
- Verify profile save/load.
- Verify starter profiles load.
- Verify update manifest parsing and checksum failure handling.

## Build

- Run `powershell -ExecutionPolicy Bypass -File build.ps1 -SkipInstaller`.
- Confirm `dist\OpenLaunchDeck\OpenLaunchDeck.exe` launches.
- Confirm `dist\OpenLaunchDeck-<version>-Windows.zip` was created.
- Confirm `dist\OpenLaunchDeck-<version>-Windows.zip.sha256` was created.
- Run `powershell -ExecutionPolicy Bypass -File build.ps1` on a machine with Inno Setup.
- Confirm `dist\installer\OpenLaunchDeckSetup-<version>.exe` was created.
- Confirm `dist\installer\OpenLaunchDeckSetup-<version>.exe.sha256` was created.

## GitHub Release

- Commit the version bump, changelog, and docs.
- Push `main`.
- Tag the version as `v<version>`.
- Push the tag.
- Confirm the Release workflow passes.
- Compare the Release workflow duration against the previous tag and check slow step timings in the build log.
- Confirm the GitHub Release contains:
  - `OpenLaunchDeckSetup-<version>.exe`
  - `OpenLaunchDeckSetup-<version>.exe.sha256`
  - `OpenLaunchDeck-<version>-Windows.zip`
  - `OpenLaunchDeck-<version>-Windows.zip.sha256`
- Download the installer from the GitHub Release and run a clean install test.
- Download the ZIP from the GitHub Release and run a portable launch test.

## Installer

- Clean install on a test Windows user profile.
- Confirm Start Menu shortcut works.
- Confirm Start Menu shortcut uses the OpenLaunchDeck icon.
- Confirm optional Desktop shortcut works.
- Confirm Desktop shortcut uses the OpenLaunchDeck icon.
- Confirm first launch creates user data under `%APPDATA%\OpenLaunchDeck`.
- Upgrade install over the previous version.
- Confirm the installer closes or requests closing the running app before replacement.
- Confirm profiles, settings, logs, backups, MIDI mappings, and imported assets remain intact.
- Uninstall and confirm AppData remains intact.

## Update Manifest

- Leave the custom manifest URL empty and confirm the latest GitHub installer and checksum assets are detected.
- Confirm a GitHub release without its installer checksum is rejected.
- Complete the remaining items below when publishing through a custom manifest service.
- Set `latest_version`.
- Set `minimum_supported_version`.
- Set `required`.
- Set installer `download_url` to the GitHub Release installer asset.
- Set the real SHA256 from the GitHub Release installer checksum file.
- Set release notes URL.
- Set `published_at`.
- Test "You are up to date."
- Test "Update available."
- Test "Required update available."
- Test a checksum failure with an intentionally wrong checksum.
- Test a failed download and confirm the current app remains usable.

## Hardware

- Connect a Novation Launchpad Mini MK3.
- Put the device in Programmer Mode.
- Verify input and output ports in MIDI Debug.
- Verify A1-H8 pad mapping.
- Verify calibration save and restore default mapping.
- Verify page lighting refresh.
- Verify press, success, error, dangerous armed, and sound-playing feedback.
- Unplug and reconnect the device while the app is running.

## Soundboard

- Assign a local `.wav` file to a button.
- Assign a local `.mp3` file to a button.
- Verify missing files show a clear error.
- Verify unsupported extensions show a clear error.
- Verify restart, overlap, ignore, and toggle-stop behavior.
- Verify Stop Sound for one button, current page, and all sounds.
- Verify global soundboard volume.
- If testing OpenLaunchDeck Audio Bridge, verify `OpenLaunchDeck Voice Output` and `OpenLaunchDeck Voice Input` both appear in Windows.
- Verify Discord and at least one game voice chat path can hear both the microphone route and routed clips through the selected voice input.

## Documentation And Source Cleanliness

- Update README.
- Update the setup guide pages under `docs/wiki`.
- Publish the same setup guide content to the GitHub Wiki when the wiki remote is initialized.
- Update `docs/updating.md`.
- Update `docs/performance.md`.
- Update `docs/troubleshooting.md` if behavior changed.
- Add current screenshots under `docs/screenshots`.
- Run the blocked public-trace wording scan listed in the release issue.
- Confirm no machine-specific paths, private hostnames, personal network addresses, tokens, credentials, or local account details are present.
- Confirm no workspace-specific instruction file is present in the repository.
- Publish release notes with the installer checksum.
