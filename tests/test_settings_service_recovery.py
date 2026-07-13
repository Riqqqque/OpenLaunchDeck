from openlaunchdeck.services import settings_service


def test_corrupt_settings_are_backed_up_and_replaced(tmp_path, monkeypatch):
    settings_path = tmp_path / "settings.json"
    backups_path = tmp_path / "backups"
    settings_path.write_text("{broken", encoding="utf-8")
    monkeypatch.setattr(settings_service, "SETTINGS_FILE", settings_path)
    monkeypatch.setattr(settings_service, "BACKUPS_DIR", backups_path)

    service = settings_service.SettingsService()

    assert service.settings.theme == "dark"
    assert "defaults were loaded" in service.load_warning
    assert len(list(backups_path.glob("settings-corrupt-*.json"))) == 1
    assert "broken" not in settings_path.read_text(encoding="utf-8")
