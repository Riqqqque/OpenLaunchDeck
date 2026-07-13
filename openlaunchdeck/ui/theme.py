from __future__ import annotations

from ..paths import THEMES_DIR


def load_theme(theme: str = "dark") -> str:
    if theme == "system":
        theme = "dark"
    path = THEMES_DIR / f"{theme}.qss"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return (THEMES_DIR / "dark.qss").read_text(encoding="utf-8")
