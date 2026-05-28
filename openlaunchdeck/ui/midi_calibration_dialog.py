from __future__ import annotations

from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout

from ..devices.device_calibration import CalibrationSession


class MidiCalibrationDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("MIDI Calibration")
        self.session = CalibrationSession()
        layout = QVBoxLayout(self)
        self.instruction_label = QLabel("Calibration is not running.")
        self.start_button = QPushButton("Start Calibration")
        self.save_button = QPushButton("Save Mapping")
        layout.addWidget(self.instruction_label)
        layout.addWidget(self.start_button)
        layout.addWidget(self.save_button)
        self.start_button.clicked.connect(self.start)

    def start(self) -> None:
        self.instruction_label.setText(self.session.start())

    def capture(self, message) -> None:
        if self.session.active:
            self.instruction_label.setText(self.session.capture(message))
