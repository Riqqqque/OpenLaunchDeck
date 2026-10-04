import pytest

from openlaunchdeck.models.update_manifest import UpdateManifest


def valid_manifest():
    return {
        "latest_version": "0.2.0",
        "minimum_supported_version": "0.1.0",
        "required": False,
        "download_url": "https://github.com/Riqqqque/OpenLaunchDeck/releases/download/v0.1.33/OpenLaunchDeckSetup-0.1.33.exe",
        "sha256": "a" * 64,
        "release_notes_url": "https://github.com/Riqqqque/OpenLaunchDeck/releases/tag/v0.1.33",
        "published_at": "2026-01-01T00:00:00Z",
    }


def test_update_manifest_parses():
    manifest = UpdateManifest.from_dict(valid_manifest())

    assert manifest.latest_version == "0.2.0"
    assert manifest.required is False


def test_update_manifest_rejects_bad_checksum():
    data = valid_manifest()
    data["sha256"] = "bad"

    with pytest.raises(ValueError):
        UpdateManifest.from_dict(data)


def test_update_manifest_rejects_missing_required_field():
    data = valid_manifest()
    data.pop("download_url")

    with pytest.raises(ValueError, match="download_url"):
        UpdateManifest.from_dict(data)


def test_update_manifest_rejects_non_boolean_required_flag():
    data = valid_manifest()
    data["required"] = "false"

    with pytest.raises(ValueError):
        UpdateManifest.from_dict(data)


def test_update_manifest_rejects_invalid_version():
    data = valid_manifest()
    data["latest_version"] = "new"

    with pytest.raises(ValueError):
        UpdateManifest.from_dict(data)


def test_update_manifest_rejects_invalid_published_date():
    data = valid_manifest()
    data["published_at"] = "not-a-date"

    with pytest.raises(ValueError):
        UpdateManifest.from_dict(data)


def test_update_urls_require_https_except_loopback():
    from openlaunchdeck.models.update_manifest import is_trusted_update_url

    assert is_trusted_update_url("https://github.com/Riqqqque/OpenLaunchDeck/releases/download/v1/setup.exe")
    assert is_trusted_update_url("http://127.0.0.1:8000/manifest.json")
    assert is_trusted_update_url("http://localhost/manifest.json")
    assert not is_trusted_update_url("http://example.com/manifest.json")
    assert not is_trusted_update_url("ftp://example.com/setup.exe")
    assert not is_trusted_update_url("https:///setup.exe")
