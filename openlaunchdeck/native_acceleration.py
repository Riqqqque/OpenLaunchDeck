from __future__ import annotations

import hashlib
import importlib
from pathlib import Path
from types import ModuleType

from .constants import BUTTON_IDS


_BUTTON_TO_INDEX = {button_id: index for index, button_id in enumerate(BUTTON_IDS)}
_native_enabled = False
_native_checked = False
_native_module: ModuleType | None = None
_logger = None


def configure(enabled: bool, logger=None) -> None:
    global _native_enabled, _native_checked, _native_module, _logger
    _native_enabled = bool(enabled)
    _native_checked = False
    _native_module = None
    _logger = logger


def native_available() -> bool:
    return _load_native() is not None


def validate_button_id(button_id: str) -> bool:
    native = _load_native()
    if native and hasattr(native, "validate_button_id"):
        return bool(native.validate_button_id(button_id))
    return button_id in _BUTTON_TO_INDEX


def button_id_to_index(button_id: str) -> int:
    native = _load_native()
    if native and hasattr(native, "button_id_to_index"):
        return int(native.button_id_to_index(button_id))
    return _BUTTON_TO_INDEX.get(button_id, -1)


def index_to_button_id(index: int) -> str:
    native = _load_native()
    if native and hasattr(native, "index_to_button_id"):
        return str(native.index_to_button_id(index))
    if 0 <= index < len(BUTTON_IDS):
        return BUTTON_IDS[index]
    raise ValueError(f"Button index out of range: {index}")


def calculate_profile_hash(json_text: str) -> str:
    native = _load_native()
    if native and hasattr(native, "calculate_profile_hash"):
        return str(native.calculate_profile_hash(json_text))
    return hashlib.sha256(json_text.encode("utf-8")).hexdigest()


def verify_sha256(file_path: str | Path, expected_hash: str) -> bool:
    native = _load_native()
    if native and hasattr(native, "verify_sha256"):
        return bool(native.verify_sha256(str(file_path), expected_hash))
    expected = expected_hash.lower()
    digest = hashlib.sha256()
    with Path(file_path).open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().lower() == expected


def _load_native() -> ModuleType | None:
    global _native_checked, _native_module
    if not _native_enabled:
        return None
    if _native_checked:
        return _native_module
    _native_checked = True
    try:
        _native_module = importlib.import_module("openlaunchdeck_native")
    except Exception as exc:
        _native_module = None
        if _logger:
            _logger.debug("Native acceleration unavailable: %s", exc)
    else:
        if _logger:
            _logger.info("Native acceleration enabled.")
    return _native_module
