from __future__ import annotations

import sys

from openlaunchdeck.services import startup_service
from openlaunchdeck.services.startup_service import StartupService, build_startup_command


class MemoryStartupBackend:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def read(self, name: str) -> str | None:
        return self.values.get(name)

    def write(self, name: str, value: str) -> None:
        self.values[name] = value

    def delete(self, name: str) -> None:
        self.values.pop(name, None)


def test_startup_service_enables_and_disables_registry_entry(monkeypatch):
    backend = MemoryStartupBackend()
    monkeypatch.setattr(
        startup_service,
        "build_startup_command",
        lambda: r'"C:\Program Files\OpenLaunchDeck\OpenLaunchDeck.exe" --background',
    )
    service = StartupService(backend=backend, app_name="OpenLaunchDeck")

    assert service.set_enabled(True)
    assert backend.values["OpenLaunchDeck"] == r'"C:\Program Files\OpenLaunchDeck\OpenLaunchDeck.exe" --background'
    assert service.is_enabled()
    assert service.is_current()

    assert service.set_enabled(False)
    assert backend.values == {}
    assert not service.is_enabled()


def test_startup_service_sync_repairs_stale_command(monkeypatch):
    backend = MemoryStartupBackend()
    backend.values["OpenLaunchDeck"] = r'"C:\Old\OpenLaunchDeck.exe"'
    monkeypatch.setattr(startup_service, "build_startup_command", lambda: r'"C:\New\OpenLaunchDeck.exe" --background')
    service = StartupService(backend=backend, app_name="OpenLaunchDeck")

    assert service.sync(True)
    assert backend.values["OpenLaunchDeck"] == r'"C:\New\OpenLaunchDeck.exe" --background'


def test_startup_service_unavailable_does_not_enable():
    service = StartupService(backend=None, platform="linux")

    assert not service.is_available()
    assert not service.set_enabled(True)
    assert service.set_enabled(False)


def test_source_startup_command_uses_module_entrypoint(monkeypatch, tmp_path):
    python = tmp_path / "python.exe"
    python.write_text("", encoding="utf-8")
    monkeypatch.setattr(sys, "executable", str(python))
    monkeypatch.delattr(sys, "frozen", raising=False)

    command = build_startup_command()

    assert "-m openlaunchdeck.main" in command
    assert "--background" in command
