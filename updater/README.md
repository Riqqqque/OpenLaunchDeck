# Updater

OpenLaunchDeck checks the latest GitHub Release by default. An update is offered only when the release contains both the versioned Windows installer and its matching `.sha256` file.

The updater:

1. Checks for a newer semantic version in the background.
2. Asks before downloading or installing anything.
3. Downloads to `%APPDATA%\OpenLaunchDeck\updates`, outside the program folder.
4. Verifies the complete installer with SHA256.
5. Refuses to launch the installer if verification fails.

A custom JSON manifest URL can replace the GitHub Release source for self-hosted deployments. Source and portable runs can still check and download an update, but users may need to close the app and run the verified installer manually.

See [Updating](../docs/updating.md) for the manifest format, local testing, release assets, and user-data guarantees.
