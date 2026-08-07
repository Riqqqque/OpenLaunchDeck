import json
import sys
from urllib.parse import parse_qs, urlparse

import pytest

from openlaunchdeck.models.settings import Settings
from openlaunchdeck.models.sound_library import SoundLibraryItem
from openlaunchdeck.services import sound_library_service as library_module
from openlaunchdeck.services.secret_store import protect_secret, unprotect_secret
from openlaunchdeck.services.sound_library_service import SoundLibraryError, SoundLibraryService


class SettingsServiceDouble:
    def __init__(self) -> None:
        self.settings = Settings()
        self.saved = []

    def update(self, **changes):
        self.saved.append(changes)
        for key, value in changes.items():
            setattr(self.settings, key, value)
        return self.settings


def _provider_item(**changes):
    data = {
        "id": 42,
        "name": "Short reaction.wav",
        "username": "sound-maker",
        "license": "Creative Commons 0",
        "duration": 1.25,
        "previews": {"preview-hq-mp3": "https://cdn.freesound.org/previews/42/42.mp3"},
        "url": "https://freesound.org/people/sound-maker/sounds/42/",
        "num_downloads": 1234,
        "avg_rating": 4.5,
        "created": "2026-01-01T00:00:00Z",
        "tags": ["reaction", "short"],
        "is_explicit": False,
    }
    data.update(changes)
    return data


def test_search_url_uses_safe_filters_without_exposing_api_key(tmp_path, monkeypatch):
    monkeypatch.setattr(library_module, "SOUND_LIBRARY_DIR", tmp_path)
    service = SoundLibraryService()

    url = service.build_search_url("  crowd   cheer  ", sort="created_desc", license_filter="cc0", maximum_duration=15, page=2)
    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    assert parsed.scheme == "https"
    assert parsed.hostname == "freesound.org"
    assert parsed.path == "/apiv2/search/text/"
    assert query["query"] == ["crowd cheer"]
    assert query["sort"] == ["created_desc"]
    assert query["page"] == ["2"]
    assert "is_explicit:false" in query["filter"][0]
    assert 'license:"Creative Commons 0"' in query["filter"][0]
    assert "token" not in query


def test_search_payload_rejects_bad_data_and_skips_unsafe_results(tmp_path, monkeypatch):
    monkeypatch.setattr(library_module, "SOUND_LIBRARY_DIR", tmp_path)
    service = SoundLibraryService()
    payload = {
        "count": 5,
        "next": "next",
        "previous": None,
        "results": [
            _provider_item(),
            _provider_item(id=43, is_explicit=True),
            _provider_item(id=44, previews={"preview-hq-mp3": "https://example.com/not-trusted.mp3"}),
            _provider_item(id=45, previews={"preview-hq-mp3": "https://[broken"}),
            _provider_item(id=46, previews={"preview-hq-mp3": "https://cdn.freesound.org:444/46.mp3"}),
        ],
    }

    page = service.parse_search_payload(json.dumps(payload), 1)

    assert [item.sound_id for item in page.items] == [42]
    assert page.total == 5
    assert page.has_next is True
    with pytest.raises(SoundLibraryError, match="invalid data"):
        service.parse_search_payload(b"not json", 1)
    with pytest.raises(SoundLibraryError, match="incomplete"):
        service.parse_search_payload(b"{}", 1)


def test_search_payload_normalizes_non_finite_numbers(tmp_path, monkeypatch):
    monkeypatch.setattr(library_module, "SOUND_LIBRARY_DIR", tmp_path)
    service = SoundLibraryService()
    payload = {"count": 1, "results": [_provider_item(duration=float("nan"), avg_rating=float("inf"))]}

    page = service.parse_search_payload(json.dumps(payload), 1)

    assert page.items[0].duration == 0.0
    assert page.items[0].rating == 0.0


def test_download_finalization_stays_in_library_and_writes_attribution(tmp_path, monkeypatch):
    monkeypatch.setattr(library_module, "SOUND_LIBRARY_DIR", tmp_path)
    service = SoundLibraryService()
    item = SoundLibraryItem(
        provider="Freesound",
        sound_id=42,
        name="Reaction sound",
        creator="sound-maker",
        license_name="Creative Commons 0",
        duration=1.0,
        preview_url="https://cdn.freesound.org/previews/42/42.mp3",
        source_url="https://freesound.org/people/sound-maker/sounds/42/",
    )
    part_path = service.part_path(item)
    part_path.write_bytes(b"ID3\x04\x00\x00test-audio")

    destination = service.finalize_download(item, part_path)

    assert destination.parent == tmp_path
    assert destination.read_bytes().startswith(b"ID3")
    metadata = json.loads(destination.with_suffix(".json").read_text(encoding="utf-8"))
    assert metadata["sound_id"] == 42
    assert metadata["audio_file"] == destination.name
    attribution = (tmp_path / "ATTRIBUTION.txt").read_text(encoding="utf-8")
    assert "sound-maker" in attribution
    assert not part_path.exists()


def test_local_import_deduplicates_and_rejects_bad_files(tmp_path, monkeypatch):
    library = tmp_path / "library"
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    monkeypatch.setattr(library_module, "SOUND_LIBRARY_DIR", library)
    service = SoundLibraryService()
    source = source_dir / "my clip.wav"
    source.write_bytes(b"RIFF" + b"\x00" * 64)

    first = service.import_local_file(source)
    second = service.import_local_file(source)

    assert first == second
    assert first.parent == library
    assert first.read_bytes() == source.read_bytes()
    assert len(service.local_items()) == 1
    invalid = source_dir / "clip.txt"
    invalid.write_text("not audio", encoding="utf-8")
    with pytest.raises(SoundLibraryError, match="WAV, MP3, or OGG"):
        service.import_local_file(invalid)


def test_api_key_is_protected_and_never_saved_as_plain_text(tmp_path, monkeypatch):
    monkeypatch.setattr(library_module, "SOUND_LIBRARY_DIR", tmp_path)
    monkeypatch.setattr(library_module, "protect_secret", lambda value: f"protected:{value[::-1]}")
    monkeypatch.setattr(library_module, "unprotect_secret", lambda value: value.removeprefix("protected:")[::-1])
    settings = SettingsServiceDouble()
    service = SoundLibraryService(settings)

    service.save_api_key("test-key-123")

    stored = settings.settings.sound_library_api_key_protected
    assert stored != "test-key-123"
    assert service.api_key() == "test-key-123"
    service.forget_api_key()
    assert service.api_key() == ""


@pytest.mark.skipif(sys.platform != "win32", reason="Windows credential encryption")
def test_windows_secret_storage_round_trip():
    protected = protect_secret("sound-library-test-key")

    assert protected != "sound-library-test-key"
    assert unprotect_secret(protected) == "sound-library-test-key"
