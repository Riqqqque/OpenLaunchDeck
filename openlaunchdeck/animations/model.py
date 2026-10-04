from __future__ import annotations

import base64
import binascii
import json
import zlib
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

GRID_SIZE = 8
FRAME_SIZE = GRID_SIZE * GRID_SIZE
MIN_FPS = 1
MAX_FPS = 30
MAX_FRAMES = 600
MAX_NAME_LENGTH = 60
MAX_AUTHOR_LENGTH = 60
MAX_DESCRIPTION_LENGTH = 280
FORMAT_VERSION = 1
OFF = "#000000"

SHARE_CODE_PREFIX = "OLDA1:"
# Hard caps for untrusted share codes and files, checked before parsing.
MAX_SHARE_CODE_LENGTH = 2_000_000
MAX_DECODED_BYTES = 1_000_000


class AnimationError(ValueError):
    """Raised when animation data is missing, malformed, or over a limit."""


def normalize_color(value: Any) -> str:
    if not isinstance(value, str):
        raise AnimationError("Pad colors must be text like #ff8800.")
    text = value.strip().lower()
    if len(text) == 4 and text.startswith("#"):
        text = "#" + "".join(char * 2 for char in text[1:])
    if len(text) != 7 or not text.startswith("#") or any(char not in "0123456789abcdef" for char in text[1:]):
        raise AnimationError(f"Invalid pad color: {value!r}")
    return text


def blank_frame() -> list[str]:
    return [OFF] * FRAME_SIZE


@dataclass(slots=True)
class IdleAnimation:
    """A frame-based pad animation: each frame is 64 colors, A1..H8 row by row."""

    id: str
    name: str
    frames: list[list[str]] = field(default_factory=lambda: [blank_frame()])
    fps: int = 10
    author: str = ""
    description: str = ""
    builtin: bool = False

    @property
    def frame_count(self) -> int:
        return len(self.frames)

    @property
    def duration_seconds(self) -> float:
        return len(self.frames) / max(MIN_FPS, self.fps)

    def iter_frames(self, seed: int = 0) -> Iterator[list[str]]:
        del seed  # Frame-based animations are already deterministic.
        while True:
            for frame in self.frames:
                yield list(frame)

    def to_dict(self) -> dict[str, Any]:
        return {
            "format": "openlaunchdeck.idle_animation",
            "version": FORMAT_VERSION,
            "id": self.id,
            "name": self.name,
            "author": self.author,
            "description": self.description,
            "fps": self.fps,
            "frames": [list(frame) for frame in self.frames],
        }

    @classmethod
    def from_dict(cls, data: Any) -> "IdleAnimation":
        if not isinstance(data, dict):
            raise AnimationError("Animation data must be a JSON object.")
        version = data.get("version", FORMAT_VERSION)
        if not isinstance(version, int) or version > FORMAT_VERSION:
            raise AnimationError("This animation was made with a newer OpenLaunchDeck. Update to use it.")
        name = _clean_text(data.get("name"), MAX_NAME_LENGTH)
        if not name:
            raise AnimationError("The animation needs a name.")
        fps = data.get("fps", 10)
        if isinstance(fps, bool) or not isinstance(fps, (int, float)) or not MIN_FPS <= fps <= MAX_FPS:
            raise AnimationError(f"Speed must be between {MIN_FPS} and {MAX_FPS} frames per second.")
        frames = data.get("frames")
        if not isinstance(frames, list) or not frames:
            raise AnimationError("The animation has no frames.")
        if len(frames) > MAX_FRAMES:
            raise AnimationError(f"Animations are limited to {MAX_FRAMES} frames.")
        clean_frames = []
        for index, frame in enumerate(frames, start=1):
            if not isinstance(frame, list) or len(frame) != FRAME_SIZE:
                raise AnimationError(f"Frame {index} must have exactly {FRAME_SIZE} pad colors.")
            clean_frames.append([normalize_color(color) for color in frame])
        return cls(
            id=_clean_text(data.get("id"), 80),
            name=name,
            frames=clean_frames,
            fps=int(fps),
            author=_clean_text(data.get("author"), MAX_AUTHOR_LENGTH),
            description=_clean_text(data.get("description"), MAX_DESCRIPTION_LENGTH),
        )


def encode_share_code(animation: IdleAnimation) -> str:
    payload = animation.to_dict()
    payload.pop("id", None)
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    packed = base64.urlsafe_b64encode(zlib.compress(raw, 9)).decode("ascii").rstrip("=")
    return SHARE_CODE_PREFIX + packed


def decode_share_code(text: str) -> IdleAnimation:
    if not isinstance(text, str):
        raise AnimationError("Paste an OpenLaunchDeck animation share code.")
    code = "".join(text.split())
    if not code.startswith(SHARE_CODE_PREFIX):
        raise AnimationError("That isn't an OpenLaunchDeck animation share code.")
    if len(code) > MAX_SHARE_CODE_LENGTH:
        raise AnimationError("That share code is too large.")
    body = code[len(SHARE_CODE_PREFIX) :]
    try:
        compressed = base64.urlsafe_b64decode(body + "=" * (-len(body) % 4))
        decompressor = zlib.decompressobj()
        raw = decompressor.decompress(compressed, MAX_DECODED_BYTES)
        if decompressor.unconsumed_tail:
            raise AnimationError("That share code is too large.")
        data = json.loads(raw.decode("utf-8"))
    except AnimationError:
        raise
    except (binascii.Error, zlib.error, UnicodeDecodeError, ValueError) as exc:
        raise AnimationError("That share code is damaged or incomplete.") from exc
    return IdleAnimation.from_dict(data)


def scale_color(color: str, factor: float) -> str:
    if factor >= 0.999:
        return color
    factor = max(0.0, factor)
    red, green, blue = (int(color[offset : offset + 2], 16) for offset in (1, 3, 5))
    return "#{:02x}{:02x}{:02x}".format(round(red * factor), round(green * factor), round(blue * factor))


def _clean_text(value: Any, limit: int) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split())[:limit]
