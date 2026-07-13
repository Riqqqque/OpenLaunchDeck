from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path
from typing import Protocol

from ..version import APP_NAME


RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


class StartupBackend(Protocol):
    def read(self, name: str) -> str | None:
        ...

    def write(self, name: str, value: str) -> None:
        ...

    def delete(self, name: str) -> None:
        ...


class WindowsRunKeyBackend:
    def __init__(self, key_path: str = RUN_KEY_PATH) -> None:
        import winreg

        self._winreg = winreg
        self._key_path = key_path

    def read(self, name: str) -> str | None:
        try:
            with self._winreg.OpenKey(self._winreg.HKEY_CURRENT_USER, self._key_path, 0, self._winreg.KEY_READ) as key:
                value, _ = self._winreg.QueryValueEx(key, name)
                return str(value)
        except FileNotFoundError:
            return None
        except OSError:
            return None

    def write(self, name: str, value: str) -> None:
        with self._winreg.CreateKeyEx(
            self._winreg.HKEY_CURRENT_USER,
            self._key_path,
            0,
            self._winreg.KEY_SET_VALUE,
        ) as key:
            self._winreg.SetValueEx(key, name, 0, self._winreg.REG_SZ, value)

    def delete(self, name: str) -> None:
        try:
            with self._winreg.OpenKey(
                self._winreg.HKEY_CURRENT_USER,
                self._key_path,
                0,
                self._winreg.KEY_SET_VALUE,
            ) as key:
                self._winreg.DeleteValue(key, name)
        except FileNotFoundError:
            return
        except OSError:
            return


def build_startup_command() -> str:
    if getattr(sys, "frozen", False):
        return subprocess.list2cmdline([sys.executable, "--background"])

    executable = Path(sys.executable)
    pythonw = executable.with_name("pythonw.exe")
    launcher = pythonw if sys.platform == "win32" and pythonw.exists() else executable
    return subprocess.list2cmdline([str(launcher), "-m", "openlaunchdeck.main", "--background"])


class StartupService:
    def __init__(
        self,
        logger: logging.Logger | None = None,
        backend: StartupBackend | None = None,
        platform: str = sys.platform,
        app_name: str = APP_NAME,
    ) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.app_name = app_name
        self._backend = backend
        if backend is None and platform == "win32":
            try:
                self._backend = WindowsRunKeyBackend()
            except Exception:
                self.logger.exception("Windows startup registration is unavailable.")
                self._backend = None

    def is_available(self) -> bool:
        return self._backend is not None

    def registered_command(self) -> str | None:
        if self._backend is None:
            return None
        return self._backend.read(self.app_name)

    def expected_command(self) -> str:
        return build_startup_command()

    def is_enabled(self) -> bool:
        return self.registered_command() is not None

    def is_current(self) -> bool:
        return self.registered_command() == self.expected_command()

    def set_enabled(self, enabled: bool) -> bool:
        if self._backend is None:
            if enabled:
                self.logger.warning("Launch at startup is only available on Windows.")
                return False
            return True

        try:
            if enabled:
                command = self.expected_command()
                self._backend.write(self.app_name, command)
                self.logger.info("Enabled launch at startup: %s", command)
            else:
                self._backend.delete(self.app_name)
                self.logger.info("Disabled launch at startup.")
            return True
        except Exception:
            self.logger.exception("Could not update Windows startup registration.")
            return False

    def sync(self, enabled: bool) -> bool:
        if enabled:
            if not self.is_current():
                return self.set_enabled(True)
            return True
        if self.is_enabled():
            return self.set_enabled(False)
        return True
