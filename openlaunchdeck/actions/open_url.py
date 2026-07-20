from __future__ import annotations

import os
import re
import subprocess
import webbrowser
from pathlib import Path
from urllib.parse import urlparse

from .base import ActionResult, BaseAction


class OpenUrlAction(BaseAction):
    type_name = "open_url"
    display_name = "Open URL"
    description = "Open a URL in the default browser, optionally in a private window."
    config_fields = [
        {"name": "url", "label": "URL", "type": "text"},
        {"name": "private_window", "label": "Open In Private Window", "type": "bool"},
    ]
    blocking = True

    def validate(self, config: dict) -> list[str]:
        url = str(config.get("url") or "")
        parsed = urlparse(url)
        return [] if parsed.scheme in {"http", "https"} and parsed.netloc else ["Enter a valid HTTP or HTTPS URL."]

    def execute(self, context, config: dict) -> ActionResult:
        errors = self.validate(config)
        if errors:
            return ActionResult.fail(errors[0])
        url = str(config["url"])
        if bool(config.get("private_window", False)):
            return _open_private_window(url)
        opened = webbrowser.open(url)
        if not opened:
            return ActionResult.fail("Windows did not accept the URL open request.")
        return ActionResult.ok(f"Opened {url}.")


_EXECUTABLE_PATTERN = re.compile(r'^\s*(?:"([^"]+\.exe)"|([^\s]+\.exe))(?:\s|$)', re.IGNORECASE)


def _open_private_window(url: str) -> ActionResult:
    if os.name != "nt":
        return ActionResult.fail("Private-window URL opening is currently supported on Windows only.")

    executable, prog_id = _default_browser_registration(urlparse(url).scheme)
    if not executable:
        return ActionResult.fail("Could not find the executable for the Windows default browser.")

    command = _private_browser_command(executable, prog_id, url)
    if command is None:
        browser_name = Path(executable).stem or "current browser"
        return ActionResult.fail(f"Private-window opening is not supported for the default browser ({browser_name}).")

    try:
        subprocess.Popen(command, close_fds=True)
    except OSError as exc:
        return ActionResult.fail(f"Could not open a private browser window: {exc}")
    return ActionResult.ok(f"Opened {url} in a private window.")


def _default_browser_registration(scheme: str) -> tuple[str, str]:
    try:
        import winreg
    except ImportError:
        return "", ""

    prog_id = _read_registry_string(
        winreg.HKEY_CURRENT_USER,
        rf"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\{scheme}\UserChoice",
        "ProgId",
    )
    command = ""
    if prog_id:
        command = _read_registry_string(
            winreg.HKEY_CLASSES_ROOT,
            rf"{prog_id}\shell\open\command",
            "",
        )
    if not command:
        command = _read_registry_string(
            winreg.HKEY_CLASSES_ROOT,
            rf"{scheme}\shell\open\command",
            "",
        )
    return _extract_executable(command), prog_id


def _read_registry_string(root, path: str, value_name: str) -> str:
    try:
        import winreg

        with winreg.OpenKey(root, path) as key:
            value, _value_type = winreg.QueryValueEx(key, value_name)
    except (ImportError, OSError):
        return ""
    return str(value or "").strip()


def _extract_executable(command: str) -> str:
    match = _EXECUTABLE_PATTERN.match(str(command or ""))
    if not match:
        return ""
    executable = os.path.expandvars(match.group(1) or match.group(2) or "")
    return executable if Path(executable).is_file() else ""


def _private_browser_command(executable: str, prog_id: str, url: str) -> list[str] | None:
    identity = f"{Path(executable).name} {prog_id}".lower()
    if "msedge" in identity:
        return [executable, "--inprivate", url]
    if "firefox" in identity:
        return [executable, "-private-window", url]
    if any(browser in identity for browser in ("brave", "chrome", "chromium", "vivaldi")):
        return [executable, "--incognito", url]
    return None
