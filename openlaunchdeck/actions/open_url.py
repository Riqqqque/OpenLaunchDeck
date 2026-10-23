from __future__ import annotations

import os
import re
import subprocess
import webbrowser
from pathlib import Path
from urllib.parse import urlparse

from .base import ActionResult, BaseAction

# A browser launcher hands the URL to the running browser and exits within a moment.
# If the browser wasn't running, the launcher becomes the browser and keeps running.
LAUNCHER_WAIT_SECONDS = 1.5
# Set by Chromium-based apps (Electron, editors, chat apps) for their own crash handler.
# A browser started with it may try to use that app's handler instead of its own.
_FOREIGN_BROWSER_VARIABLES = ("CHROME_CRASHPAD_PIPE_NAME",)


class OpenUrlAction(BaseAction):
    type_name = "open_url"
    display_name = "Open URL"
    description = "Open a website in the default browser, optionally in a private window."
    config_fields = [
        {"name": "url", "label": "URL", "type": "text", "placeholder": "https://example.com"},
        {"name": "private_window", "label": "Open In Private Window", "type": "bool"},
    ]
    blocking = True

    def validate(self, config: dict) -> list[str]:
        return [] if normalize_http_url(config.get("url")) else ["Enter a valid HTTP or HTTPS URL."]

    def execute(self, context, config: dict) -> ActionResult:
        url = normalize_http_url(config.get("url"))
        if url is None:
            return ActionResult.fail("Enter a valid HTTP or HTTPS URL.")
        if bool(config.get("private_window", False)):
            return _open_private_window(url)
        opened = webbrowser.open(url)
        if not opened:
            return ActionResult.fail("Windows did not accept the URL open request.")
        return ActionResult.ok(f"Opened {url}.")


_EXECUTABLE_PATTERN = re.compile(r'^\s*(?:"([^"]+\.exe)"|([^\s]+\.exe))(?:\s|$)', re.IGNORECASE)
_EXPLICIT_SCHEME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
_HOST_PORT_PATTERN = re.compile(r"^[A-Za-z0-9.-]+:\d+(?:[/?#]|$)")


def normalize_http_url(value: object) -> str | None:
    raw = str(value or "").strip()
    if not raw or any(character.isspace() or ord(character) < 32 for character in raw):
        return None
    if "\\" in raw:
        return None

    lowered = raw.lower()
    if lowered.startswith(("http://", "https://")):
        candidate = raw
    elif raw.startswith("//"):
        candidate = f"https:{raw}"
    elif _HOST_PORT_PATTERN.match(raw):
        candidate = f"https://{raw}"
    elif _EXPLICIT_SCHEME_PATTERN.match(raw):
        return None
    else:
        candidate = f"https://{raw}"

    try:
        parsed = urlparse(candidate)
        hostname = parsed.hostname
        _ = parsed.port
    except ValueError:
        return None
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc or not hostname:
        return None
    return candidate


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

    browser_name = Path(executable).stem or "The browser"
    try:
        process = subprocess.Popen(command, close_fds=True, env=_browser_environment())
    except OSError as exc:
        return ActionResult.fail(f"Could not open a private browser window: {exc}")
    exit_code = _launcher_exit_code(process)
    if exit_code not in (None, 0):
        return ActionResult.fail(
            f"{browser_name} didn't open the private window (exit code {exit_code}). Try again, or restart {browser_name}."
        )
    return ActionResult.ok(f"Opened {url} in a private window.")


def _browser_environment() -> dict[str, str]:
    environment = dict(os.environ)
    for name in _FOREIGN_BROWSER_VARIABLES:
        environment.pop(name, None)
    return environment


def _launcher_exit_code(process) -> int | None:
    try:
        return process.wait(timeout=LAUNCHER_WAIT_SECONDS)
    except subprocess.TimeoutExpired:
        return None


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
