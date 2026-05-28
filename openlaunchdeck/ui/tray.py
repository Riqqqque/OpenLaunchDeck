from __future__ import annotations

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from .icons import app_icon


class TrayController:
    def __init__(self, window, services) -> None:
        self.window = window
        self.services = services
        self.tray = QSystemTrayIcon(app_icon(), window)
        menu = QMenu()
        open_action = QAction("Open OpenLaunchDeck", menu)
        reconnect_action = QAction("Reconnect Device", menu)
        stop_sounds_action = QAction("Stop All Sounds", menu)
        quit_action = QAction("Quit", menu)
        open_action.triggered.connect(window.show)
        reconnect_action.triggered.connect(window.connect_device)
        stop_sounds_action.triggered.connect(services.audio_engine.stop_all)
        quit_action.triggered.connect(window.quit_app)
        for action in (open_action, reconnect_action, stop_sounds_action, quit_action):
            menu.addAction(action)
        self.tray.setContextMenu(menu)

    def show(self) -> None:
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()
