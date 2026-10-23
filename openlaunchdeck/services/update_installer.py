from __future__ import annotations

import subprocess
import sys
from pathlib import Path


# Inno Setup switches for a one-click update: no wizard pages, close the running app,
# and /RELAUNCH=1 tells our installer script to start OpenLaunchDeck again when done.
SILENT_UPDATE_ARGUMENTS = ["/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/CLOSEAPPLICATIONS", "/RELAUNCH=1"]
DETACHED_PROCESS = 0x00000008
CREATE_BREAKAWAY_FROM_JOB = 0x01000000


class UpdateInstaller:
    def __init__(self, logger=None) -> None:
        self.logger = logger

    @staticmethod
    def install_mode() -> str:
        return "installed" if getattr(sys, "frozen", False) else "portable/source"

    @staticmethod
    def can_launch_installer() -> bool:
        return sys.platform == "win32"

    def launch(self, installer_path: Path, silent: bool = False) -> bool:
        """Start the installer. Silent updates show no wizard and reopen the app afterwards."""
        if not installer_path.exists():
            raise FileNotFoundError(installer_path)
        if installer_path.suffix.casefold() != ".exe":
            raise ValueError("OpenLaunchDeck updates must use a Windows .exe installer.")
        if not self.can_launch_installer():
            if self.logger:
                self.logger.info("Installer launch is not available on this platform.")
            return False
        if self.logger:
            self.logger.info("Launching update installer: %s", installer_path)
        command = [str(installer_path)]
        if silent:
            command += SILENT_UPDATE_ARGUMENTS
        try:
            # Detach from the app's job so the installer keeps running after the app quits.
            subprocess.Popen(
                command,
                close_fds=True,
                cwd=str(installer_path.parent),
                creationflags=DETACHED_PROCESS | CREATE_BREAKAWAY_FROM_JOB,
            )
        except OSError:
            subprocess.Popen(command, close_fds=True, cwd=str(installer_path.parent), creationflags=DETACHED_PROCESS)
        return True
