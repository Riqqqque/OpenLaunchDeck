from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

from packaging.version import Version, InvalidVersion

from ..models.update_manifest import UpdateManifest
from ..native_acceleration import verify_sha256 as verify_sha256_accelerated
from ..paths import UPDATES_DIR


@dataclass(slots=True)
class UpdateCheckResult:
    available: bool
    message: str
    manifest: UpdateManifest | None = None
    required: bool = False
    unsupported: bool = False
    current_version: str = ""
    latest_version: str = ""
    release_notes_url: str = ""


class UpdateService:
    def __init__(self, current_version: str, logger=None) -> None:
        self.current_version = current_version
        self.logger = logger

    @staticmethod
    def _parse_version(value: str) -> Version:
        try:
            return Version(value)
        except InvalidVersion as exc:
            raise ValueError("Update manifest contains an invalid version.") from exc

    def is_newer(self, latest_version: str) -> bool:
        return self._parse_version(latest_version) > self._parse_version(self.current_version)

    def is_current_supported(self, minimum_supported_version: str) -> bool:
        return self._parse_version(self.current_version) >= self._parse_version(minimum_supported_version)

    def parse_manifest(self, data: dict) -> UpdateManifest:
        return UpdateManifest.from_dict(data)

    def check_manifest(self, manifest: UpdateManifest) -> UpdateCheckResult:
        current = self._parse_version(self.current_version)
        latest = self._parse_version(manifest.latest_version)
        minimum = self._parse_version(manifest.minimum_supported_version)
        available = latest > current
        unsupported = current < minimum
        required = bool(manifest.required or unsupported)

        if unsupported and available:
            message = "Required update available. This version is below the minimum supported version."
        elif unsupported:
            message = "This version is below the minimum supported version."
        elif available and required:
            message = "Required update available."
        elif available:
            message = f"Version {manifest.latest_version} is available."
        else:
            message = "You are up to date."

        if self.logger:
            self.logger.info(
                "Update check result: current=%s latest=%s minimum=%s available=%s required=%s unsupported=%s",
                self.current_version,
                manifest.latest_version,
                manifest.minimum_supported_version,
                available,
                required,
                unsupported,
            )

        return UpdateCheckResult(
            available=available,
            message=message,
            manifest=manifest,
            required=required,
            unsupported=unsupported,
            current_version=self.current_version,
            latest_version=manifest.latest_version,
            release_notes_url=manifest.release_notes_url,
        )

    def check_manifest_data(self, data: dict) -> UpdateCheckResult:
        return self.check_manifest(self.parse_manifest(data))

    def fetch_manifest(self, manifest_url: str) -> UpdateManifest:
        if not manifest_url:
            raise ValueError("No update manifest URL is configured.")
        try:
            import requests
        except Exception as exc:
            raise RuntimeError("HTTP dependency is not installed.") from exc
        if self.logger:
            self.logger.info("Fetching update manifest: %s", manifest_url)
        start = time.perf_counter()
        try:
            response = requests.get(manifest_url, timeout=10)
            response.raise_for_status()
            manifest = self.parse_manifest(response.json())
        except Exception:
            if self.logger:
                self.logger.exception("Update manifest fetch failed.")
            raise
        if self.logger:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self.logger.info("Fetched update manifest for version %s", manifest.latest_version)
            self.logger.debug("Update check fetch elapsed=%.3f ms", elapsed_ms)
        return manifest

    def download(
        self,
        manifest: UpdateManifest,
        destination: Path | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> Path:
        try:
            import requests
        except Exception as exc:
            raise RuntimeError("HTTP dependency is not installed.") from exc
        destination = destination or UPDATES_DIR
        destination.mkdir(parents=True, exist_ok=True)
        filename = Path(urlparse(manifest.download_url).path).name or "OpenLaunchDeckUpdate.exe"
        target = destination / filename
        partial = target.with_suffix(target.suffix + ".part")
        target.unlink(missing_ok=True)
        partial.unlink(missing_ok=True)

        if self.logger:
            self.logger.info("Downloading update installer to %s", target)

        start = time.perf_counter()
        try:
            with requests.get(manifest.download_url, stream=True, timeout=(10, 60)) as response:
                response.raise_for_status()
                total = int(response.headers.get("content-length") or 0)
                downloaded = 0
                with partial.open("wb") as file:
                    for chunk in response.iter_content(chunk_size=1024 * 256):
                        if chunk:
                            file.write(chunk)
                            downloaded += len(chunk)
                            if progress_callback:
                                progress_callback(downloaded, total)
            partial.replace(target)
        except Exception:
            partial.unlink(missing_ok=True)
            target.unlink(missing_ok=True)
            if self.logger:
                self.logger.exception("Update installer download failed.")
            raise

        if not self.verify_sha256(target, manifest.sha256):
            target.unlink(missing_ok=True)
            if self.logger:
                self.logger.error("Downloaded update failed checksum verification: %s", target)
            raise ValueError("Downloaded update failed checksum verification.")
        if self.logger:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self.logger.info("Downloaded update installer verified: %s", target)
            self.logger.debug("Update download and checksum elapsed=%.3f ms", elapsed_ms)
        return target

    @staticmethod
    def sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @classmethod
    def verify_sha256(cls, path: Path, expected: str) -> bool:
        return verify_sha256_accelerated(path, expected)
