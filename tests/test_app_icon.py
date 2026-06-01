import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from openlaunchdeck.paths import ICONS_DIR
from openlaunchdeck.ui.icons import app_icon


def test_app_icon_assets_exist_and_load():
    QApplication.instance() or QApplication([])

    assert (ICONS_DIR / "openlaunchdeck.svg").exists()
    assert (ICONS_DIR / "openlaunchdeck.ico").exists()
    assert (ICONS_DIR / "openlaunchdeck_256.png").exists()
    assert not app_icon().isNull()
