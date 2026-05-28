import pytest

from openlaunchdeck.models.update_manifest import UpdateManifest


def valid_manifest():
    return {
        "latest_version": "0.2.0",
        "minimum_supported_version": "0.1.0",
        "required": False,
        "download_url": "https://example.com/OpenLaunchDeckSetup-0.2.0.exe",
        "sha256": "a" * 64,
        "release_notes_url": "https://example.com/releases/tag/v0.2.0",
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
