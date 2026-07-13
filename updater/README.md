# Updater

OpenLaunchDeck checks the latest GitHub release by default and requires a matching installer `.sha256` asset. A custom JSON manifest URL can override that source for self-hosted deployments. The app compares versions, asks before installing, downloads the installer to `%APPDATA%\OpenLaunchDeck\updates`, verifies SHA256, and then launches the installer when supported.

Source and portable runs may not be able to replace their own files automatically. In that case, download and run the installer manually.
