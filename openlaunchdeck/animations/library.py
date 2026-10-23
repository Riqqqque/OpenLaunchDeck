from __future__ import annotations

import itertools
import json
import shutil
import uuid
from pathlib import Path
from typing import Union

from ..config_store import write_json
from ..paths import ANIMATIONS_DIR, BACKUPS_DIR
from .builtin import BUILTIN_ANIMATIONS, BUILTIN_BY_ID, BuiltinAnimation
from .model import MAX_FRAMES, AnimationError, IdleAnimation, decode_share_code, encode_share_code

AnyAnimation = Union[BuiltinAnimation, IdleAnimation]
FILE_SUFFIX = ".json"
MAX_FILE_BYTES = 2_000_000
MAX_BAKE_SECONDS = 20


class AnimationLibrary:
    """Built-in animations plus the user's saved and imported ones."""

    def __init__(self, directory: Path | None = None, logger=None) -> None:
        self.directory = directory or ANIMATIONS_DIR
        self.logger = logger
        self._user: dict[str, IdleAnimation] = {}
        self._paths: dict[str, Path] = {}
        self.reload()

    def reload(self) -> None:
        self._user.clear()
        self._paths.clear()
        self.directory.mkdir(parents=True, exist_ok=True)
        for path in sorted(self.directory.glob(f"*{FILE_SUFFIX}")):
            try:
                animation = self._read_file(path)
            except (AnimationError, OSError) as exc:
                if self.logger:
                    self.logger.warning("Skipped animation %s: %s", path.name, exc)
                continue
            animation.id = self._unique_id(animation.id or path.stem)
            self._user[animation.id] = animation
            self._paths[animation.id] = path

    def all(self) -> list[AnyAnimation]:
        return [*BUILTIN_ANIMATIONS, *sorted(self._user.values(), key=lambda item: item.name.casefold())]

    def user_animations(self) -> list[IdleAnimation]:
        return sorted(self._user.values(), key=lambda item: item.name.casefold())

    def get(self, animation_id: str) -> AnyAnimation | None:
        return BUILTIN_BY_ID.get(animation_id) or self._user.get(animation_id)

    def is_builtin(self, animation_id: str) -> bool:
        return animation_id in BUILTIN_BY_ID

    def save(self, animation: IdleAnimation) -> IdleAnimation:
        # Validate through the same path a shared file takes.
        clean = IdleAnimation.from_dict(animation.to_dict())
        if animation.id and animation.id in self._user:
            clean.id = animation.id
        else:
            clean.id = self._unique_id(animation.id or clean.name)
        path = self._paths.get(clean.id) or self._free_path(clean.id)
        write_json(path, clean.to_dict())
        self._user[clean.id] = clean
        self._paths[clean.id] = path
        return clean

    def delete(self, animation_id: str) -> bool:
        if animation_id not in self._user:
            return False
        path = self._paths.pop(animation_id)
        self._user.pop(animation_id)
        if path.exists():
            backup_dir = BACKUPS_DIR / "deleted_animations"
            backup_dir.mkdir(parents=True, exist_ok=True)
            target = backup_dir / path.name
            index = 2
            while target.exists():
                target = backup_dir / f"{path.stem}_{index}{path.suffix}"
                index += 1
            shutil.move(str(path), str(target))
        return True

    def import_file(self, path: Path) -> IdleAnimation:
        animation = self._read_file(path)
        animation.id = ""
        return self.save(animation)

    def import_share_code(self, code: str) -> IdleAnimation:
        animation = decode_share_code(code)
        animation.id = ""
        return self.save(animation)

    def export_file(self, animation_id: str, path: Path) -> None:
        write_json(path, self.as_frames(animation_id).to_dict())

    def share_code(self, animation_id: str) -> str:
        return encode_share_code(self.as_frames(animation_id))

    def as_frames(self, animation_id: str, seconds: float = 10.0) -> IdleAnimation:
        """Return a frame-based copy; built-ins are recorded for `seconds`."""
        animation = self.get(animation_id)
        if animation is None:
            raise AnimationError("That animation no longer exists.")
        if isinstance(animation, IdleAnimation):
            return IdleAnimation.from_dict(animation.to_dict())
        seconds = max(1.0, min(MAX_BAKE_SECONDS, seconds))
        count = min(MAX_FRAMES, max(1, round(animation.fps * seconds)))
        return IdleAnimation(
            id="",
            name=animation.name,
            frames=list(itertools.islice(animation.iter_frames(0), count)),
            fps=animation.fps,
            author=animation.author,
            description=animation.description,
        )

    def _read_file(self, path: Path) -> IdleAnimation:
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                raise AnimationError("That animation file is too large.")
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AnimationError("That file isn't a readable animation.") from exc
        return IdleAnimation.from_dict(data)

    def _unique_id(self, value: str) -> str:
        base = "".join(char.lower() if char.isalnum() else "_" for char in str(value).strip()).strip("_")[:60]
        base = base or f"animation_{uuid.uuid4().hex[:8]}"
        candidate = base
        index = 2
        while candidate in self._user or candidate in BUILTIN_BY_ID:
            candidate = f"{base}_{index}"
            index += 1
        return candidate

    def _free_path(self, animation_id: str) -> Path:
        claimed = {path.resolve() for path in self._paths.values()}
        candidate = self.directory / f"{animation_id}{FILE_SUFFIX}"
        index = 2
        while candidate.exists() or candidate.resolve() in claimed:
            candidate = self.directory / f"{animation_id}_{index}{FILE_SUFFIX}"
            index += 1
        return candidate
