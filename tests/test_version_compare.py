from openlaunchdeck.services.update_service import UpdateService


def manifest_data(**overrides):
    data = {
        "latest_version": "0.2.0",
        "minimum_supported_version": "0.1.0",
        "required": False,
        "download_url": "https://github.com/Riqqqque/OpenLaunchDeck/releases/download/v0.1.33/OpenLaunchDeckSetup-0.1.33.exe",
        "sha256": "a" * 64,
        "release_notes_url": "https://github.com/Riqqqque/OpenLaunchDeck/releases/tag/v0.1.33",
        "published_at": "2026-01-01T00:00:00Z",
    }
    data.update(overrides)
    return data


def test_version_compare_detects_newer_version():
    service = UpdateService("0.1.0")

    assert service.is_newer("0.2.0") is True
    assert service.is_newer("0.1.0") is False


def test_update_check_reports_no_update_available():
    service = UpdateService("0.2.0")

    result = service.check_manifest_data(manifest_data())

    assert result.available is False
    assert result.message == "You are up to date."


def test_update_check_reports_update_available():
    service = UpdateService("0.1.0")

    result = service.check_manifest_data(manifest_data())

    assert result.available is True
    assert result.required is False
    assert result.latest_version == "0.2.0"


def test_update_check_reports_required_update():
    service = UpdateService("0.1.0")

    result = service.check_manifest_data(manifest_data(required=True))

    assert result.available is True
    assert result.required is True
    assert result.message == "Required update available."


def test_update_check_reports_unsupported_current_version():
    service = UpdateService("0.1.0")

    result = service.check_manifest_data(manifest_data(minimum_supported_version="0.2.0"))

    assert result.available is True
    assert result.required is True
    assert result.unsupported is True
    assert "minimum supported version" in result.message
