# Updating

OpenLaunchDeck uses a manifest-based update check for installer releases. The app never installs silently. A user starts a manual check from `Help > Check for Updates`, or enables a quiet startup check in Settings. Startup checks run in the background and only show a status message when an update is available.

## Version Source

The version source of truth is `openlaunchdeck/version.py`.

```python
APP_NAME = "OpenLaunchDeck"
__version__ = "0.1.0"
```

When preparing a release:

1. Update `__version__`.
2. Update `CHANGELOG.md`.
3. Run the build script.
4. Commit and push the release changes.
5. Push a `v<version>` tag.
6. Confirm the GitHub Release contains the installer, portable ZIP, and checksum files.
7. Update the remote manifest.

`build.ps1` reads the version from `openlaunchdeck/version.py` and passes it to the Inno Setup script.
The Release workflow uses the same build script and publishes release assets when a version tag is pushed. In GitHub Actions it uses the current runner Python, preinstalled dependencies, faster ZIP packaging, and faster installer compression to reduce tagged-release wait time.

## User Data

Program files live in the install folder. User data lives in:

`%APPDATA%\OpenLaunchDeck`

That folder contains:

- `settings.json`
- `profiles\`
- `logs\`
- `backups\`
- `midi_mappings\`
- `imported_assets\`
- `updates\`

The installer writes only application files to the install directory. It does not write profiles, settings, logs, backups, MIDI mappings, imported assets, or update downloads into the install folder. Upgrade installs replace program files and leave AppData untouched.

Before launching a downloaded installer, OpenLaunchDeck tries to back up profile JSON files into `%APPDATA%\OpenLaunchDeck\backups` when automatic profile backups are enabled.

## Manifest Format

```json
{
  "latest_version": "0.2.0",
  "minimum_supported_version": "0.1.0",
  "required": false,
  "download_url": "https://example.com/OpenLaunchDeckSetup-0.2.0.exe",
  "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "release_notes_url": "https://example.com/releases/tag/v0.2.0",
  "published_at": "2026-01-01T00:00:00Z"
}
```

The checksum in this example is a placeholder. Replace it with the real SHA256
for the installer before publishing a release manifest.

Rules:

- `latest_version` and `minimum_supported_version` must be valid semantic versions.
- `required` must be a JSON boolean.
- `download_url` must be HTTP or HTTPS.
- `sha256` must be the SHA256 checksum of the installer.
- `release_notes_url` may be empty, otherwise it must be HTTP or HTTPS.
- `published_at` must be ISO 8601.

The update service compares the current version with `latest_version`, checks whether the current version is below `minimum_supported_version`, and reports whether the update is optional or required.

## Download And Verification

Installer downloads are saved under:

`%APPDATA%\OpenLaunchDeck\updates`

The updater writes to a `.part` file first. When the download finishes, the file is moved into place and verified against the manifest SHA256. If verification fails, the downloaded file is deleted and the installer is not launched.

If the download fails, the current app stays open and usable.

## Manual Update Path

Manual updates are always supported:

1. Download the release installer.
2. Compare the installer SHA256 with the published checksum.
3. Close OpenLaunchDeck.
4. Run the installer.
5. Launch OpenLaunchDeck again.

Profiles and settings remain in AppData.

## GitHub Release Assets

Each tagged release should include:

- `OpenLaunchDeckSetup-<version>.exe`
- `OpenLaunchDeckSetup-<version>.exe.sha256`
- `OpenLaunchDeck-<version>-Windows.zip`
- `OpenLaunchDeck-<version>-Windows.zip.sha256`

Use the installer for normal updates. Use the ZIP for portable testing or troubleshooting.

## Local Update Testing

1. Build the installer:

   ```powershell
   powershell -ExecutionPolicy Bypass -File build.ps1 -RequireInstaller
   ```

2. Copy the installer to a local test web server folder.
3. Generate SHA256:

   ```powershell
   Get-FileHash .\OpenLaunchDeckSetup-0.2.0.exe -Algorithm SHA256
   ```

4. Create a manifest JSON using that checksum.
5. Serve the manifest and installer over HTTP.
6. Put the manifest URL in Settings.
7. Open `Help > Check for Updates`.
8. Confirm that the update can be detected, downloaded to AppData, verified, and launched only after user confirmation.

## Portable And Source Runs

Portable and source runs can check manifests and download verified installers, but replacing the currently running files may not apply to every setup. If automatic installer launch is not available, the dialog keeps the verified installer path visible so the user can run it manually.
