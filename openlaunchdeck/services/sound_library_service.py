from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import unicodedata
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlparse

from ..config_store import read_json, write_json
from ..models.sound_library import SoundLibraryItem, SoundSearchPage
from ..paths import SOUND_LIBRARY_DIR
from .secret_store import SecretStorageError, protect_secret, unprotect_secret


SEARCH_ENDPOINT = "https://freesound.org/apiv2/search/text/"
API_KEY_URL = "https://freesound.org/apiv2/apply"
PROVIDER_TERMS_URL = "https://freesound.org/help/tos_api/"
MAX_DOWNLOAD_BYTES = 25 * 1024 * 1024
SUPPORTED_IMPORT_EXTENSIONS = {".wav", ".mp3", ".ogg"}
SEARCH_SORTS = {"score", "downloads_desc", "created_desc", "rating_desc"}
LICENSE_FILTERS = {
    "cc0": 'license:"Creative Commons 0"',
    "attribution": '(license:"Creative Commons 0" OR license:"Attribution")',
    "all": "",
}
SEARCH_FIELDS = ",".join(
    (
        "id",
        "name",
        "username",
        "license",
        "duration",
        "previews",
        "url",
        "num_downloads",
        "avg_rating",
        "created",
        "tags",
        "is_explicit",
    )
)


class SoundLibraryError(RuntimeError):
    pass


