from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class SoundMetadata:
    file_path: str
    display_name: str
    suffix: str
    size_bytes: int
    modified_ns: int

    @classmethod
    def from_path(cls, path: Path) -> "SoundMetadata":
        stat = path.stat()
        return cls(
            file_path=str(path),
            display_name=path.name,
            suffix=path.suffix.lower(),
            size_bytes=stat.st_size,
            modified_ns=stat.st_mtime_ns,
        )


@dataclass(slots=True)
class SoundInstance:
    instance_id: str
    button_id: str
    page_id: str
    file_path: str
    display_name: str = ""
    player: Any = None
    audio_output: Any = None
    loop: bool = False
    volume: int = 100
