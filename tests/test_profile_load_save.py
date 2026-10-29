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


def test_existing_server_profile_is_not_moved_automatically(tmp_path, monkeypatch):
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

    assert profile_path.exists()
    assert "server_admin" in service.profiles


def test_existing_soundboard_is_not_replaced_from_bundled_copy(tmp_path, monkeypatch):
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

    assert not (backups_dir / "refreshed_starter_profiles").exists()
    assert service.profiles["soundboard"].name == "Soundboard"
    assert old_marker in (profiles_dir / "soundboard.json").read_text(encoding="utf-8")


def test_empty_sound_slot_does_not_replace_custom_profile(tmp_path, monkeypatch):
    profiles_dir = tmp_path / "profiles"
    backups_dir = tmp_path / "backups"
    starters_dir = tmp_path / "starters"
    profiles_dir.mkdir()
    starters_dir.mkdir()
    custom = '{"name":"My Sounds","id":"soundboard","pages":[{"name":"Main","id":"main","buttons":{"A1":{"label":"Mine","action":{"type":"play_sound","config":{"file_path":""}}}}}]}'
    (profiles_dir / "soundboard.json").write_text(custom, encoding="utf-8")
    (starters_dir / "soundboard.json").write_text('{"name":"Bundled","id":"soundboard","pages":[]}', encoding="utf-8")
    monkeypatch.setattr(profile_service, "PROFILES_DIR", profiles_dir)
    monkeypatch.setattr(profile_service, "BACKUPS_DIR", backups_dir)
    monkeypatch.setattr(profile_service, "STARTER_PROFILES_DIR", starters_dir)

    service = profile_service.ProfileService()

    assert service.profiles["soundboard"].name == "My Sounds"
    assert not (backups_dir / "refreshed_starter_profiles").exists()


def test_import_profile_sanitizes_id_and_avoids_collision(tmp_path, monkeypatch):
    profiles_dir = tmp_path / "profiles"
    backups_dir = tmp_path / "backups"
    starters_dir = tmp_path / "starters"
    profiles_dir.mkdir()
    starters_dir.mkdir()
    (profiles_dir / "safe.json").write_text('{"name":"Existing","id":"safe","pages":[]}', encoding="utf-8")
    imported = tmp_path / "import.json"
    imported.write_text('{"name":"Imported","id":"../safe","pages":[]}', encoding="utf-8")
    monkeypatch.setattr(profile_service, "PROFILES_DIR", profiles_dir)
    monkeypatch.setattr(profile_service, "BACKUPS_DIR", backups_dir)
    monkeypatch.setattr(profile_service, "STARTER_PROFILES_DIR", starters_dir)
    service = profile_service.ProfileService()

    profile = service.import_profile(imported)

    assert profile.id == "safe_2"
    assert (profiles_dir / "safe_2.json").exists()
    assert not (tmp_path / "safe_2.json").exists()


def test_delete_profile_keeps_backup(tmp_path, monkeypatch):
    profiles_dir = tmp_path / "profiles"
    backups_dir = tmp_path / "backups"
    starters_dir = tmp_path / "starters"
    profiles_dir.mkdir()
    starters_dir.mkdir()
    (profiles_dir / "one.json").write_text('{"name":"One","id":"one","pages":[]}', encoding="utf-8")
    (profiles_dir / "two.json").write_text('{"name":"Two","id":"two","pages":[]}', encoding="utf-8")
    monkeypatch.setattr(profile_service, "PROFILES_DIR", profiles_dir)
    monkeypatch.setattr(profile_service, "BACKUPS_DIR", backups_dir)
    monkeypatch.setattr(profile_service, "STARTER_PROFILES_DIR", starters_dir)
    service = profile_service.ProfileService()

    assert service.delete_profile("two") is True
    assert "two" not in service.profiles
    assert not (profiles_dir / "two.json").exists()
    assert (backups_dir / "deleted_profiles" / "two.json").exists()


def test_new_profiles_never_overwrite_unloaded_or_renamed_files(tmp_path, monkeypatch):
    profiles_dir = tmp_path / "profiles"
    backups_dir = tmp_path / "backups"
    starters_dir = tmp_path / "starters"
    profiles_dir.mkdir()
    starters_dir.mkdir()
    renamed_path = profiles_dir / "work.json"
    renamed_path.write_text('{"name":"Gaming","id":"gaming","pages":[]}', encoding="utf-8")
    corrupt_path = profiles_dir / "stream.json"
    corrupt_path.write_text("{not json", encoding="utf-8")
    monkeypatch.setattr(profile_service, "PROFILES_DIR", profiles_dir)
    monkeypatch.setattr(profile_service, "BACKUPS_DIR", backups_dir)
    monkeypatch.setattr(profile_service, "STARTER_PROFILES_DIR", starters_dir)

    service = profile_service.ProfileService()
    service.create_profile("Work")
    service.create_profile("Stream")

    assert corrupt_path.read_text(encoding="utf-8") == "{not json"
    assert '"Gaming"' in renamed_path.read_text(encoding="utf-8")
    assert set(profile_service.ProfileService().profiles) == {"gaming", "work", "stream"}


def test_upgrade_gives_action_pads_on_dim_a_visible_color(tmp_path, monkeypatch):
    from openlaunchdeck.models.action_config import ActionConfig

    profiles_dir = tmp_path / "profiles"
    starters_dir = tmp_path / "starters"
    profiles_dir.mkdir()
    starters_dir.mkdir()
    monkeypatch.setattr(profile_service, "PROFILES_DIR", profiles_dir)
    monkeypatch.setattr(profile_service, "BACKUPS_DIR", tmp_path / "backups")
    monkeypatch.setattr(profile_service, "STARTER_PROFILES_DIR", starters_dir)
    service = profile_service.ProfileService()
    page = service.current_page
    page.buttons["B6"] = ButtonConfig(id="B6", label="expresso", color="dim", action=ActionConfig("play_sound", {"file_path": "x.mp3"}))
    page.buttons["B7"] = ButtonConfig(id="B7", color="dim", action=ActionConfig("hotkey", {}))
    page.buttons["C1"] = ButtonConfig(id="C1", color="red", action=ActionConfig("hotkey", {}))
    page.buttons["C2"] = ButtonConfig.blank("C2")

    assert service.upgrade_dim_action_pads() == 2

    reloaded = profile_service.ProfileService().current_page
    assert reloaded.get_button("B6").color == "blue"
    assert reloaded.get_button("B7").color == "blue"
    assert reloaded.get_button("C1").color == "red"
    assert reloaded.get_button("C2").color == "dim", "empty pads stay unlit"
