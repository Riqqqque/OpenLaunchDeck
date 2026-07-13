from __future__ import annotations

import subprocess
import sys
from pathlib import Path


class UpdateInstaller:
    def __init__(self, logger=None) -> None:
        self.logger = logger

    @staticmethod
    def install_mode() -> str:
        return "installed" if getattr(sys, "frozen", False) else "portable/source"

    @staticmethod
    def can_launch_installer() -> bool:
        return sys.platform == "win32"

    def launch(self, installer_path: Path) -> bool:
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
        subprocess.Popen([str(installer_path)], close_fds=True, cwd=str(installer_path.parent))
        return True
