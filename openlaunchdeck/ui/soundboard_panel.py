from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QCheckBox, QComboBox, QDialog, QFormLayout, QLabel, QListWidget, QPushButton, QSpinBox, QVBoxLayout

from ..audio.output_devices import list_output_devices


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
        self.output_combo.addItem("System default", "")
        devices = list_output_devices()
        for device in devices:
            self.output_combo.addItem(device["description"], device["id"])
        current_device = audio_engine.default_output_device_id
        if current_device:
            index = self.output_combo.findData(current_device)
            if index >= 0:
                self.output_combo.setCurrentIndex(index)
        self.voice_output_combo = QComboBox()
        self.voice_output_combo.addItem("Not configured", "")
        for device in devices:
            self.voice_output_combo.addItem(device["description"], device["id"])
        current_voice_device = audio_engine.voice_chat_output_device_id
        if current_voice_device:
            index = self.voice_output_combo.findData(current_voice_device)
            if index >= 0:
                self.voice_output_combo.setCurrentIndex(index)
        self.monitor_voice_check = QCheckBox()
        self.monitor_voice_check.setChecked(audio_engine.monitor_voice_chat_routes)
        self.volume_spin = QSpinBox()
        self.volume_spin.setRange(0, 100)
        self.volume_spin.setValue(audio_engine.global_volume)
        form.addRow("Default Output", self.output_combo)
        form.addRow("Voice Chat Output", self.voice_output_combo)
        form.addRow("Monitor Voice Routes", self.monitor_voice_check)
        form.addRow("Global Volume", self.volume_spin)
        layout.addLayout(form)

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
        self.output_combo.currentIndexChanged.connect(lambda _index: self._set_output_device())
        self.voice_output_combo.currentIndexChanged.connect(lambda _index: self._set_voice_output_device())
        self.monitor_voice_check.stateChanged.connect(lambda _state: self._set_monitor_voice_routes())
        self.volume_spin.valueChanged.connect(self._set_global_volume)
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh()

    def refresh(self) -> None:
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
