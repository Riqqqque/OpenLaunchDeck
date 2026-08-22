from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..devices.device_calibration import CalibrationSession
from ..devices.midi_manager import MidiManager
from ..devices.midi_mapping import (
    MidiMapping,
    auxiliary_verification_table,
    message_to_raw_data,
    parse_auxiliary_message,
)


class MidiDebugWindow(QWidget):
    closed = Signal()

    def __init__(self, device, parent=None) -> None:
        super().__init__(parent)
        self.device = device
        self.calibration = CalibrationSession()
        self.setWindowTitle("MIDI Debug")
        self.resize(860, 640)
        self.setMinimumSize(680, 500)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.input_combo = QComboBox()
        self.output_combo = QComboBox()
        self.input_combo.setToolTip("Detected MIDI inputs. Save a manual choice under Settings > Launchpad.")
        self.output_combo.setToolTip("Detected MIDI outputs. Save a manual choice under Settings > Launchpad.")
        form.addRow("Input Port", self.input_combo)
        form.addRow("Output Port", self.output_combo)
        layout.addLayout(form)

        self.last_label = QLabel("Last message: none")
        self.last_label.setWordWrap(True)
        self.parsed_label = QLabel("Parsed button: none")
        self.parsed_control_label = QLabel("Parsed hardware control: none")
        self.calibration_label = QLabel("Calibration: idle")

        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        live_tab = QWidget()
        live_layout = QVBoxLayout(live_tab)
        live_layout.setContentsMargins(10, 10, 10, 10)
        live_layout.addWidget(self.last_label)
        parsed_row = QHBoxLayout()
        parsed_row.addWidget(self.parsed_label)
        parsed_row.addWidget(self.parsed_control_label)
        parsed_row.addStretch(1)
        live_layout.addLayout(parsed_row)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.document().setMaximumBlockCount(2000)
        live_layout.addWidget(self.log, 1)
        tabs.addTab(live_tab, "Live Messages")

        mapping_tab = QWidget()
        mapping_layout = QVBoxLayout(mapping_tab)
        mapping_layout.setContentsMargins(10, 10, 10, 10)
        mapping_layout.addWidget(self.calibration_label)
        self.mapping_table = QTableWidget(0, 4)
        self.mapping_table.setHorizontalHeaderLabels(["Button", "Type", "Number", "Channel"])
        self.mapping_table.setAlternatingRowColors(True)
        self.mapping_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        mapping_layout.addWidget(self.mapping_table, 1)
        tabs.addTab(mapping_tab, "Pad Mapping")

        controls_tab = QWidget()
        controls_layout = QVBoxLayout(controls_tab)
        controls_layout.setContentsMargins(10, 10, 10, 10)
        controls_note = QLabel("Programmer Mode hardware controls use fixed CC messages. Assign their behavior in Settings > Launchpad.")
        controls_note.setWordWrap(True)
        controls_note.setObjectName("MutedText")
        controls_layout.addWidget(controls_note)
        self.controls_table = QTableWidget(0, 5)
        self.controls_table.setHorizontalHeaderLabels(["Control", "Name", "Type", "Number", "Channel"])
        self.controls_table.setAlternatingRowColors(True)
        self.controls_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        controls_layout.addWidget(self.controls_table, 1)
        tabs.addTab(controls_tab, "Hardware Controls")
        layout.addWidget(tabs, 1)

        buttons = QGridLayout()
        buttons.setHorizontalSpacing(8)
        buttons.setVerticalSpacing(8)
        self.refresh_button = QPushButton("Refresh Ports")
        self.clear_button = QPushButton("Clear Log")
        self.save_button = QPushButton("Save Log")
        self.start_calibration_button = QPushButton("Start Calibration")
        self.save_mapping_button = QPushButton("Save Mapping")
        self.restore_default_button = QPushButton("Restore Default Mapping")
        self.clear_pads_button = QPushButton("Clear Lights")
        button_list = (
            self.refresh_button,
            self.clear_button,
            self.save_button,
            self.clear_pads_button,
            self.start_calibration_button,
            self.save_mapping_button,
            self.restore_default_button,
        )
        for index, button in enumerate(button_list):
            button.setObjectName("PrimaryButton" if button is self.start_calibration_button else "SecondaryButton")
            buttons.addWidget(button, index // 4, index % 4)
        layout.addLayout(buttons)
        self.refresh_button.clicked.connect(self.refresh_ports)
        self.clear_button.clicked.connect(self.log.clear)
        self.save_button.clicked.connect(self.save_log)
        self.start_calibration_button.clicked.connect(self.start_calibration)
        self.save_mapping_button.clicked.connect(self.save_mapping)
        self.restore_default_button.clicked.connect(self.restore_default_mapping)
        self.clear_pads_button.clicked.connect(self.device.clear_surface)
        self.refresh_ports()
        self.refresh_mapping_table()
        self.refresh_controls_table()

    def refresh_ports(self) -> None:
        inputs = MidiManager.available_input_ports()
        outputs = MidiManager.available_output_ports()
        detected_input, detected_output = MidiManager.detect_launchpad_ports(inputs, outputs)
        current_input = self.device.input_port_name or self.input_combo.currentText() or detected_input
        current_output = self.device.output_port_name or self.output_combo.currentText() or detected_output
        self.input_combo.clear()
        self.output_combo.clear()
        self.input_combo.addItems(inputs)
        self.output_combo.addItems(outputs)
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

    def refresh_controls_table(self) -> None:
        rows = auxiliary_verification_table()
        self.controls_table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            self.controls_table.setItem(row_index, 0, QTableWidgetItem(str(row["control_id"])))
            self.controls_table.setItem(row_index, 1, QTableWidgetItem(str(row["label"])))
            self.controls_table.setItem(row_index, 2, QTableWidgetItem(str(row["message_type"])))
            self.controls_table.setItem(row_index, 3, QTableWidgetItem(str(row["number"])))
            self.controls_table.setItem(row_index, 4, QTableWidgetItem(str(row["channel"])))

    def append_incoming(self, message, text: str) -> None:
        parsed = self.device.mapping.parse_message(message)
        parsed_control = None if parsed else parse_auxiliary_message(message)
        raw_data = message_to_raw_data(message)
        self.last_label.setText(f"Last message: {text}")
        self.parsed_label.setText(f"Parsed button: {parsed.button_id if parsed else 'none'}")
        self.parsed_control_label.setText(
            f"Parsed hardware control: {parsed_control.control_id if parsed_control else 'none'}"
        )
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

    def closeEvent(self, event) -> None:
        self.closed.emit()
        super().closeEvent(event)
