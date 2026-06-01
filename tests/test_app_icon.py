import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage

from openlaunchdeck.paths import ICONS_DIR
from openlaunchdeck.ui.icons import app_icon


def test_app_icon_assets_exist_and_load():
    QApplication.instance() or QApplication([])

    assert (ICONS_DIR / "openlaunchdeck.svg").exists()
    assert (ICONS_DIR / "openlaunchdeck.ico").exists()
    assert (ICONS_DIR / "openlaunchdeck_256.png").exists()
    icon = app_icon()
    assert not icon.isNull()
    assert max(size.width() for size in icon.availableSizes()) >= 256


def test_app_icon_has_transparent_outer_corners():
    image = QImage(str(ICONS_DIR / "openlaunchdeck_256.png"))

    assert not image.isNull()
    assert image.pixelColor(0, 0).alpha() == 0
    assert image.pixelColor(255, 255).alpha() == 0
