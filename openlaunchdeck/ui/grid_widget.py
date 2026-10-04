from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QGridLayout, QWidget

from ..constants import BUTTON_COLUMNS, BUTTON_ROWS
from .button_cell import ButtonCell
from .theme import current_theme

# Hardware style: chassis padding and the strip for the round top/side buttons,
# both as a fraction of the pad size.
CHASSIS_PADDING = 0.24
CHASSIS_BUTTON_STRIP = 0.62


class GridWidget(QWidget):
    button_clicked = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("LaunchpadGrid")
        self.cells: dict[str, ButtonCell] = {}
        self.selected_button_id = "A1"
        self._density = "comfortable"
        self._spacing = 7
        self._chassis_visible = False
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(self._spacing)
        for row_index, row in enumerate(BUTTON_ROWS):
            for col_index, column in enumerate(BUTTON_COLUMNS):
                button_id = f"{row}{column}"
                cell = ButtonCell(button_id)
                cell.clicked.connect(lambda bid=button_id: self.button_clicked.emit(bid))
                layout.addWidget(cell, row_index, col_index)
                self.cells[button_id] = cell

    def set_density(self, density: str) -> None:
        spacing = {"mini": 4, "compact": 5, "comfortable": 7, "large": 8}.get(density, 7)
        self._density = density
        self._spacing = spacing
        if self.layout() is not None:
            self.layout().setSpacing(spacing)
        for cell in self.cells.values():
            cell.set_density(density)
        self.adjustSize()

    def fit_to_viewport(self, viewport_size: QSize) -> None:
        maximum = {
            "mini": QSize(112, 70),
            "compact": QSize(132, 82),
            "comfortable": QSize(152, 94),
            "large": QSize(176, 108),
        }.get(self._density, QSize(152, 94))
        pad_style = current_theme().pad_style
        chassis = pad_style.chassis
        # With the chassis, each axis also holds two paddings and one button strip.
        extra = (2 * CHASSIS_PADDING + CHASSIS_BUTTON_STRIP) if chassis else 0.0
        strip_gap = self._spacing if chassis else 0
        available_width = max(0, viewport_size.width() - 8 - self._spacing * 7 - strip_gap)
        available_height = max(0, viewport_size.height() - 8 - self._spacing * 7 - strip_gap)
        cell_height = min(maximum.height(), max(38, int(available_height / (8 + extra))))
        natural_width = max(48, int(available_width / (8 + extra)))
        aspect_limit = pad_style.aspect_limit or {"mini": 2.15, "compact": 2.0}.get(self._density, 1.75)
        cell_width = min(maximum.width(), natural_width, max(56, int(cell_height * aspect_limit)))
        for cell in self.cells.values():
            cell.set_cell_size(cell_width, cell_height)
        grid_width = cell_width * 8 + self._spacing * 7
        grid_height = cell_height * 8 + self._spacing * 7
        if chassis:
            pad = min(cell_width, cell_height)
            padding = max(10, int(pad * CHASSIS_PADDING))
            strip = max(16, int(pad * CHASSIS_BUTTON_STRIP)) + strip_gap
            total = QSize(grid_width + 2 * padding + strip, grid_height + 2 * padding + strip)
            # In very small windows the pads win; the chassis comes back when there is room.
            chassis = total.width() <= viewport_size.width() and total.height() <= viewport_size.height()
        self._chassis_visible = chassis
        if chassis:
            self.layout().setContentsMargins(padding, padding + strip, padding + strip, padding)
            self.setFixedSize(total)
        else:
            self.layout().setContentsMargins(0, 0, 0, 0)
            self.setFixedSize(grid_width, grid_height)
        self.update()

    def paintEvent(self, event) -> None:
        if not self._chassis_visible or not current_theme().pad_style.chassis:
            return super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        body = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        corner = min(body.width(), body.height()) * 0.045
        painter.setPen(QPen(QColor("#2a2e36"), 1.5))
        painter.setBrush(QColor("#15171c"))
        painter.drawRoundedRect(body, corner, corner)
        first = self.cells["A1"].geometry()
        margins = self.layout().contentsMargins()
        diameter = min(first.width(), first.height()) * 0.42
        top_center_y = margins.left() + (margins.top() - margins.left() - self._spacing) / 2
        right_center_x = self.width() - margins.left() - (margins.right() - margins.left() - self._spacing) / 2
        painter.setPen(QPen(QColor("#3a3e48"), 1))
        painter.setBrush(QColor("#23262d"))
        for column in BUTTON_COLUMNS:
            center_x = self.cells[f"A{column}"].geometry().center().x()
            painter.drawEllipse(QRectF(center_x - diameter / 2, top_center_y - diameter / 2, diameter, diameter))
        for row in BUTTON_ROWS:
            center_y = self.cells[f"{row}8"].geometry().center().y()
            painter.drawEllipse(QRectF(right_center_x - diameter / 2, center_y - diameter / 2, diameter, diameter))
        # The logo pad in the top-right corner, in the app's colors.
        logo = diameter * 0.9
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#ff5fa2"))
        painter.drawRoundedRect(
            QRectF(right_center_x - logo / 2, top_center_y - logo / 2, logo, logo), logo * 0.2, logo * 0.2
        )
        painter.end()

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
        playing = audio_engine.is_button_playing(button_id, page.id) if audio_engine else False
        cell.set_state(button, selected=button_id == self.selected_button_id, armed=armed, playing=playing)

    def update_buttons(self, page, button_ids, dangerous_service=None, audio_engine=None) -> None:
        playing_buttons = None
        if audio_engine is not None and hasattr(audio_engine, "playing_button_ids"):
            playing_buttons = audio_engine.playing_button_ids(page.id)
        for button_id in button_ids:
            cell = self.cells.get(button_id)
            if not cell:
                continue
            button = page.get_button(button_id)
            armed = dangerous_service.is_armed(button_id) if dangerous_service else False
            if playing_buttons is not None:
                playing = button_id in playing_buttons
            else:
                playing = audio_engine.is_button_playing(button_id) if audio_engine else False
            cell.set_state(button, selected=button_id == self.selected_button_id, armed=armed, playing=playing)
