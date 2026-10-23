from openlaunchdeck.services import backup_service


def test_automatic_backups_keep_only_the_newest(tmp_path, monkeypatch):
    backups = tmp_path / "backups"
    profiles = tmp_path / "profiles"
    profiles.mkdir()
    (profiles / "main.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(backup_service, "BACKUPS_DIR", backups)
    monkeypatch.setattr(backup_service, "PROFILES_DIR", profiles)
    for day in range(1, 6):
        (backups / f"profiles-202601{day:02d}-120000").mkdir(parents=True)
    (backups / "manual").mkdir()
    (backups / "OpenLaunchDeck-full-pre-0.2.0.zip").write_bytes(b"zip")

    removed = backup_service.BackupService.prune_automatic_backups(keep=3)

    assert removed == ["profiles-20260101-120000", "profiles-20260102-120000"]
    assert sorted(path.name for path in backups.iterdir()) == [
        "OpenLaunchDeck-full-pre-0.2.0.zip",
        "manual",
        "profiles-20260103-120000",
        "profiles-20260104-120000",
        "profiles-20260105-120000",
    ]
    created = backup_service.BackupService().backup_profiles()
    assert (backups / created.split("\\")[-1].split("/")[-1] / "main.json").exists()