class SoundLibraryService:
    def __init__(self, settings_service=None, logger=None) -> None:
        self.settings_service = settings_service
        self.logger = logger
        self._cached_api_key: str | None = None
        SOUND_LIBRARY_DIR.mkdir(parents=True, exist_ok=True)

    def api_key(self) -> str:
        environment_key = os.environ.get("OPENLAUNCHDECK_FREESOUND_API_KEY", "").strip()
        if environment_key:
            return environment_key
        if self._cached_api_key is not None:
            return self._cached_api_key
        if self.settings_service is None:
            return ""
        protected = self.settings_service.settings.sound_library_api_key_protected
        try:
            self._cached_api_key = unprotect_secret(protected)
            return self._cached_api_key
        except SecretStorageError:
            if self.logger:
                self.logger.warning("The saved sound library credential could not be read for this Windows account.")
            self._cached_api_key = ""
            return ""

    def save_api_key(self, api_key: str) -> None:
        clean_key = api_key.strip()
        if not clean_key:
            raise SoundLibraryError("Enter a Freesound API key.")
        if len(clean_key) > 256 or any(character.isspace() for character in clean_key):
            raise SoundLibraryError("The API key format is not valid.")
        if self.settings_service is None:
            raise SoundLibraryError("Settings are unavailable.")
        try:
            protected = protect_secret(clean_key)
        except SecretStorageError as exc:
            raise SoundLibraryError(str(exc)) from exc
        try:
            self.settings_service.update(sound_library_api_key_protected=protected)
        except OSError as exc:
            raise SoundLibraryError("The sound library credential could not be saved.") from exc
        self._cached_api_key = clean_key

    def forget_api_key(self) -> None:
        if self.settings_service is not None:
            try:
                self.settings_service.update(sound_library_api_key_protected="")
            except OSError as exc:
                raise SoundLibraryError("The saved sound library credential could not be removed.") from exc
        self._cached_api_key = ""

    def build_search_url(
        self,
        query: str,
        *,
        sort: str = "downloads_desc",
        license_filter: str = "cc0",
        maximum_duration: int = 15,
        page: int = 1,
        page_size: int = 24,
    ) -> str:
        clean_query = " ".join(query.strip().split())[:120]
        clean_sort = sort if sort in SEARCH_SORTS else "downloads_desc"
        clean_license = license_filter if license_filter in LICENSE_FILTERS else "cc0"
        duration = max(1, min(60, int(maximum_duration)))
        filters = ["is_explicit:false", f"duration:[0.1 TO {duration}]"]
        if LICENSE_FILTERS[clean_license]:
            filters.append(LICENSE_FILTERS[clean_license])
        parameters = {
            "query": clean_query,
            "sort": clean_sort,
            "filter": " ".join(filters),
            "fields": SEARCH_FIELDS,
            "page": max(1, int(page)),
            "page_size": max(1, min(50, int(page_size))),
            "group_by_pack": 1,
        }
        return SEARCH_ENDPOINT + "?" + urlencode(parameters)

    def parse_search_payload(self, payload: bytes | str, page: int) -> SoundSearchPage:
        try:
            data = json.loads(payload)
        except (json.JSONDecodeError, UnicodeDecodeError, TypeError) as exc:
            raise SoundLibraryError("The sound provider returned invalid data.") from exc
        if not isinstance(data, dict) or not isinstance(data.get("results"), list):
            raise SoundLibraryError("The sound provider response is incomplete.")
        items: list[SoundLibraryItem] = []
        for raw_item in data["results"]:
            item = self._parse_item(raw_item)
            if item is not None:
                items.append(item)
        return SoundSearchPage(
            items=tuple(items),
            total=_safe_int(data.get("count")),
            page=max(1, page),
            has_next=bool(data.get("next")),
            has_previous=bool(data.get("previous")),
        )

    def downloaded_path(self, item: SoundLibraryItem) -> Path:
        return SOUND_LIBRARY_DIR / f"freesound-{item.sound_id}-{_safe_stem(item.name)}.mp3"

    def part_path(self, item: SoundLibraryItem) -> Path:
        return self.downloaded_path(item).with_suffix(".mp3.part")

    def existing_download(self, item: SoundLibraryItem) -> Path | None:
        path = self.downloaded_path(item)
        return path if path.is_file() and path.stat().st_size > 0 else None

    def finalize_download(self, item: SoundLibraryItem, part_path: Path) -> Path:
        destination = self.downloaded_path(item)
        self._require_library_child(part_path)
        self._require_library_child(destination)
        try:
            size = part_path.stat().st_size
        except OSError as exc:
            raise SoundLibraryError("The downloaded sound could not be read.") from exc
        if size <= 0 or size > MAX_DOWNLOAD_BYTES:
            raise SoundLibraryError("The downloaded sound has an invalid size.")
        metadata = item.to_metadata(destination.name)
        metadata["downloaded_at"] = datetime.now(UTC).isoformat()
        metadata_path = destination.with_suffix(".json")
        write_json(metadata_path, metadata)
        try:
            os.replace(part_path, destination)
        except OSError:
            metadata_path.unlink(missing_ok=True)
            raise
        self._refresh_attribution_index()
        return destination

    def import_local_file(self, source: Path) -> Path:
        source = source.expanduser().resolve()
        if not source.is_file():
            raise SoundLibraryError("The selected sound file does not exist.")
        extension = source.suffix.casefold()
        if extension not in SUPPORTED_IMPORT_EXTENSIONS:
            raise SoundLibraryError("Choose a WAV, MP3, or OGG file.")
        size = source.stat().st_size
        if size <= 0 or size > MAX_DOWNLOAD_BYTES:
            raise SoundLibraryError("The sound must be between 1 byte and 25 MB.")
        digest = _sha256_file(source)[:12]
        destination = SOUND_LIBRARY_DIR / f"local-{digest}-{_safe_stem(source.stem)}{extension}"
        if not destination.exists():
            temporary = destination.with_suffix(destination.suffix + ".part")
            try:
                with source.open("rb") as input_file, temporary.open("wb") as output_file:
                    shutil.copyfileobj(input_file, output_file, length=1024 * 1024)
                os.replace(temporary, destination)
            except OSError:
                temporary.unlink(missing_ok=True)
                raise
        item = SoundLibraryItem(
            provider="Local",
            sound_id=0,
            name=source.stem,
            creator="Local file",
            license_name="User supplied",
            duration=0,
            preview_url="",
            source_url="",
            local_path=str(destination),
        )
        metadata = item.to_metadata(destination.name)
        metadata["imported_at"] = datetime.now(UTC).isoformat()
        write_json(destination.with_suffix(".json"), metadata)
        self._refresh_attribution_index()
        return destination

    def local_items(self) -> list[SoundLibraryItem]:
        items: list[SoundLibraryItem] = []
        for metadata_path in sorted(SOUND_LIBRARY_DIR.glob("*.json"), key=_modified_time, reverse=True):
            try:
                data = read_json(metadata_path, {})
                if not isinstance(data, dict):
                    continue
                audio_name = Path(str(data.get("audio_file") or "")).name
                audio_path = SOUND_LIBRARY_DIR / audio_name
                self._require_library_child(audio_path)
                if not audio_path.is_file():
                    continue
                items.append(SoundLibraryItem.from_metadata(data, str(audio_path)))
            except (OSError, ValueError):
                if self.logger:
                    self.logger.warning("Ignored invalid sound library metadata: %s", metadata_path.name)
        return items

    def _parse_item(self, data: Any) -> SoundLibraryItem | None:
        if not isinstance(data, dict) or bool(data.get("is_explicit")):
            return None
        previews = data.get("previews")
        preview_url = str(previews.get("preview-hq-mp3") or "") if isinstance(previews, dict) else ""
        source_url = str(data.get("url") or "")
        if not _is_freesound_url(preview_url) or not _is_freesound_url(source_url):
            return None
        sound_id = _safe_int(data.get("id"))
        if sound_id <= 0:
            return None
        name = " ".join(str(data.get("name") or "Untitled sound").split())[:160]
        creator = " ".join(str(data.get("username") or "Unknown creator").split())[:80]
        license_name = " ".join(str(data.get("license") or "Unknown license").split())[:80]
        tags = data.get("tags")
        return SoundLibraryItem(
            provider="Freesound",
            sound_id=sound_id,
            name=name,
            creator=creator,
            license_name=license_name,
            duration=max(0.0, _safe_float(data.get("duration"))),
            preview_url=preview_url,
            source_url=source_url,
            downloads=max(0, _safe_int(data.get("num_downloads"))),
            rating=max(0.0, min(5.0, _safe_float(data.get("avg_rating")))),
            created=str(data.get("created") or ""),
            tags=tuple(str(tag)[:60] for tag in tags[:20]) if isinstance(tags, list) else (),
        )

    @staticmethod
    def _require_library_child(path: Path) -> None:
        root = SOUND_LIBRARY_DIR.resolve()
        resolved = path.resolve(strict=False)
        if not resolved.is_relative_to(root):
            raise SoundLibraryError("The sound library path is not safe.")

    def _write_attribution_index(self) -> None:
        lines = ["OpenLaunchDeck Sound Library", ""]
        for item in self.local_items_without_refresh():
            lines.append(item.attribution)
        text = "\n".join(lines).rstrip() + "\n"
        temporary = SOUND_LIBRARY_DIR / "ATTRIBUTION.txt.tmp"
        temporary.write_text(text, encoding="utf-8")
        os.replace(temporary, SOUND_LIBRARY_DIR / "ATTRIBUTION.txt")

    def _refresh_attribution_index(self) -> None:
        try:
            self._write_attribution_index()
        except OSError:
            if self.logger:
                self.logger.warning("The sound library attribution index could not be refreshed.", exc_info=True)

    def local_items_without_refresh(self) -> list[SoundLibraryItem]:
        items: list[SoundLibraryItem] = []
        for metadata_path in SOUND_LIBRARY_DIR.glob("*.json"):
            try:
                data = read_json(metadata_path, {})
                if not isinstance(data, dict):
                    continue
                audio_name = Path(str(data.get("audio_file") or "")).name
                audio_path = SOUND_LIBRARY_DIR / audio_name
                if audio_path.is_file():
                    items.append(SoundLibraryItem.from_metadata(data, str(audio_path)))
            except (OSError, ValueError):
                continue
        return sorted(items, key=lambda item: (item.provider, item.creator.casefold(), item.name.casefold()))


def _is_freesound_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
        host = (parsed.hostname or "").casefold()
        port = parsed.port
    except ValueError:
        return False
    trusted_host = host == "freesound.org" or host.endswith(".freesound.org")
    return (
        parsed.scheme == "https"
        and trusted_host
        and port in (None, 443)
        and parsed.username is None
        and parsed.password is None
    )


def _safe_stem(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    clean = re.sub(r"[^A-Za-z0-9._-]+", "-", normalized).strip(" .-_")
    return clean[:72] or "sound"


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _modified_time(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0
