# Updater

OpenLaunchDeck update checks read a JSON manifest from a configured URL. The app compares the installed version to `latest_version`, checks `minimum_supported_version`, asks before installing, downloads the installer to `%APPDATA%\OpenLaunchDeck\updates`, verifies SHA256, and then launches the installer when supported.

Source and portable runs may not be able to replace their own files automatically. In that case, download and run the installer manually.
