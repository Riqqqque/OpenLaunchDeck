# Release And Update Flow

OpenLaunchDeck publishes versioned Windows installers and portable ZIPs through GitHub Releases.

## For Users

### Install

Download `OpenLaunchDeckSetup-<version>.exe` from the [latest release](https://github.com/Riqqqque/OpenLaunchDeck/releases/latest).

The installer updates program files while user data remains under:

```text
%APPDATA%\OpenLaunchDeck
```

### Check For Updates

Use **Help > Check for Updates**.

The app can:

1. Read the latest GitHub release or a configured manifest.
2. Compare semantic versions.
3. Show whether the update is normal, required, or unsupported by the current version.
4. Download the installer outside the program folder.
5. Verify SHA256.
6. Ask before launching the installer.

It does not silently download and install updates by default.

### Manual Update

1. Download the latest installer and checksum.
2. Verify the checksum when needed.
3. Quit OpenLaunchDeck from the tray.
4. Run the installer.
5. Launch the app.
6. Confirm the version under **Help > About OpenLaunchDeck**.
7. Test one safe button.

### Preserved Data

- Settings
- Profiles
- Logs
- Backups
- MIDI mappings
- Imported assets
- Update metadata/downloads

Uninstalling the program does not need to remove this data. Delete the AppData folder separately only when you intentionally want to erase the setup.

## Release Assets

Each public release should include:

- `OpenLaunchDeckSetup-<version>.exe`
- Installer `.sha256`
- `OpenLaunchDeck-<version>-Windows.zip`
- Portable ZIP `.sha256`

The installer is the normal choice. The ZIP is for portable testing and diagnostics.

## For Maintainers

### Version Source

Update `openlaunchdeck/version.py`:

```python
APP_NAME = "OpenLaunchDeck"
__version__ = "0.1.0"
```

Keep the fallback version in `installer/openlaunchdeck.iss` synchronized. Update the changelog and any release-specific docs in the same commit.

### Build And Verify

```powershell
powershell -ExecutionPolicy Bypass -File build.ps1 -RequireInstaller
```

The build creates the application, installer, portable ZIP, and checksum files. It runs tests unless explicitly told not to.

Before release:

1. Install over the previous version.
2. Compare profile/settings data before and after.
3. Launch the installed application.
4. Test Simulation mode.
5. Test real Launchpad input/lighting when hardware behavior changed.
6. Test OBS and soundboard paths when they changed.
7. Verify installer and ZIP checksums.

Follow [the full release checklist](https://github.com/Riqqqque/OpenLaunchDeck/blob/main/docs/release_checklist.md).

### Publish

Push a tag matching the source version:

```powershell
git tag v<version>
git push origin v<version>
```

The Release workflow validates the tag, runs tests, builds Windows packages, verifies expected assets, and publishes the GitHub release.

### Custom Manifest

The optional JSON manifest contains:

- `latest_version`
- `minimum_supported_version`
- `required`
- `download_url`
- `sha256`
- `release_notes_url`
- `published_at`

Use placeholder URLs and checksums in examples. Never publish a manifest until the real installer exists and its SHA256 is known.

More technical detail is in [docs/updating.md](https://github.com/Riqqqque/OpenLaunchDeck/blob/main/docs/updating.md).
