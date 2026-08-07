from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class SoundLibraryItem:
    provider: str
    sound_id: int
    name: str
    creator: str
    license_name: str
    duration: float
    preview_url: str
    source_url: str
    downloads: int = 0
    rating: float = 0.0
    created: str = ""
    tags: tuple[str, ...] = ()
    local_path: str = ""

    @property
    def attribution(self) -> str:
        source = f" ({self.source_url})" if self.source_url else ""
        return f'"{self.name}" by {self.creator}{source} - {self.license_name}'

    def to_metadata(self, audio_file: str) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "provider": self.provider,
            "sound_id": self.sound_id,
            "name": self.name,
            "creator": self.creator,
            "license": self.license_name,
            "duration": self.duration,
            "preview_url": self.preview_url,
            "source_url": self.source_url,
            "downloads": self.downloads,
            "rating": self.rating,
            "created": self.created,
            "tags": list(self.tags),
            "audio_file": audio_file,
            "attribution": self.attribution,
        }

    @classmethod
    def from_metadata(cls, data: dict[str, Any], local_path: str) -> "SoundLibraryItem":
        tags = data.get("tags")
        return cls(
            provider=str(data.get("provider") or "Local"),
            sound_id=_safe_int(data.get("sound_id")),
            name=str(data.get("name") or "Untitled sound"),
            creator=str(data.get("creator") or "Local file"),
            license_name=str(data.get("license") or "User supplied"),
            duration=_safe_float(data.get("duration")),
            preview_url=str(data.get("preview_url") or ""),
            source_url=str(data.get("source_url") or ""),
            downloads=_safe_int(data.get("downloads")),
            rating=_safe_float(data.get("rating")),
            created=str(data.get("created") or ""),
            tags=tuple(str(tag) for tag in tags) if isinstance(tags, list) else (),
            local_path=local_path,
        )


@dataclass(frozen=True, slots=True)
class SoundSearchPage:
    items: tuple[SoundLibraryItem, ...]
    total: int
    page: int
    has_next: bool
    has_previous: bool


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
