from pathlib import Path

import pytest

from openlaunchdeck.actions import open_url
from openlaunchdeck.actions.open_url import OpenUrlAction


def test_normal_url_uses_windows_default_handler(monkeypatch):
    opened = []
    monkeypatch.setattr(open_url.webbrowser, "open", lambda url: opened.append(url) or True)

    result = OpenUrlAction().execute(None, {"url": "https://example.com"})

    assert result.success is True
    assert opened == ["https://example.com"]


def test_private_url_launches_default_brave_in_incognito(monkeypatch, tmp_path):
    browser = tmp_path / "brave.exe"
    browser.write_bytes(b"")
    launched = []
    monkeypatch.setattr(open_url.os, "name", "nt")
    monkeypatch.setattr(open_url, "_default_browser_registration", lambda _scheme: (str(browser), "BraveHTML"))
    monkeypatch.setattr(open_url.subprocess, "Popen", lambda command, **kwargs: launched.append((command, kwargs)))

    result = OpenUrlAction().execute(
        None,
        {"url": "https://example.com/private", "private_window": True},
    )

    assert result.success is True
    assert launched == [([str(browser), "--incognito", "https://example.com/private"], {"close_fds": True})]


def test_private_url_does_not_fall_back_to_normal_window(monkeypatch, tmp_path):
    browser = tmp_path / "unknown.exe"
    browser.write_bytes(b"")
    normal_opened = []
    monkeypatch.setattr(open_url.os, "name", "nt")
    monkeypatch.setattr(open_url, "_default_browser_registration", lambda _scheme: (str(browser), "UnknownHTML"))
    monkeypatch.setattr(open_url.webbrowser, "open", lambda url: normal_opened.append(url) or True)

    result = OpenUrlAction().execute(None, {"url": "https://example.com", "private_window": True})

    assert result.success is False
    assert "not supported" in result.message.lower()
    assert normal_opened == []


@pytest.mark.parametrize(
    ("executable", "prog_id", "expected_switch"),
    [
        ("brave.exe", "BraveHTML", "--incognito"),
        ("chrome.exe", "ChromeHTML", "--incognito"),
        ("chromium.exe", "ChromiumHTM", "--incognito"),
        ("vivaldi.exe", "VivaldiHTM", "--incognito"),
        ("msedge.exe", "MSEdgeHTM", "--inprivate"),
        ("firefox.exe", "FirefoxURL", "-private-window"),
    ],
)
def test_private_browser_switches(executable, prog_id, expected_switch):
    command = open_url._private_browser_command(executable, prog_id, "https://example.com")

    assert command == [executable, expected_switch, "https://example.com"]


def test_extract_executable_handles_quoted_windows_command(tmp_path):
    browser = tmp_path / "browser.exe"
    browser.write_bytes(b"")
    command = f'"{browser}" --single-argument %1'

    assert Path(open_url._extract_executable(command)) == browser


def test_open_url_rejects_non_http_address(monkeypatch):
    monkeypatch.setattr(open_url.webbrowser, "open", lambda _url: pytest.fail("invalid URL was opened"))

    result = OpenUrlAction().execute(None, {"url": "file:///C:/Windows/win.ini", "private_window": True})

    assert result.success is False
    assert "valid HTTP or HTTPS" in result.message


def test_private_window_is_exposed_as_boolean_editor_field():
    field = next(item for item in OpenUrlAction.config_fields if item["name"] == "private_window")

    assert field == {"name": "private_window", "label": "Open In Private Window", "type": "bool"}
