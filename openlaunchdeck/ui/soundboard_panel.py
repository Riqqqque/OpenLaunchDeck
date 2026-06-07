from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from ..audio.input_devices import list_input_devices
from ..audio.bridge_driver import detect_openlaunchdeck_bridge
from ..audio.output_devices import hidden_advanced_output_count, hidden_duplicate_count, list_output_devices
from ..audio.voice_routing import find_best_voice_route


class SoundboardPanel(QDialog):
    def __init__(self, audio_engine, settings_service=None, parent=None) -> None:
        super().__init__(parent)
        self.audio_engine = audio_engine
        self.settings_service = settings_service
        self.setWindowTitle("Soundboard")
        self.setObjectName("SoundboardPanel")
        self.resize(560, 520)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        form = QFormLayout()
        form.setSpacing(10)
        self.output_combo = QComboBox()
        self.output_combo.addItem("System default (recommended)", "")
        devices = list_output_devices()
        input_devices = list_input_devices()
        self._add_device_items(self.output_combo, devices)
        current_device = audio_engine.default_output_device_id
        if current_device:
            self._select_saved_device(self.output_combo, current_device)
        self.voice_output_combo = QComboBox()
        self.voice_output_combo.addItem("Not configured", "")
        self._add_device_items(self.voice_output_combo, devices)
        current_voice_device = audio_engine.voice_chat_output_device_id
        if current_voice_device:
            self._select_saved_device(self.voice_output_combo, current_voice_device)
        self.mic_input_combo = QComboBox()
        self.mic_input_combo.addItem("System default microphone", "")
        self._add_device_items(self.mic_input_combo, input_devices, "Audio input")
        current_mic_device = audio_engine.voice_route_microphone_device_id
        if current_mic_device:
            self._select_saved_device(self.mic_input_combo, current_mic_device)
        self.mic_route_check = QCheckBox()
        self.mic_route_check.setChecked(audio_engine.voice_route_microphone_enabled)
        self.mic_volume_spin = QSpinBox()
        self.mic_volume_spin.setRange(0, 100)
        self.mic_volume_spin.setValue(audio_engine.voice_route_microphone_volume)
        self.monitor_voice_check = QCheckBox()
        self.monitor_voice_check.setChecked(audio_engine.monitor_voice_chat_routes)
        self.volume_spin = QSpinBox()
        self.volume_spin.setRange(0, 100)
        self.volume_spin.setValue(audio_engine.global_volume)
        form.addRow("Default Output", self.output_combo)
        form.addRow("Voice Route Output", self.voice_output_combo)
        form.addRow("Microphone Input", self.mic_input_combo)
        form.addRow("Route Microphone", self.mic_route_check)
        form.addRow("Microphone Volume", self.mic_volume_spin)
        form.addRow("Monitor Voice Routes", self.monitor_voice_check)
        form.addRow("Global Volume", self.volume_spin)
        layout.addLayout(form)
        self.route_status = QLabel()
        self.route_status.setWordWrap(True)
        self.route_status.setObjectName("MutedText")
        layout.addWidget(self.route_status)
        self.bridge_status = QLabel()
        self.bridge_status.setWordWrap(True)
        self.bridge_status.setObjectName("MutedText")
        layout.addWidget(self.bridge_status)
        discord_row = QHBoxLayout()
        discord_row.setSpacing(8)
        self.discord_input = QLabel("Discord input: not configured")
        self.discord_input.setWordWrap(True)
        self.discord_input.setObjectName("MutedText")
        self.auto_route_button = QPushButton("Auto Find Route")
        self.auto_route_button.setObjectName("SecondaryButton")
        self.copy_discord_input_button = QPushButton("Copy Discord Input")
        self.copy_discord_input_button.setObjectName("SecondaryButton")
        discord_row.addWidget(self.discord_input, 1)
        discord_row.addWidget(self.auto_route_button)
        discord_row.addWidget(self.copy_discord_input_button)
        layout.addLayout(discord_row)
        hidden_duplicates = hidden_duplicate_count(devices)
        hidden_advanced = hidden_advanced_output_count()
        self.device_note = QLabel()
        self.device_note.setWordWrap(True)
        self.device_note.setObjectName("MutedText")
        note_parts = []
        if hidden_duplicates:
            note_parts.append(f"{hidden_duplicates} duplicate Windows output names")
        if hidden_advanced:
            note_parts.append(f"{hidden_advanced} advanced mixer buses")
        if note_parts:
            self.device_note.setText(
                "Hidden " + " and ".join(note_parts) + ". "
                "The selected device still uses a real Windows output ID."
            )
            layout.addWidget(self.device_note)

        title = QLabel("Currently Playing")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        self.stop_all_button = QPushButton("Stop All Sounds")
        self.refresh_button = QPushButton("Refresh")
        self.docs_button = QPushButton("Open Soundboard Docs")
        self.stop_all_button.setObjectName("PrimaryButton")
        self.refresh_button.setObjectName("SecondaryButton")
        self.docs_button.setObjectName("SecondaryButton")
        layout.addWidget(self.stop_all_button)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.docs_button)
        self.stop_all_button.clicked.connect(self._stop_all)
        self.refresh_button.clicked.connect(self.refresh)
        self.docs_button.clicked.connect(self.open_docs)
        self.auto_route_button.clicked.connect(self.auto_find_route)
        self.copy_discord_input_button.clicked.connect(self.copy_discord_input)
        self.output_combo.currentIndexChanged.connect(lambda _index: self._set_output_device())
        self.voice_output_combo.currentIndexChanged.connect(lambda _index: self._set_voice_output_device())
        self.mic_input_combo.currentIndexChanged.connect(lambda _index: self._set_mic_input_device())
        self.mic_route_check.stateChanged.connect(lambda _state: self._set_mic_route_enabled())
        self.mic_volume_spin.valueChanged.connect(self._set_mic_route_volume)
        self.monitor_voice_check.stateChanged.connect(lambda _state: self._set_monitor_voice_routes())
        self.volume_spin.valueChanged.connect(self._set_global_volume)
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh()

    def refresh(self) -> None:
        self.refresh_route_status()
        self.list_widget.clear()
        for instance in self.audio_engine.currently_playing():
            name = instance.display_name or Path(instance.file_path).name
            loop_text = " loop" if instance.loop else ""
            route_text = " voice" if instance.routed_to_voice_chat else ""
            self.list_widget.addItem(f"{instance.button_id}: {name} ({instance.volume}%{loop_text}{route_text})")

    def _stop_all(self) -> None:
        self.audio_engine.stop_all()
        self.refresh()

    def _set_output_device(self) -> None:
        device_id = str(self.output_combo.currentData() or "")
        self.audio_engine.set_default_output_device(device_id)
        if self.settings_service is not None:
            self.settings_service.update(soundboard_default_output_device=device_id)

    def _set_voice_output_device(self) -> None:
        device_id = str(self.voice_output_combo.currentData() or "")
        self.audio_engine.set_voice_chat_output_device(device_id)
        if self.settings_service is not None:
            self.settings_service.update(soundboard_voice_chat_output_device=device_id)
        self.refresh_route_status()

    def _set_mic_input_device(self) -> None:
        device_id = str(self.mic_input_combo.currentData() or "")
        self.audio_engine.set_voice_route_microphone_device(device_id)
        if self.settings_service is not None:
            self.settings_service.update(soundboard_voice_route_microphone_device=device_id)
        self.refresh_route_status()

    def _set_mic_route_enabled(self) -> None:
        enabled = self.mic_route_check.isChecked()
        self.audio_engine.set_voice_route_microphone_enabled(enabled)
        if self.settings_service is not None:
            self.settings_service.update(soundboard_voice_route_microphone_enabled=enabled)
        self.refresh_route_status()

    def _set_mic_route_volume(self, volume: int) -> None:
        self.audio_engine.set_voice_route_microphone_volume(volume)
        if self.settings_service is not None:
            self.settings_service.update(soundboard_voice_route_microphone_volume=volume)

    def _set_monitor_voice_routes(self) -> None:
        enabled = self.monitor_voice_check.isChecked()
        self.audio_engine.set_monitor_voice_chat_routes(enabled)
        if self.settings_service is not None:
            self.settings_service.update(soundboard_monitor_voice_chat=enabled)

    def _set_global_volume(self, volume: int) -> None:
        self.audio_engine.set_global_volume(volume)
        if self.settings_service is not None:
            self.settings_service.update(soundboard_global_volume=volume)

    def open_docs(self) -> None:
        docs_path = Path(__file__).resolve().parents[2] / "docs" / "soundboard_setup.md"
        if not docs_path.exists() and hasattr(sys, "_MEIPASS"):
            docs_path = Path(sys._MEIPASS) / "docs" / "soundboard_setup.md"  # type: ignore[attr-defined]
        if docs_path.exists():
            if sys.platform == "win32":
                os.startfile(str(docs_path))  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", str(docs_path)])

    def refresh_route_status(self) -> None:
        status = self.audio_engine.voice_route_status()
        messages = [status.message]
        mic_state = self.audio_engine.voice_route_microphone_state()
        if self.audio_engine.voice_route_microphone_enabled or mic_state.running:
            messages.append(mic_state.message)
        self.route_status.setText("\n".join(messages))
        bridge = detect_openlaunchdeck_bridge()
        self.bridge_status.setText(f"Audio Bridge: {bridge.message}")
        if status.ready:
            self.discord_input.setText(f"Discord input: {status.discord_input_name}")
            self.copy_discord_input_button.setEnabled(True)
        else:
            self.discord_input.setText("Discord input: not ready")
            self.copy_discord_input_button.setEnabled(False)

    def copy_discord_input(self) -> None:
        status = self.audio_engine.voice_route_status()
        if status.discord_input_name:
            QApplication.clipboard().setText(status.discord_input_name)

    def auto_find_route(self) -> None:
        route = find_best_voice_route()
        if route is None:
            self.route_status.setText("No voice route is ready. Windows needs a playback output with a matching recording input for Discord.")
            return
        index = self.voice_output_combo.findData(route.output_id)
        if index < 0:
            self.voice_output_combo.addItem(route.output_name, route.output_id)
            index = self.voice_output_combo.findData(route.output_id)
        self.voice_output_combo.setCurrentIndex(max(0, index))
        self._set_voice_output_device()

    def _add_device_items(self, combo: QComboBox, devices: list[dict[str, str | int]], fallback_name: str = "Audio output") -> None:
        for device in devices:
            duplicate_count = int(device.get("duplicate_count", 1))
            label = str(device.get("display_name") or device.get("description") or fallback_name)
            combo.addItem(label, str(device.get("id") or ""))
            if duplicate_count > 1:
                index = combo.count() - 1
                combo.setItemData(
                    index,
                    f"Windows reported {duplicate_count} outputs named {label}. "
                    "OpenLaunchDeck shows one entry to keep this list usable.",
                    Qt.ItemDataRole.ToolTipRole,
                )

    def _select_saved_device(self, combo: QComboBox, device_id: str) -> None:
        index = combo.findData(device_id)
        if index < 0:
            combo.addItem("Saved device not shown in current Windows list", device_id)
            index = combo.findData(device_id)
        combo.setCurrentIndex(max(0, index))
