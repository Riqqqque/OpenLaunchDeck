# Installer

`openlaunchdeck.iss` is the Inno Setup script for the Windows installer.

The installer writes program files to the selected install location and leaves user data in `%APPDATA%\OpenLaunchDeck`. Upgrade installs should replace app files without touching profiles, logs, settings, backups, or MIDI mappings.

`build.ps1` passes the version from `openlaunchdeck/version.py` into Inno Setup and writes a `.sha256` file beside the installer. The Inno script does not remove AppData during upgrade or uninstall.

Build from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File build.ps1
```
