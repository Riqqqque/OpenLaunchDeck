from __future__ import annotations

from pathlib import Path

from ..paths import THEMES_DIR


def load_theme(theme: str = "dark") -> str:
    path = THEMES_DIR / f"{theme}.qss"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""
