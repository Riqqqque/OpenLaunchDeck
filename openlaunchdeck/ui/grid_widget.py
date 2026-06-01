from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGridLayout, QWidget

from ..constants import BUTTON_COLUMNS, BUTTON_ROWS
from .button_cell import ButtonCell


class GridWidget(QWidget):
    button_clicked = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("LaunchpadGrid")
        self.cells: dict[str, ButtonCell] = {}
        self.selected_button_id = "A1"
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        for row_index, row in enumerate(BUTTON_ROWS):
            for col_index, column in enumerate(BUTTON_COLUMNS):
                button_id = f"{row}{column}"
                cell = ButtonCell(button_id)
                cell.clicked.connect(lambda bid=button_id: self.button_clicked.emit(bid))
                layout.addWidget(cell, row_index, col_index)
                self.cells[button_id] = cell

    def set_density(self, density: str) -> None:
        spacing = {"compact": 7, "comfortable": 10, "large": 12}.get(density, 10)
        if self.layout() is not None:
            self.layout().setSpacing(spacing)
        for cell in self.cells.values():
            cell.set_density(density)

    def select(self, button_id: str) -> str:
        previous = self.selected_button_id
        self.selected_button_id = button_id
        return previous

    def update_from_page(self, page, dangerous_service=None, audio_engine=None) -> None:
        self.update_buttons(page, self.cells.keys(), dangerous_service, audio_engine)

    def update_button(self, page, button_id: str, dangerous_service=None, audio_engine=None) -> None:
        cell = self.cells.get(button_id)
        if not cell:
            return
        button = page.get_button(button_id)
        armed = dangerous_service.is_armed(button_id) if dangerous_service else False
        playing = audio_engine.is_button_playing(button_id) if audio_engine else False
        cell.set_state(button, selected=button_id == self.selected_button_id, armed=armed, playing=playing)

    def update_buttons(self, page, button_ids, dangerous_service=None, audio_engine=None) -> None:
        for button_id in button_ids:
            cell = self.cells.get(button_id)
            if not cell:
                continue
            button = page.get_button(button_id)
            armed = dangerous_service.is_armed(button_id) if dangerous_service else False
            playing = audio_engine.is_button_playing(button_id) if audio_engine else False
            cell.set_state(button, selected=button_id == self.selected_button_id, armed=armed, playing=playing)
