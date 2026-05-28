from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from packaging.version import InvalidVersion, Version


@dataclass(frozen=True, slots=True)
class UpdateManifest:
    latest_version: str
    minimum_supported_version: str
    required: bool
    download_url: str
    sha256: str
    release_notes_url: str
    published_at: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UpdateManifest":
        if not isinstance(data, dict):
            raise ValueError("Update manifest must be a JSON object.")
        required_fields = (
            "latest_version",
            "minimum_supported_version",
            "required",
            "download_url",
            "sha256",
            "release_notes_url",
            "published_at",
        )
        missing = [field for field in required_fields if field not in data]
        if missing:
            raise ValueError(f"Update manifest is missing: {', '.join(missing)}.")
        if not isinstance(data["required"], bool):
            raise ValueError("Update manifest required field must be true or false.")
        manifest = cls(
            latest_version=str(data["latest_version"]),
            minimum_supported_version=str(data["minimum_supported_version"]),
            required=data["required"],
            download_url=str(data["download_url"]),
            sha256=str(data["sha256"]).lower(),
            release_notes_url=str(data["release_notes_url"]),
            published_at=str(data["published_at"]),
        )
        manifest.validate()
        return manifest

    def validate(self) -> None:
        for field_name, value in (
            ("latest_version", self.latest_version),
            ("minimum_supported_version", self.minimum_supported_version),
        ):
            try:
                Version(value)
            except InvalidVersion as exc:
                raise ValueError(f"Update manifest contains an invalid {field_name}.") from exc
        if len(self.sha256) != 64 or any(char not in "0123456789abcdef" for char in self.sha256):
            raise ValueError("Update manifest contains an invalid SHA256 checksum.")
        if not self.download_url.startswith(("https://", "http://")):
            raise ValueError("Update manifest download URL must be HTTP or HTTPS.")
        if self.release_notes_url and not self.release_notes_url.startswith(("https://", "http://")):
            raise ValueError("Update manifest release notes URL must be HTTP or HTTPS.")
        try:
            datetime.fromisoformat(self.published_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("Update manifest published_at must be ISO 8601.") from exc

    def to_dict(self) -> dict[str, Any]:
        return {
            "latest_version": self.latest_version,
            "minimum_supported_version": self.minimum_supported_version,
            "required": self.required,
            "download_url": self.download_url,
            "sha256": self.sha256,
            "release_notes_url": self.release_notes_url,
            "published_at": self.published_at,
        }
