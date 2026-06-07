from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QObject, Qt, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from .. import native_acceleration
from ..constants import BUTTON_IDS
from ..devices.midi_manager import MidiManager
from ..models.button import ButtonConfig
from ..paths import APP_DATA_DIR, LOGS_DIR, PROFILES_DIR
from ..version import APP_NAME, __version__
from .button_editor import ButtonEditor
from .grid_widget import GridWidget
from .icons import app_icon
from .midi_debug_window import MidiDebugWindow
from .profile_manager_dialog import ProfileManagerDialog
from .profile_sidebar import ProfileSidebar
from .settings_dialog import SettingsDialog
from .setup_wizard import SetupWizard
from .soundboard_panel import SoundboardPanel
from .theme import load_theme
from ..services.update_service import UpdateService
from .tray import TrayController
from .update_dialog import UpdateCheckWorker, UpdateDialog


class MidiConnectionWorker(QObject):
    finished = Signal(bool, str, str, str)

    def __init__(self, device, input_port: str, output_port: str) -> None:
        super().__init__()
        self.device = device
        self.input_port = input_port
        self.output_port = output_port

    @Slot()
    def run(self) -> None:
        try:
            self.device.connect(self.input_port, self.output_port)
        except Exception as exc:
            self.finished.emit(False, str(exc), self.input_port, self.output_port)
            return
        self.finished.emit(True, "Connected.", self.input_port, self.output_port)


