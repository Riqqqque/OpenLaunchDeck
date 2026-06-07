from openlaunchdeck.models.button import ButtonConfig
from openlaunchdeck.models.profile import Profile
from openlaunchdeck.services import profile_service


def test_profile_round_trip_fills_missing_buttons():
    profile = Profile.from_dict(
        {
            "name": "Test",
            "id": "test",
            "default_page": "main",
            "pages": [
                {
                    "name": "Main",
                    "id": "main",
                    "buttons": {
                        "A1": {
                            "label": "Browser",
                            "color": "green",
                            "action": {"type": "open_url", "config": {"url": "https://github.com/Riqqqque/OpenLaunchDeck"}},
                        }
                    },
                }
            ],
        }
    )

    assert profile.get_page("main").get_button("A1").label == "Browser"
    assert len(profile.get_page("main").buttons) == 64
    assert profile.to_dict()["pages"][0]["buttons"]["H8"]["action"]["type"] == "noop"


def test_button_config_uses_target_slot_id_when_loaded_or_pasted():
    button = ButtonConfig.from_dict(
        "C4",
        {
            "id": "A8",
            "label": "Copied",
            "action": {"type": "volume_control", "config": {"mode": "volume_up"}},
        },
    )

    assert button.id == "C4"
    assert button.to_dict()["id"] == "C4"


def test_profile_service_repairs_stale_button_ids(tmp_path, monkeypatch):
    profiles_dir = tmp_path / "profiles"
    backups_dir = tmp_path / "backups"
    starters_dir = tmp_path / "starters"
    profiles_dir.mkdir()
    starters_dir.mkdir()
    profile_path = profiles_dir / "custom.json"
    profile_path.write_text(
        """
        {
          "name": "Custom",
          "id": "custom",
          "default_page": "main",
          "pages": [
            {
              "name": "Main",
              "id": "main",
              "buttons": {
                "C4": {
                  "id": "A8",
                  "label": "Copied",
                  "action": {"type": "volume_control", "config": {"mode": "volume_up"}}
                }
              }
            }
          ]
        }
        """,
        encoding="utf-8",
    )
    monkeypatch.setattr(profile_service, "PROFILES_DIR", profiles_dir)
    monkeypatch.setattr(profile_service, "BACKUPS_DIR", backups_dir)
    monkeypatch.setattr(profile_service, "STARTER_PROFILES_DIR", starters_dir)

    service = profile_service.ProfileService()

    assert service.profiles["custom"].get_page("main").buttons["C4"].id == "C4"
    assert '"id": "C4"' in profile_path.read_text(encoding="utf-8")


def test_retired_unconfigured_starter_profile_moves_to_backup(tmp_path, monkeypatch):
    profiles_dir = tmp_path / "profiles"
    backups_dir = tmp_path / "backups"
    starters_dir = tmp_path / "starters"
    profiles_dir.mkdir()
    starters_dir.mkdir()
    profile_path = profiles_dir / "server_admin.json"
    retired_marker = "replace" + "-this-command"
    profile_path.write_text(
        f'{{"name":"Server Admin","id":"server_admin","pages":[],"command":"{retired_marker}"}}',
        encoding="utf-8",
    )
    monkeypatch.setattr(profile_service, "PROFILES_DIR", profiles_dir)
    monkeypatch.setattr(profile_service, "BACKUPS_DIR", backups_dir)
    monkeypatch.setattr(profile_service, "STARTER_PROFILES_DIR", starters_dir)

    service = profile_service.ProfileService()

    assert not profile_path.exists()
    assert (backups_dir / "retired_starter_profiles" / "server_admin.json").exists()
    assert "server_admin" not in service.profiles


def test_outdated_starter_profile_refreshes_from_bundled_copy(tmp_path, monkeypatch):
    profiles_dir = tmp_path / "profiles"
    backups_dir = tmp_path / "backups"
    starters_dir = tmp_path / "starters"
    profiles_dir.mkdir()
    starters_dir.mkdir()
    old_marker = "plan" + "ned"
    (profiles_dir / "soundboard.json").write_text(
        f'{{"name":"Soundboard","id":"soundboard","pages":[],"notes":"{old_marker}"}}',
        encoding="utf-8",
    )
    (starters_dir / "soundboard.json").write_text(
        '{"name":"Soundboard","id":"soundboard","default_page":"main","pages":[{"name":"Main","id":"main","buttons":{}}]}',
        encoding="utf-8",
    )
    monkeypatch.setattr(profile_service, "PROFILES_DIR", profiles_dir)
    monkeypatch.setattr(profile_service, "BACKUPS_DIR", backups_dir)
    monkeypatch.setattr(profile_service, "STARTER_PROFILES_DIR", starters_dir)

    service = profile_service.ProfileService()

    assert (backups_dir / "refreshed_starter_profiles" / "soundboard.json").exists()
    assert service.profiles["soundboard"].name == "Soundboard"
    assert old_marker not in (profiles_dir / "soundboard.json").read_text(encoding="utf-8")
