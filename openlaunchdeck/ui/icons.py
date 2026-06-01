from __future__ import annotations

from PySide6.QtGui import QIcon

from ..paths import ICONS_DIR


def app_icon() -> QIcon:
    for file_name in ("openlaunchdeck_256.png", "openlaunchdeck.ico", "openlaunchdeck.svg"):
        icon_path = ICONS_DIR / file_name
        if icon_path.exists():
            icon = QIcon(str(icon_path))
            if not icon.isNull():
                return icon
    return QIcon()
