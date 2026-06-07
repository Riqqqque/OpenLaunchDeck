from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from ..audio.output_devices import hidden_advanced_output_count, hidden_duplicate_count, list_output_devices
from ..paths import APP_DATA_DIR


class SettingsDialog(QDialog):
    def __init__(self, settings_service, parent=None, startup_service=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setObjectName("SettingsDialog")
        self.resize(620, 680)
        self.settings_service = settings_service
        self.startup_service = startup_service
        settings = settings_service.settings
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        form = QFormLayout()
        form.setSpacing(10)

        self.theme = QComboBox()
        for theme in ("dark", "light", "system"):
            self.theme.addItem(theme, theme)
        self.theme.setCurrentIndex(max(0, self.theme.findData(settings.theme)))

        self.grid_density = QComboBox()
        self.grid_density.addItem("Compact", "compact")
        self.grid_density.addItem("Comfortable", "comfortable")
        self.grid_density.addItem("Large", "large")
        self.grid_density.setCurrentIndex(max(0, self.grid_density.findData(settings.grid_density)))

        self.auto_connect = QCheckBox()
        self.auto_connect.setChecked(settings.auto_connect)
        self.start_minimized = QCheckBox()
        self.start_minimized.setChecked(settings.start_minimized)
        self.minimize_to_tray = QCheckBox()
        self.minimize_to_tray.setChecked(settings.minimize_to_tray)
        self.launch_at_startup = QCheckBox()
        self.launch_at_startup.setChecked(settings.launch_at_startup)
        if self.startup_service is None or not self.startup_service.is_available():
            self.launch_at_startup.setChecked(False)
            self.launch_at_startup.setEnabled(False)
            self.launch_at_startup.setToolTip("Launch at startup is available in the Windows desktop app.")
        else:
            self.launch_at_startup.setToolTip("Start OpenLaunchDeck when you sign in to Windows.")
        self.midi_input = QLineEdit(settings.midi_input_port)
        self.midi_output = QLineEdit(settings.midi_output_port)
        self.midi_debug = QCheckBox()
        self.midi_debug.setChecked(settings.midi_debug_logging)
        self.autosave = QCheckBox()
        self.autosave.setChecked(settings.profile_autosave)
        self.backups = QCheckBox()
        self.backups.setChecked(settings.backup_profiles_automatically)
        devices = list_output_devices()
        self.output_device = QComboBox()
        self.output_device.addItem("System default (recommended)", "")
        self._add_device_items(self.output_device, devices)
        self._select_saved_device(self.output_device, settings.soundboard_default_output_device)
        self.voice_output_device = QComboBox()
        self.voice_output_device.addItem("Not configured", "")
        self._add_device_items(self.voice_output_device, devices)
        self._select_saved_device(self.voice_output_device, settings.soundboard_voice_chat_output_device)
        self.monitor_voice_routes = QCheckBox()
        self.monitor_voice_routes.setChecked(settings.soundboard_monitor_voice_chat)
        self.global_volume = QSpinBox()
        self.global_volume.setRange(0, 100)
        self.global_volume.setValue(settings.soundboard_global_volume)
        self.stop_on_exit = QCheckBox()
        self.stop_on_exit.setChecked(settings.soundboard_stop_sounds_on_exit)
        self.check_updates = QCheckBox()
        self.check_updates.setChecked(settings.check_updates_on_startup)
        self.update_channel = QComboBox()
        self.update_channel.addItem("stable", "stable")
        self.update_channel.addItem("beta", "beta")
        self.update_channel.setCurrentIndex(max(0, self.update_channel.findData(settings.update_channel)))
        self.update_url = QLineEdit(settings.update_manifest_url)
        self.performance_logging = QCheckBox()
        self.performance_logging.setChecked(settings.enable_performance_logging)
        self.native_acceleration = QCheckBox()
        self.native_acceleration.setChecked(settings.use_native_acceleration)
        config_button = QPushButton(str(APP_DATA_DIR))
        config_button.setObjectName("SecondaryButton")
        config_button.clicked.connect(lambda: self.parent().open_folder(APP_DATA_DIR) if self.parent() else None)

        form.addRow("Theme", self.theme)
        form.addRow("Grid density", self.grid_density)
        form.addRow("Auto-connect", self.auto_connect)
        form.addRow("Start minimized", self.start_minimized)
        form.addRow("Minimize to tray", self.minimize_to_tray)
        form.addRow("Launch at startup", self.launch_at_startup)
        form.addRow("MIDI input port", self.midi_input)
        form.addRow("MIDI output port", self.midi_output)
        form.addRow("MIDI debug logging", self.midi_debug)
        form.addRow("Config folder", config_button)
        form.addRow("Profile autosave", self.autosave)
        form.addRow("Automatic backups", self.backups)
        form.addRow("Sound output device", self.output_device)
        form.addRow("Voice chat output device", self.voice_output_device)
        audio_note = QLabel("Use system default for normal monitoring. Use a virtual mixer only for the voice chat output route.")
        audio_note.setWordWrap(True)
        audio_note.setObjectName("MutedText")
        form.addRow("Audio routing", audio_note)
        hidden_duplicates = hidden_duplicate_count(devices)
        hidden_advanced = hidden_advanced_output_count()
        note_parts = []
        if hidden_duplicates:
            note_parts.append(f"{hidden_duplicates} duplicate Windows outputs")
        if hidden_advanced:
            note_parts.append(f"{hidden_advanced} advanced VoiceMeeter buses")
        if note_parts:
            note = QLabel("Hidden " + " and ".join(note_parts))
            note.setWordWrap(True)
            note.setObjectName("MutedText")
            form.addRow("Audio devices", note)
        form.addRow("Monitor voice routes", self.monitor_voice_routes)
        form.addRow("Soundboard volume", self.global_volume)
        form.addRow("Stop sounds on exit", self.stop_on_exit)
        form.addRow("Check updates on startup", self.check_updates)
        form.addRow("Update channel", self.update_channel)
        form.addRow("Update manifest URL", self.update_url)
        form.addRow("Performance logging", self.performance_logging)
        form.addRow("Native acceleration", self.native_acceleration)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self) -> None:
        launch_at_startup = self.launch_at_startup.isChecked()
        if self.startup_service is not None:
            if not self.startup_service.set_enabled(launch_at_startup):
                QMessageBox.warning(
                    self,
                    "Startup setting not changed",
                    "OpenLaunchDeck could not update the Windows startup entry. Check the log for details.",
                )
                return

        self.settings_service.update(
            theme=self.theme.currentData(),
            grid_density=self.grid_density.currentData(),
            auto_connect=self.auto_connect.isChecked(),
            start_minimized=self.start_minimized.isChecked(),
            minimize_to_tray=self.minimize_to_tray.isChecked(),
            launch_at_startup=launch_at_startup,
            midi_input_port=self.midi_input.text(),
            midi_output_port=self.midi_output.text(),
            midi_debug_logging=self.midi_debug.isChecked(),
            profile_autosave=self.autosave.isChecked(),
            backup_profiles_automatically=self.backups.isChecked(),
            soundboard_default_output_device=str(self.output_device.currentData() or ""),
            soundboard_voice_chat_output_device=str(self.voice_output_device.currentData() or ""),
            soundboard_monitor_voice_chat=self.monitor_voice_routes.isChecked(),
            soundboard_global_volume=self.global_volume.value(),
            soundboard_stop_sounds_on_exit=self.stop_on_exit.isChecked(),
            check_updates_on_startup=self.check_updates.isChecked(),
            update_channel=self.update_channel.currentData(),
            update_manifest_url=self.update_url.text(),
            enable_performance_logging=self.performance_logging.isChecked(),
            use_native_acceleration=self.native_acceleration.isChecked(),
        )
        super().accept()

    def _add_device_items(self, combo: QComboBox, devices: list[dict[str, str | int]]) -> None:
        for device in devices:
            combo.addItem(str(device.get("display_name") or device.get("description") or "Audio output"), str(device.get("id") or ""))

    def _select_saved_device(self, combo: QComboBox, device_id: str) -> None:
        if not device_id:
            combo.setCurrentIndex(0)
            return
        index = combo.findData(device_id)
        if index < 0:
            combo.addItem("Saved device not currently available", device_id)
            index = combo.findData(device_id)
        combo.setCurrentIndex(max(0, index))
