# Security Policy

## Supported Versions

Security fixes are prepared against the latest public release.

## Reporting A Vulnerability

Do not open a public issue for secrets, unsafe command behavior, updater problems, or other sensitive reports.

Use GitHub private vulnerability reporting if it is enabled for the repository. If it is not enabled, contact the maintainer through the public GitHub profile and request a private reporting channel.

Include:

- OpenLaunchDeck version
- Windows version
- Reproduction steps
- Impact
- Logs or diagnostic output with secrets removed

## Scope

Security-sensitive areas include update checks, downloaded installers, checksum verification, command execution actions, PowerShell actions, SSH actions, profile import, and file/path actions.

OpenLaunchDeck does not silently install updates. Installer downloads must pass SHA256 verification before launch.
