import hashlib
import sys

import pytest

from openlaunchdeck.models.update_manifest import UpdateManifest
from openlaunchdeck.services.update_service import UpdateService


def test_update_checksum_verification_with_local_file(tmp_path):
    file_path = tmp_path / "update.exe"
    file_path.write_bytes(b"local update bytes")
    expected = hashlib.sha256(b"local update bytes").hexdigest()

    assert UpdateService.verify_sha256(file_path, expected) is True
    assert UpdateService.verify_sha256(file_path, "0" * 64) is False


def test_download_deletes_installer_when_checksum_fails(tmp_path, monkeypatch):
    class ResponseTestDouble:
        headers = {"content-length": "12"}

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def raise_for_status(self):
            return None

        def iter_content(self, chunk_size):
            yield b"wrong bytes"

    class RequestsTestDouble:
        @staticmethod
        def get(*args, **kwargs):
            return ResponseTestDouble()

    monkeypatch.setitem(sys.modules, "requests", RequestsTestDouble)
    manifest = UpdateManifest.from_dict(
        {
            "latest_version": "0.2.0",
            "minimum_supported_version": "0.1.0",
            "required": False,
            "download_url": "https://github.com/Riqqqque/OpenLaunchDeck/releases/download/v0.1.33/OpenLaunchDeckSetup-0.1.33.exe",
            "sha256": hashlib.sha256(b"expected bytes").hexdigest(),
            "release_notes_url": "https://github.com/Riqqqque/OpenLaunchDeck/releases/tag/v0.1.33",
            "published_at": "2026-01-01T00:00:00Z",
        }
    )

    with pytest.raises(ValueError):
        UpdateService("0.1.0").download(manifest, tmp_path)

    assert list(tmp_path.iterdir()) == []