class MainWindow(QMainWindow):
    action_finished = Signal(str, object)
    hardware_button = Signal(str, bool, object)
    midi_in = Signal(object, str)
    midi_out = Signal(object, str)
    device_disconnected = Signal(str)
    audio_state_changed = Signal()

    def __init__(self, services) -> None:
        super().__init__()
        self.services = services
        self._force_quit = False
        self.clipboard_button: dict | None = None
        self.midi_debug_window: MidiDebugWindow | None = None
        self.soundboard_panel: SoundboardPanel | None = None
        self._connect_thread: QThread | None = None
        self._connect_worker: MidiConnectionWorker | None = None
        self._startup_update_thread: QThread | None = None
        self._startup_update_worker: UpdateCheckWorker | None = None
        self._grid_focus_mode = False
        self._midi_debug_callbacks_active = False
        self.setWindowTitle(f"{APP_NAME} {__version__}")
        self.setWindowIcon(app_icon())
        self.resize(1480, 920)
        self.setMinimumSize(980, 640)
        self.setStyleSheet(load_theme(self.services.settings_service.settings.theme))

        self.services.action_runner.completion_callback = lambda button_id, result: self.action_finished.emit(button_id, result)
        self.services.device.button_callback = lambda button_id, pressed, raw: self.hardware_button.emit(button_id, pressed, raw)
        self.services.device.midi_in_callback = None
        self.services.device.midi_out_callback = None
        self.services.device.disconnect_callback = lambda reason: self.device_disconnected.emit(reason)
        self.services.audio_engine.state_changed_callback = lambda: self.audio_state_changed.emit()

        self._build_menu()
        self._build_main_layout()
        self._build_status_bar()
        self._connect_signals()
        self.refresh_all()
        self.tray = TrayController(self, services)
        self.tray.show()

        if not self.services.settings_service.settings.first_run_complete:
            QTimer.singleShot(150, self.show_first_run)
        if self.services.settings_service.settings.auto_connect:
            QTimer.singleShot(250, self.connect_device)
        if (
            self.services.settings_service.settings.check_updates_on_startup
            and self.services.settings_service.settings.update_manifest_url.strip()
        ):
            QTimer.singleShot(1500, self.check_updates_on_startup)

    def _build_main_layout(self) -> None:
        central = QWidget()
        central.setObjectName("MainSurface")
        root = QVBoxLayout(central)
        self.main_root_layout = root
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(14)

        header = QFrame()
        self.app_header = header
        header.setObjectName("AppHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(18, 14, 18, 14)
        header_layout.setSpacing(12)

        brand = QWidget()
        brand.setObjectName("HeaderBrand")
        brand_layout = QVBoxLayout(brand)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(1)
        title = QLabel(APP_NAME)
        title.setObjectName("HeaderTitle")
        subtitle = QLabel("Macro deck workspace for Launchpad Mini MK3")
        subtitle.setObjectName("HeaderSubtitle")
        brand_layout.addWidget(title)
        brand_layout.addWidget(subtitle)
        header_layout.addWidget(brand, 1)

        header_meta = QWidget()
        header_meta.setObjectName("HeaderMeta")
        header_meta_layout = QVBoxLayout(header_meta)
        header_meta_layout.setContentsMargins(0, 0, 0, 0)
        header_meta_layout.setSpacing(6)
        self.header_profile = QLabel("")
        self.header_profile.setObjectName("HeaderActiveDeck")
        self.header_mode = QLabel("Simulation")
        self.header_mode.setObjectName("HeaderModeChip")
        header_meta_layout.addWidget(self.header_profile, 0, Qt.AlignmentFlag.AlignRight)
        header_meta_layout.addWidget(self.header_mode, 0, Qt.AlignmentFlag.AlignRight)
        header_layout.addWidget(header_meta)

        actions_frame = QFrame()
        actions_frame.setObjectName("HeaderActions")
        actions_layout = QHBoxLayout(actions_frame)
        actions_layout.setContentsMargins(6, 6, 6, 6)
        actions_layout.setSpacing(6)
        self.header_reconnect_button = QPushButton("Reconnect")
        self.header_debug_button = QPushButton("MIDI")
        self.header_soundboard_button = QPushButton("Soundboard")
        self.header_update_button = QPushButton("Updates")
        for button in (
            self.header_reconnect_button,
            self.header_debug_button,
            self.header_soundboard_button,
            self.header_update_button,
        ):
            button.setObjectName("HeaderButton")
            actions_layout.addWidget(button)
        self.header_update_button.setObjectName("HeaderPrimaryButton")
        header_layout.addWidget(actions_frame)

        root.addWidget(header)

        self.sidebar = ProfileSidebar()
        self.sidebar.setMinimumWidth(190)
        self.sidebar.setMaximumWidth(320)
        self.sidebar_scroll = QScrollArea()
        self.sidebar_scroll.setObjectName("SidebarScroll")
        self.sidebar_scroll.setWidgetResizable(True)
        self.sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.sidebar_scroll.setWidget(self.sidebar)
        self.sidebar_scroll.setMinimumWidth(210)
        self.grid = GridWidget()
        self._applied_grid_density = self.services.settings_service.settings.grid_density
        self.grid.set_density(self._applied_grid_density)
        self.editor = ButtonEditor(self.services.action_registry)
        self.editor_scroll = QScrollArea()
        self.editor_scroll.setObjectName("InspectorScroll")
        self.editor_scroll.setWidgetResizable(True)
        self.editor_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.editor_scroll.setWidget(self.editor)
        self.editor_scroll.setMinimumWidth(300)

        deck_panel = QFrame()
        self.deck_panel = deck_panel
        deck_panel.setObjectName("DeckPanel")
        deck_panel.setMinimumWidth(360)
        deck_layout = QVBoxLayout(deck_panel)
        self.deck_layout = deck_layout
        deck_layout.setContentsMargins(18, 18, 18, 18)
        deck_layout.setSpacing(12)
        deck_header = QHBoxLayout()
        deck_title = QLabel("Launchpad Grid")
        deck_title.setObjectName("PanelTitle")
        self.deck_hint = QLabel("Click pads to edit. Use Test to run the selected action.")
        self.deck_hint.setObjectName("PanelHint")
        self.grid_focus_button = QPushButton("Focus Grid")
        self.grid_focus_button.setObjectName("HeaderButton")
        self.grid_focus_button.setToolTip("Hide the side panels and give the Launchpad grid more room.")
        deck_header.addWidget(deck_title)
        deck_header.addStretch(1)
        deck_header.addWidget(self.deck_hint)
        deck_header.addWidget(self.grid_focus_button)
        deck_layout.addLayout(deck_header)
        self.grid_scroll = QScrollArea()
        self.grid_scroll.setObjectName("GridScroll")
        self.grid_scroll.setWidgetResizable(True)
        self.grid_scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.grid_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.grid_scroll.setMinimumSize(0, 0)
        self.grid_scroll.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.grid_scroll.setWidget(self.grid)
        deck_layout.addWidget(self.grid_scroll, 1)

        self.workspace_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.workspace_splitter.setObjectName("WorkspaceSplitter")
        self.workspace_splitter.setChildrenCollapsible(False)
        self.workspace_splitter.addWidget(self.sidebar_scroll)
        self.workspace_splitter.addWidget(deck_panel)
        self.workspace_splitter.addWidget(self.editor_scroll)
        self.workspace_splitter.setStretchFactor(0, 0)
        self.workspace_splitter.setStretchFactor(1, 1)
        self.workspace_splitter.setStretchFactor(2, 0)
        self.workspace_splitter.setSizes([238, 850, 360])
        root.addWidget(self.workspace_splitter, 1)
        self.setCentralWidget(central)
        self._apply_responsive_layout()

        self.header_reconnect_button.clicked.connect(self.reconnect_device)
        self.header_debug_button.clicked.connect(self.show_midi_debug)
        self.header_soundboard_button.clicked.connect(self.show_soundboard_panel)
        self.header_update_button.clicked.connect(self.check_updates)
        self.grid_focus_button.clicked.connect(self.toggle_grid_focus_mode)

    def _build_menu(self) -> None:
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        import_action = QAction("Import Profile", self)
        export_action = QAction("Export Profile", self)
        quit_action = QAction("Quit", self)
        import_action.triggered.connect(self.import_profile)
        export_action.triggered.connect(self.export_profile)
        quit_action.triggered.connect(self.quit_app)
        file_menu.addActions([import_action, export_action])
        file_menu.addSeparator()
        file_menu.addAction(quit_action)

        edit_menu = menu_bar.addMenu("Edit")
        copy_action = QAction("Copy Button Config", self)
        paste_action = QAction("Paste Button Config", self)
        clear_action = QAction("Clear Button", self)
        copy_action.triggered.connect(self.copy_button_config)
        paste_action.triggered.connect(self.paste_button_config)
        clear_action.triggered.connect(self.clear_selected_button)
        edit_menu.addActions([copy_action, paste_action, clear_action])

        view_menu = menu_bar.addMenu("View")
        self.grid_focus_action = QAction("Focus Launchpad Grid", self)
        self.grid_focus_action.setCheckable(True)
        self.grid_focus_action.setShortcut("Ctrl+G")
        self.grid_focus_action.triggered.connect(self.set_grid_focus_mode)
        view_menu.addAction(self.grid_focus_action)

        device_menu = menu_bar.addMenu("Device")
        connect_action = QAction("Connect", self)
        disconnect_action = QAction("Disconnect", self)
        reconnect_action = QAction("Reconnect", self)
        debug_action = QAction("MIDI Debug", self)
        connect_action.triggered.connect(self.connect_device)
        disconnect_action.triggered.connect(self.disconnect_device)
        reconnect_action.triggered.connect(self.reconnect_device)
        debug_action.triggered.connect(self.show_midi_debug)
        device_menu.addActions([connect_action, disconnect_action, reconnect_action])
        device_menu.addSeparator()
        device_menu.addAction(debug_action)

        profiles_menu = menu_bar.addMenu("Profiles")
        manager_action = QAction("Profile Manager", self)
        manager_action.triggered.connect(lambda: ProfileManagerDialog(self).exec())
        profiles_menu.addAction(manager_action)

        soundboard_menu = menu_bar.addMenu("Soundboard")
        panel_action = QAction("Open Soundboard Panel", self)
        stop_all_action = QAction("Stop All Sounds", self)
        panel_action.triggered.connect(self.show_soundboard_panel)
        stop_all_action.triggered.connect(self.stop_all_sounds)
        soundboard_menu.addActions([panel_action, stop_all_action])

        settings_menu = menu_bar.addMenu("Settings")
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        settings_menu.addAction(settings_action)

        help_menu = menu_bar.addMenu("Help")
        update_action = QAction("Check for Updates", self)
        logs_action = QAction("Open Logs Folder", self)
        diagnostics_action = QAction("Copy Diagnostic Info", self)
        about_action = QAction(f"About {APP_NAME}", self)
        update_action.triggered.connect(self.check_updates)
        logs_action.triggered.connect(lambda: self.open_folder(LOGS_DIR))
        diagnostics_action.triggered.connect(self.copy_diagnostic_info)
        about_action.triggered.connect(self.show_about)
        help_menu.addActions([update_action, logs_action, diagnostics_action])
        help_menu.addSeparator()
        help_menu.addAction(about_action)

    def _build_status_bar(self) -> None:
        self.device_status = QLabel("Device: Simulation")
        self.profile_status = QLabel("")
        self.page_status = QLabel("")
        self.last_pressed_status = QLabel("Last: none")
        self.last_result_status = QLabel("Result: none")
        self.mode_status = QLabel("Simulation mode")
        for label in (
            self.device_status,
            self.profile_status,
            self.page_status,
            self.last_pressed_status,
            self.last_result_status,
            self.mode_status,
        ):
            self.statusBar().addPermanentWidget(label)

    def _connect_signals(self) -> None:
        self.grid.button_clicked.connect(self.select_button)
        self.editor.changed.connect(self.save_button_changes)
        self.editor.test_requested.connect(lambda: self.handle_simulation_press(self.grid.selected_button_id))
        self.editor.clear_requested.connect(self.clear_selected_button)
        self.editor.copy_requested.connect(self.copy_button_config)
        self.editor.paste_requested.connect(self.paste_button_config)
        self.sidebar.profile_changed.connect(self.change_profile)
        self.sidebar.page_changed.connect(self.change_page)
        self.sidebar.add_page_requested.connect(self.add_page)
        self.sidebar.duplicate_page_requested.connect(self.duplicate_page)
        self.sidebar.delete_page_requested.connect(self.delete_page)
        self.sidebar.import_profile_requested.connect(self.import_profile)
        self.sidebar.export_profile_requested.connect(self.export_profile)
        self.action_finished.connect(self.on_action_finished)
        self.hardware_button.connect(self.handle_hardware_button)
        self.midi_in.connect(self.on_midi_in)
        self.midi_out.connect(self.on_midi_out)
        self.device_disconnected.connect(self.on_device_disconnected)
        self.audio_state_changed.connect(self.on_audio_state_changed)

    def refresh_all(self) -> None:
        profile_service = self.services.profile_service
        current_page = profile_service.current_page
        self.sidebar.refresh(profile_service)
        if self.grid.selected_button_id not in BUTTON_IDS:
            self.grid.select("A1")
        self.grid.update_from_page(current_page, self.services.action_runner.dangerous_service, self.services.audio_engine)
        self.editor.set_button(current_page.get_button(self.grid.selected_button_id))
        self.profile_status.setText(f"Profile: {profile_service.current_profile.name}")
        self.page_status.setText(f"Page: {current_page.name}")
        self.mode_status.setText("Connected mode" if self.services.device.connected else "Simulation mode")
        self.device_status.setText("Device: Connected" if self.services.device.connected else "Device: Simulation")
        self.header_profile.setText(f"{profile_service.current_profile.name} / {current_page.name}")
        self._set_header_mode(self.services.device.connected)

    def _set_header_mode(self, connected: bool) -> None:
        self.header_mode.setText("Connected mode" if connected else "Simulation mode")
        self.header_mode.setProperty("state", "connected" if connected else "simulation")
        tooltip = (
            "Connected mode: Launchpad MIDI input and output are active."
            if connected
            else "Simulation mode: no Launchpad Mini MK3 MIDI connection is active. Plug in the device, then use Reconnect or Device > Connect. The on-screen grid still works for editing."
        )
        self.header_mode.setToolTip(tooltip)
        self.mode_status.setToolTip(tooltip)
        self.device_status.setToolTip(tooltip)
        self.header_mode.style().unpolish(self.header_mode)
        self.header_mode.style().polish(self.header_mode)

    def refresh_lighting(self) -> None:
        self.services.lighting_service.refresh_page(
            self.services.profile_service.current_page,
            self.services.audio_engine,
            self.services.action_runner.dangerous_service,
        )

    def handle_simulation_press(self, button_id: str) -> None:
        if not button_id:
            return
        self.select_button(button_id)
        self.last_pressed_status.setText(f"Last: {button_id}")
        self.services.action_runner.handle_button_press(button_id, "simulation")

    def handle_hardware_button(self, button_id: str, pressed: bool, raw) -> None:
        if not pressed:
            return
        self.select_button(button_id)
        self.last_pressed_status.setText(f"Last: {button_id}")
        self.services.lighting_service.flash(button_id, "white", delay=0.12)
        self.services.action_runner.handle_button_press(button_id, "midi")

    def select_button(self, button_id: str) -> None:
        previous = self.grid.select(button_id)
        self.editor.set_button(self.services.profile_service.current_page.get_button(button_id))
        self.grid.update_buttons(
            self.services.profile_service.current_page,
            {previous, button_id},
            self.services.action_runner.dangerous_service,
            self.services.audio_engine,
        )

    def save_button_changes(self) -> None:
        if self.services.settings_service.settings.profile_autosave:
            self.services.profile_service.save_current()
        self.grid.update_button(
            self.services.profile_service.current_page,
            self.grid.selected_button_id,
            self.services.action_runner.dangerous_service,
            self.services.audio_engine,
        )
        self.refresh_lighting()

    def clear_selected_button(self) -> None:
        button_id = self.grid.selected_button_id
        self.services.profile_service.current_page.buttons[button_id] = ButtonConfig.blank(button_id)
        self.services.profile_service.save_current()
        self.refresh_all()
        self.refresh_lighting()

    def copy_button_config(self) -> None:
        button = self.services.profile_service.current_page.get_button(self.grid.selected_button_id)
        self.clipboard_button = button.to_dict()
        QApplication.clipboard().setText(json.dumps(self.clipboard_button, indent=2))
        self.statusBar().showMessage("Button config copied.", 2500)

    def paste_button_config(self) -> None:
        data = self.clipboard_button
        if data is None:
            try:
                data = json.loads(QApplication.clipboard().text())
            except json.JSONDecodeError:
                QMessageBox.warning(self, APP_NAME, "Clipboard does not contain a button config.")
                return
        button_id = self.grid.selected_button_id
        self.services.profile_service.current_page.buttons[button_id] = ButtonConfig.from_dict(button_id, data)
        self.services.profile_service.save_current()
        self.refresh_all()
        self.refresh_lighting()

    def change_profile(self, profile_id: str) -> None:
        if profile_id and self.services.profile_service.set_current_profile(profile_id):
            self.services.action_runner.disarm_all()
            self.services.lighting_service.stop_all_blinks()
            self.refresh_all()
            self.refresh_lighting()

    def change_page(self, page_id: str) -> None:
        old_page_id = self.services.profile_service.current_page.id
        if page_id and self.services.profile_service.set_current_page(page_id):
            self.services.action_runner.disarm_all()
            self.services.lighting_service.stop_all_blinks()
            self.services.audio_engine.stop_page(old_page_id)
            self.refresh_all()
            self.refresh_lighting()

    def add_page(self) -> None:
        name, ok = QInputDialog.getText(self, "Add Page", "Page name:")
        if ok and name.strip():
            page = self.services.profile_service.add_page(name.strip())
            self.services.profile_service.set_current_page(page.id)
            self.refresh_all()
            self.refresh_lighting()

    def duplicate_page(self) -> None:
        page = self.services.profile_service.duplicate_page(self.services.profile_service.current_page.id)
        self.services.profile_service.set_current_page(page.id)
        self.refresh_all()
        self.refresh_lighting()

    def delete_page(self) -> None:
        if QMessageBox.question(self, APP_NAME, "Delete the current page?") != QMessageBox.StandardButton.Yes:
            return
        if not self.services.profile_service.delete_page(self.services.profile_service.current_page.id):
            QMessageBox.information(self, APP_NAME, "A profile must keep at least one page.")
        self.refresh_all()
        self.refresh_lighting()

    def import_profile(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import Profile", str(PROFILES_DIR), "JSON files (*.json)")
        if not path:
            return
        try:
            profile = self.services.profile_service.import_profile(Path(path))
            self.services.profile_service.set_current_profile(profile.id)
        except Exception as exc:
            QMessageBox.warning(self, APP_NAME, f"Profile could not be imported:\n{exc}")
            return
        self.refresh_all()

    def export_profile(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Profile",
            str(Path.home() / f"{self.services.profile_service.current_profile.id}.json"),
            "JSON files (*.json)",
        )
        if path:
            self.services.profile_service.export_profile(self.services.profile_service.current_profile_id, Path(path))

    def connect_device(self) -> None:
        if self._connect_thread is not None:
            self.statusBar().showMessage("MIDI connection is already in progress.", 2500)
            return
        settings = self.services.settings_service.settings
        input_port, output_port = MidiManager.resolve_launchpad_ports(settings.midi_input_port, settings.midi_output_port)
        if not input_port and not output_port:
            self.statusBar().showMessage("No Launchpad MIDI ports detected; simulation mode is active.", 4000)
            self.refresh_all()
            return
        self.statusBar().showMessage("Connecting MIDI device...", 4000)
        self._connect_thread = QThread(self)
        self._connect_worker = MidiConnectionWorker(self.services.device, input_port, output_port)
        self._connect_worker.moveToThread(self._connect_thread)
        self._connect_thread.started.connect(self._connect_worker.run)
        self._connect_worker.finished.connect(self.on_connect_finished)
        self._connect_worker.finished.connect(self._connect_thread.quit)
        self._connect_thread.finished.connect(self._connect_worker.deleteLater)
        self._connect_thread.finished.connect(self._connect_thread.deleteLater)
        self._connect_thread.finished.connect(self.clear_connect_worker)
        self._connect_thread.start()
        self.refresh_all()

    def disconnect_device(self) -> None:
        self.services.device.close()
        self.services.action_runner.disarm_all()
        self.services.lighting_service.stop_all_blinks()
        self.services.lighting_service.clear()
        self.refresh_all()

    def reconnect_device(self) -> None:
        self.disconnect_device()
        self.connect_device()

    def show_midi_debug(self) -> None:
        if self.midi_debug_window is None:
            self.midi_debug_window = MidiDebugWindow(self.services.device)
            self.midi_debug_window.closed.connect(self.disable_midi_debug_callbacks)
        self.midi_debug_window.refresh_ports()
        self.enable_midi_debug_callbacks()
        self.midi_debug_window.show()
        self.midi_debug_window.raise_()

    def enable_midi_debug_callbacks(self) -> None:
        if self._midi_debug_callbacks_active:
            return
        self.services.device.midi_in_callback = lambda message, text: self.midi_in.emit(message, text)
        self.services.device.midi_out_callback = lambda message, text: self.midi_out.emit(message, text)
        self._midi_debug_callbacks_active = True

    def disable_midi_debug_callbacks(self) -> None:
        self.services.device.midi_in_callback = None
        self.services.device.midi_out_callback = None
        self._midi_debug_callbacks_active = False

    def on_midi_in(self, message, text: str) -> None:
        if self.midi_debug_window and self.midi_debug_window.isVisible():
            self.midi_debug_window.append_incoming(message, text)

    def on_midi_out(self, message, text: str) -> None:
        if self.midi_debug_window and self.midi_debug_window.isVisible():
            self.midi_debug_window.append_outgoing(message, text)

    def on_action_finished(self, button_id: str, result) -> None:
        self.last_result_status.setText(f"Result: {result.message[:60]}")
        if result.details.get("page_changed"):
            self.services.lighting_service.stop_blink(button_id)
            self.refresh_all()
            self.refresh_lighting()
            return
        if "Press again" in result.message:
            self.services.lighting_service.blink(button_id, "yellow", "red")
            QTimer.singleShot(5200, self.refresh_after_danger_timeout)
        elif result.success:
            self.services.lighting_service.stop_blink(button_id)
            self.services.lighting_service.flash(button_id, "green", delay=0.18)
        else:
            self.services.lighting_service.stop_blink(button_id)
            self.services.lighting_service.flash(button_id, "red", delay=0.3)
        self.grid.update_button(
            self.services.profile_service.current_page,
            button_id,
            self.services.action_runner.dangerous_service,
            self.services.audio_engine,
        )

    def show_soundboard_panel(self) -> None:
        self.soundboard_panel = SoundboardPanel(self.services.audio_engine, self.services.settings_service, self)
        self.soundboard_panel.exec()

    def stop_all_sounds(self) -> None:
        self.services.audio_engine.stop_all()
        self.refresh_all()
        self.refresh_lighting()

    def show_settings(self) -> None:
        dialog = SettingsDialog(self.services.settings_service, self, self.services.startup_service)
        if dialog.exec():
            self.setStyleSheet(load_theme(self.services.settings_service.settings.theme))
            self._apply_responsive_layout()
            self.services.audio_engine.set_global_volume(self.services.settings_service.settings.soundboard_global_volume)
            self.services.audio_engine.set_default_output_device(self.services.settings_service.settings.soundboard_default_output_device)
            self.services.audio_engine.set_voice_chat_output_device(self.services.settings_service.settings.soundboard_voice_chat_output_device)
            self.services.audio_engine.set_monitor_voice_chat_routes(self.services.settings_service.settings.soundboard_monitor_voice_chat)
            self.services.audio_engine.performance_logging_enabled = self.services.settings_service.settings.enable_performance_logging
            self.services.performance_monitor.set_enabled(self.services.settings_service.settings.enable_performance_logging)
            native_acceleration.configure(self.services.settings_service.settings.use_native_acceleration, self.services.logger)

    def toggle_grid_focus_mode(self) -> None:
        self.set_grid_focus_mode(not self._grid_focus_mode)

    def set_grid_focus_mode(self, enabled: bool) -> None:
        self._grid_focus_mode = bool(enabled)
        if hasattr(self, "grid_focus_action"):
            self.grid_focus_action.setChecked(self._grid_focus_mode)
        self.grid_focus_button.setText("Edit Layout" if self._grid_focus_mode else "Focus Grid")
        self.grid_focus_button.setToolTip(
            "Show the profile library and button editor."
            if self._grid_focus_mode
            else "Hide the side panels and give the Launchpad grid more room."
        )
        self._apply_responsive_layout()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "workspace_splitter"):
            self._apply_responsive_layout()

    def _apply_responsive_layout(self) -> None:
        width = self.width()
        base_density = self.services.settings_service.settings.grid_density
        if self._grid_focus_mode:
            if width < 1350:
                density = "mini"
            elif width < 1550 and base_density != "compact":
                density = "compact"
            else:
                density = base_density
        elif width < 1600:
            density = "mini"
        elif width < 1700 and base_density != "compact":
            density = "compact"
        else:
            density = base_density
        if density != getattr(self, "_applied_grid_density", None):
            self._applied_grid_density = density
            self.grid.set_density(density)

        compact_header = width < 1350
        narrow_header = width < 1180
        compact_workspace = width < 1350
        self.app_header.setVisible(not self._grid_focus_mode)
        if self._grid_focus_mode:
            self.main_root_layout.setContentsMargins(14, 12, 14, 12)
            self.main_root_layout.setSpacing(10)
            self.deck_layout.setContentsMargins(12, 12, 12, 12)
            self.deck_layout.setSpacing(8)
        else:
            self.main_root_layout.setContentsMargins(18, 16, 18, 16)
            self.main_root_layout.setSpacing(14)
            self.deck_layout.setContentsMargins(18, 18, 18, 18)
            self.deck_layout.setSpacing(12)

        self.deck_hint.setVisible(not compact_header and not self._grid_focus_mode)
        self.header_profile.setVisible(not compact_header)
        self.header_mode.setVisible(not narrow_header)
        self.header_soundboard_button.setText("Sounds" if compact_header else "Soundboard")
        self.header_reconnect_button.setText("Reconnect" if not narrow_header else "Link")
        self.header_debug_button.setVisible(not compact_header)
        self.header_soundboard_button.setVisible(not compact_header)
        self.header_update_button.setVisible(not compact_header)
        self.sidebar_scroll.setVisible(not compact_workspace and not self._grid_focus_mode)
        self.editor_scroll.setVisible(not self._grid_focus_mode)

        if self._grid_focus_mode:
            self.workspace_splitter.setOrientation(Qt.Orientation.Horizontal)
            self.grid_scroll.setWidgetResizable(True)
            self.deck_panel.setMinimumWidth(360)
            self.workspace_splitter.setSizes([0, max(760, width - 80), 0])
        elif compact_workspace:
            self.workspace_splitter.setOrientation(Qt.Orientation.Vertical)
            self.grid_scroll.setWidgetResizable(True)
            self.sidebar_scroll.setMinimumWidth(0)
            self.editor_scroll.setMinimumWidth(0)
            self.editor_scroll.setMinimumHeight(260)
            self.deck_panel.setMinimumWidth(360)
            self.deck_panel.setMinimumHeight(220)
            editor_height = 300 if self.height() >= 720 else 260
            self.workspace_splitter.setSizes([0, max(220, self.height() - editor_height - 260), editor_height])
        else:
            self.workspace_splitter.setOrientation(Qt.Orientation.Horizontal)
            self.grid_scroll.setWidgetResizable(True)
            self.sidebar_scroll.setMinimumWidth(210)
            self.editor_scroll.setMinimumHeight(0)
            self.deck_panel.setMinimumHeight(0)
            self.editor_scroll.setMinimumWidth(300)
            self.deck_panel.setMinimumWidth(520)
            self.workspace_splitter.setSizes([238, max(620, width - 660), 360])

    def show_first_run(self) -> None:
        dialog = SetupWizard(self.services.profile_service, self.services.settings_service, self)
        dialog.exec()
        self.refresh_all()

    def check_updates(self) -> None:
        UpdateDialog(self.services.settings_service, self.services.logger, self, auto_check=True).exec()

    def check_updates_on_startup(self) -> None:
        if self._startup_update_thread is not None:
            return
        manifest_url = self.services.settings_service.settings.update_manifest_url.strip()
        if not manifest_url:
            return
        service = UpdateService(__version__, self.services.logger)
        self._startup_update_thread = QThread(self)
        self._startup_update_worker = UpdateCheckWorker(service, manifest_url)
        self._startup_update_worker.moveToThread(self._startup_update_thread)
        self._startup_update_thread.started.connect(self._startup_update_worker.run)
        self._startup_update_worker.finished.connect(self.on_startup_update_result)
        self._startup_update_worker.failed.connect(self.on_startup_update_error)
        self._startup_update_worker.finished.connect(self._startup_update_thread.quit)
        self._startup_update_worker.failed.connect(self._startup_update_thread.quit)
        self._startup_update_thread.finished.connect(self._startup_update_worker.deleteLater)
        self._startup_update_thread.finished.connect(self._startup_update_thread.deleteLater)
        self._startup_update_thread.finished.connect(self.clear_startup_update_worker)
        self._startup_update_thread.start()

    def on_startup_update_result(self, result) -> None:
        if result.available or result.unsupported:
            self.statusBar().showMessage(result.message, 8000)
        elif self.services.logger:
            self.services.logger.info("Startup update check found no update.")

    def on_startup_update_error(self, message: str) -> None:
        if self.services.logger:
            self.services.logger.warning("Startup update check failed: %s", message)

    def clear_startup_update_worker(self) -> None:
        self._startup_update_thread = None
        self._startup_update_worker = None

    def copy_diagnostic_info(self) -> None:
        info = [
            f"App version: {__version__}",
            f"Python: {sys.version.split()[0]}",
            f"OS: {platform.platform()}",
            f"MIDI inputs: {', '.join(MidiManager.available_input_ports()) or 'none'}",
            f"MIDI outputs: {', '.join(MidiManager.available_output_ports()) or 'none'}",
            f"Current profile: {self.services.profile_service.current_profile.name}",
            f"Current page: {self.services.profile_service.current_page.name}",
            f"Simulation mode: {not self.services.device.connected}",
            f"Log folder: {LOGS_DIR}",
            f"Install mode: {'installed' if getattr(sys, 'frozen', False) else 'portable/source'}",
            "Native acceleration available: false",
        ]
        QApplication.clipboard().setText("\n".join(info))
        self.statusBar().showMessage("Diagnostic info copied.", 3000)

    def show_about(self) -> None:
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"{APP_NAME} {__version__}\n\nA Windows desktop macro deck app for Launchpad Mini MK3.",
        )

    def open_folder(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(str(path))  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", str(path)])

    def on_connect_finished(self, success: bool, message: str, input_port: str, output_port: str) -> None:
        if success:
            self.services.settings_service.update(midi_input_port=input_port, midi_output_port=output_port)
            self.statusBar().showMessage("MIDI device connected.", 3000)
            self.refresh_lighting()
        else:
            QMessageBox.warning(self, APP_NAME, f"Could not connect MIDI device:\n{message}")
        self.refresh_all()

    def clear_connect_worker(self) -> None:
        self._connect_thread = None
        self._connect_worker = None

    def on_device_disconnected(self, reason: str) -> None:
        self.services.action_runner.disarm_all()
        self.services.lighting_service.stop_all_blinks()
        self.services.lighting_service.clear()
        self.statusBar().showMessage(f"MIDI device disconnected: {reason}", 5000)
        self.refresh_all()

    def on_audio_state_changed(self) -> None:
        self.grid.update_from_page(
            self.services.profile_service.current_page,
            self.services.action_runner.dangerous_service,
            self.services.audio_engine,
        )
        self.refresh_lighting()
        if self.soundboard_panel is not None and self.soundboard_panel.isVisible():
            self.soundboard_panel.refresh()

    def refresh_after_danger_timeout(self) -> None:
        armed = self.services.action_runner.dangerous_service
        for button_id in BUTTON_IDS:
            if not armed.is_armed(button_id):
                self.services.lighting_service.stop_blink(button_id)
        self.grid.update_from_page(self.services.profile_service.current_page, armed, self.services.audio_engine)
        self.refresh_lighting()

    def closeEvent(self, event) -> None:
        if not self._force_quit and self.services.settings_service.settings.minimize_to_tray and self.tray.tray.isVisible():
            self.hide()
            event.ignore()
            return
        self.services.audio_engine.stop_all()
        self.services.device.close()
        super().closeEvent(event)

    def restore_from_tray(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def quit_app(self) -> None:
        self._force_quit = True
        self.close()
