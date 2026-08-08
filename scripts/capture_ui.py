from __future__ import annotations

import argparse
import os
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
_data_dir = tempfile.TemporaryDirectory(prefix="openlaunchdeck-ui-")
os.environ["OPENLAUNCHDECK_DATA_DIR"] = _data_dir.name

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication

from openlaunchdeck.app import build_services
from openlaunchdeck.logging_setup import shutdown_logging
from openlaunchdeck.ui.main_window import MainWindow
from openlaunchdeck.ui.settings_dialog import SettingsDialog
from openlaunchdeck.ui.sound_library_dialog import SoundLibraryDialog
from openlaunchdeck.ui.theme import apply_theme, theme_definitions


def settle(app: QApplication, milliseconds: int = 80) -> None:
    deadline = time.monotonic() + milliseconds / 1000
    while time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.005)


def capture(widget, path: Path, app: QApplication, expected_size: tuple[int, int] | None = None) -> None:
    widget.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    widget.show()
    if expected_size is not None:
        widget.resize(*expected_size)
    settle(app)
    if expected_size is not None and (widget.width(), widget.height()) != expected_size:
        raise RuntimeError(
            f"{widget.windowTitle() or widget.objectName()} rendered at {widget.width()}x{widget.height()} "
            f"instead of {expected_size[0]}x{expected_size[1]}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    if not widget.grab().save(str(path)):
        raise RuntimeError(f"Could not save {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture OpenLaunchDeck UI screenshots with the offscreen Qt backend.")
    parser.add_argument("--output", type=Path, default=Path("build/ui-qa"))
    parser.add_argument("--docs", action="store_true", help="Refresh the public screenshots under docs/screenshots.")
    args = parser.parse_args()

    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")
    available_families = set(QFontDatabase.families())
    preferred_family = next(
        (family for family in ("Segoe UI", "Arial", "Tahoma") if family in available_families),
        app.font().family(),
    )
    app_font = app.font()
    app_font.setFamily(preferred_family)
    app.setFont(app_font)
    services = build_services()
    services.settings_service.settings.first_run_complete = True
    services.settings_service.settings.auto_connect = False
    services.settings_service.settings.check_updates_on_startup = False
    if "basic_pc" in services.profile_service.profiles:
        services.profile_service.set_current_profile("basic_pc")
    window = MainWindow(services)
    try:
        sizes = ((760, 560, "narrow"), (1180, 720, "compact"), (1600, 900, "wide"))
        for definition in theme_definitions():
            apply_theme(definition.key, window)
            for width, height, label in sizes:
                window.resize(width, height)
                window._apply_responsive_layout(force=True)
                settle(app)
                capture(window, args.output / f"main-{definition.key}-{label}.png", app, (width, height))

        apply_theme("midnight", window)
        window.set_grid_focus_mode(True)
        window.resize(760, 560)
        window._apply_responsive_layout(force=True)
        capture(window, args.output / "main-midnight-focus.png", app, (760, 560))
        window.set_grid_focus_mode(False)
        window.resize(1600, 900)
        window._apply_responsive_layout(force=True)
        settle(app)
        if args.docs:
            capture(window, Path("docs/screenshots/main-window-dark.png"), app, (1600, 900))

        library = SoundLibraryDialog(
            services.settings_service,
            services.logger,
            selected_button_provider=lambda: window.grid.selected_button_id,
            parent=window,
        )
        library.resize(1100, 760)
        capture(library, args.output / "sound-library.png", app, (1100, 760))
        if args.docs:
            capture(library, Path("docs/screenshots/sound-library.png"), app, (1100, 760))
        library.close()

        settings = SettingsDialog(services.settings_service, window, services.startup_service)
        settings.resize(800, 680)
        capture(settings, args.output / "settings-appearance.png", app, (800, 680))
        if args.docs:
            capture(settings, Path("docs/screenshots/settings-themes.png"), app, (800, 680))
        settings.reject()
    finally:
        window._force_quit = True
        window.close()
        services.action_runner.shutdown()
        services.lighting_service.shutdown()
        services.audio_engine.shutdown()
        services.device.close()
        shutdown_logging(services.logger)
        _data_dir.cleanup()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
