from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QPlainTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..devices.device_calibration import CalibrationSession
from ..devices.midi_manager import MidiManager
from ..devices.midi_mapping import MidiMapping, message_to_raw_data


class MidiDebugWindow(QWidget):
    def __init__(self, device, parent=None) -> None:
        super().__init__(parent)
        self.device = device
        self.calibration = CalibrationSession()
        self.setWindowTitle("MIDI Debug")
        self.resize(760, 520)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.input_combo = QComboBox()
        self.output_combo = QComboBox()
        form.addRow("Input Port", self.input_combo)
        form.addRow("Output Port", self.output_combo)
        layout.addLayout(form)

        self.last_label = QLabel("Last message: none")
        self.parsed_label = QLabel("Parsed button: none")
        self.calibration_label = QLabel("Calibration: idle")
        layout.addWidget(self.last_label)
        layout.addWidget(self.parsed_label)
        layout.addWidget(self.calibration_label)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

        self.mapping_table = QTableWidget(0, 4)
        self.mapping_table.setHorizontalHeaderLabels(["Button", "Type", "Number", "Channel"])
        self.mapping_table.setMinimumHeight(170)
        layout.addWidget(self.mapping_table)

        buttons = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh Ports")
        self.clear_button = QPushButton("Clear Log")
        self.save_button = QPushButton("Save Log")
        self.start_calibration_button = QPushButton("Start Calibration")
        self.save_mapping_button = QPushButton("Save Mapping")
        self.restore_default_button = QPushButton("Restore Default Mapping")
        self.clear_pads_button = QPushButton("Clear Pads")
        for button in (
            self.refresh_button,
            self.clear_button,
            self.save_button,
            self.start_calibration_button,
            self.save_mapping_button,
            self.restore_default_button,
            self.clear_pads_button,
        ):
            buttons.addWidget(button)
        layout.addLayout(buttons)
        self.refresh_button.clicked.connect(self.refresh_ports)
        self.clear_button.clicked.connect(self.log.clear)
        self.save_button.clicked.connect(self.save_log)
        self.start_calibration_button.clicked.connect(self.start_calibration)
        self.save_mapping_button.clicked.connect(self.save_mapping)
        self.restore_default_button.clicked.connect(self.restore_default_mapping)
        self.clear_pads_button.clicked.connect(self.device.clear_all_pads)
        self.refresh_ports()
        self.refresh_mapping_table()

    def refresh_ports(self) -> None:
        current_input = self.input_combo.currentText()
        current_output = self.output_combo.currentText()
        self.input_combo.clear()
        self.output_combo.clear()
        self.input_combo.addItems(MidiManager.available_input_ports())
        self.output_combo.addItems(MidiManager.available_output_ports())
        if current_input:
            index = self.input_combo.findText(current_input)
            if index >= 0:
                self.input_combo.setCurrentIndex(index)
        if current_output:
            index = self.output_combo.findText(current_output)
            if index >= 0:
                self.output_combo.setCurrentIndex(index)

    def refresh_mapping_table(self) -> None:
        rows = self.device.mapping.verification_table()
        self.mapping_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            self.mapping_table.setItem(row_index, 0, QTableWidgetItem(str(row["button_id"])))
            self.mapping_table.setItem(row_index, 1, QTableWidgetItem(str(row["message_type"])))
            self.mapping_table.setItem(row_index, 2, QTableWidgetItem(str(row["number"])))
            self.mapping_table.setItem(row_index, 3, QTableWidgetItem(str(row["channel"])))
        self.mapping_table.resizeColumnsToContents()

    def append_incoming(self, message, text: str) -> None:
        parsed = self.device.mapping.parse_message(message)
        raw_data = message_to_raw_data(message)
        self.last_label.setText(f"Last message: {text}")
        self.parsed_label.setText(f"Parsed button: {parsed.button_id if parsed else 'none'}")
        self.log.appendPlainText(f"IN  {text} data={raw_data}")
        if self.calibration.active:
            instruction = self.calibration.capture(message)
            self.calibration_label.setText(instruction)
            if self.calibration.raw_messages:
                self.log.appendPlainText(f"CAL {self.calibration.raw_log_lines()[-1]}")

    def append_outgoing(self, message, text: str) -> None:
        self.log.appendPlainText(f"OUT {text} data={message_to_raw_data(message)}")

    def start_calibration(self) -> None:
        self.calibration_label.setText(self.calibration.start())
        self.log.appendPlainText("Calibration started. Press each requested pad once.")

    def save_mapping(self) -> None:
        if self.calibration.active:
            self.calibration_label.setText("Finish calibration before saving.")
            return
        if len(self.calibration.captured) != len(self.calibration.expected_buttons):
            self.calibration_label.setText("Run full calibration before saving.")
            return
        if self.calibration.captured:
            mapping = self.calibration.to_mapping()
            mapping.save_user_default()
            self.device.mapping = mapping
            self.calibration_label.setText("Calibration saved.")
            self.log.appendPlainText("Calibration mapping saved.")
            self.refresh_mapping_table()

    def restore_default_mapping(self) -> None:
        self.device.mapping = MidiMapping.restore_user_default()
        self.calibration_label.setText("Default mapping restored.")
        self.log.appendPlainText("Default Programmer Mode mapping restored.")
        self.refresh_mapping_table()

    def save_log(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save MIDI Log", str(Path.home() / "openlaunchdeck-midi-log.txt"))
        if path:
            Path(path).write_text(self.log.toPlainText(), encoding="utf-8")
