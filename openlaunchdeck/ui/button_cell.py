from __future__ import annotations

from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from ..constants import NAMED_COLORS
from ..models.button import ButtonConfig


CELL_SIZES = {
    "compact": QSize(76, 66),
    "comfortable": QSize(92, 78),
    "large": QSize(108, 92),
}


class ButtonCell(QWidget):
    clicked = Signal()

    def __init__(self, button_id: str) -> None:
        super().__init__()
        self.button_id = button_id
        self._density = "comfortable"
        self.setMinimumSize(CELL_SIZES[self._density])
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setToolTip(button_id)
        self._button = ButtonConfig.blank(button_id)
        self._selected = False
        self._armed = False
        self._playing = False
        self._hover = False
        self._pressed = False
        self._state_key: tuple | None = None
        self._text = f"{button_id}\nEmpty\nnoop"

    def set_state(self, button: ButtonConfig, selected: bool = False, armed: bool = False, playing: bool = False) -> None:
        action_type = button.action.type if button.action else "noop"
        label = button.label or "Empty"
        color = button.active_color if playing else button.color
        if armed:
            color = "yellow"
        if not button.enabled:
            color = "off"
        state_key = (
            button.id,
            label,
            action_type,
            button.enabled,
            color,
            selected,
            armed,
            playing,
        )
        if state_key == self._state_key:
            return
        self._button = button
        self._state_key = state_key
        self._selected = selected
        self._armed = armed
        self._playing = playing
        self._text = f"{button.id}\n{label}\n{action_type}"
        self.setEnabled(True)
        self.update()

    def set_density(self, density: str) -> None:
        if density not in CELL_SIZES:
            density = "comfortable"
        self._density = density
        self.setMinimumSize(CELL_SIZES[density])
        self.updateGeometry()
        self.update()

    def sizeHint(self) -> QSize:
        return CELL_SIZES.get(self._density, CELL_SIZES["comfortable"])

    def text(self) -> str:
        return self._text

    def enterEvent(self, event) -> None:
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover = False
        self._pressed = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            self.update()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            was_pressed = self._pressed
            self._pressed = False
            self.update()
            if was_pressed and self.rect().contains(event.position().toPoint()):
                self.clicked.emit()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.clicked.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(2, 2, -2, -2)
        button = self._button
        action_type = button.action.type if button.action else "noop"
        label = button.label or "Empty"
        color_name = button.active_color if self._playing else button.color
        if self._armed:
            color_name = "yellow"
        if not button.enabled:
            color_name = "off"

        accent = QColor(NAMED_COLORS.get(color_name, color_name if color_name.startswith("#") else NAMED_COLORS["dim"]))
        base = QColor("#171d27")
        if button.enabled:
            base = self._blend(base, accent, 0.18 if not self._hover else 0.26)
        else:
            base = QColor("#111722")
        if self._pressed:
            base = self._blend(base, QColor("#ffffff"), 0.08)

        border = QColor("#334155")
        if self._selected:
            border = QColor("#e5f4ff")
        elif self._armed:
            border = QColor("#facc15")
        elif self._playing:
            border = QColor("#38bdf8")
        elif self._hover:
            border = QColor("#64748b")

        painter.setPen(QPen(border, 2 if self._selected else 1.5))
        painter.setBrush(base)
        painter.drawRoundedRect(rect, 8, 8)

        strip = QRect(rect.left() + 8, rect.top() + 7, max(18, rect.width() - 16), 4)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(accent if button.enabled else QColor("#273244"))
        painter.drawRoundedRect(strip, 2, 2)

        painter.setPen(QColor("#dbeafe") if button.enabled else QColor("#64748b"))
        id_font = QFont("Segoe UI", 8, QFont.Weight.DemiBold)
        painter.setFont(id_font)
        painter.drawText(rect.adjusted(10, 12, -10, -10), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, button.id)

        badge = self._badge_text(button.enabled)
        if badge:
            self._draw_badge(painter, rect, badge)

        title_font = QFont("Segoe UI", 10 if self._density != "large" else 11, QFont.Weight.Bold)
        painter.setFont(title_font)
        title_color = QColor("#f8fafc") if button.enabled else QColor("#94a3b8")
        if color_name in {"white", "yellow"} and button.enabled:
            title_color = QColor("#0f172a")
        painter.setPen(title_color)
        title_rect = rect.adjusted(9, 27, -9, -22)
        self._draw_elided_center(painter, title_rect, label)

        action_label = action_type.replace("_", " ").title()
        action_font = QFont("Segoe UI", 7 if self._density == "compact" else 8, QFont.Weight.DemiBold)
        painter.setFont(action_font)
        metrics = QFontMetrics(action_font)
        action_text = metrics.elidedText(action_label, Qt.TextElideMode.ElideRight, max(18, rect.width() - 20))
        pill = QRect(rect.left() + 8, rect.bottom() - 19, rect.width() - 16, 13)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(8, 13, 20, 168))
        painter.drawRoundedRect(pill, 6, 6)
        painter.setPen(QColor("#cbd5e1") if button.enabled else QColor("#64748b"))
        painter.drawText(pill, Qt.AlignmentFlag.AlignCenter, action_text)

    def _badge_text(self, enabled: bool) -> str:
        if self._armed:
            return "ARM"
        if self._playing:
            return "PLAY"
        if not enabled:
            return "OFF"
        return ""

    def _draw_badge(self, painter: QPainter, rect: QRect, text: str) -> None:
        font = QFont("Segoe UI", 7, QFont.Weight.Bold)
        painter.setFont(font)
        metrics = QFontMetrics(font)
        width = metrics.horizontalAdvance(text) + 10
        badge_rect = QRect(rect.right() - width - 8, rect.top() + 10, width, 15)
        color = QColor("#facc15") if text == "ARM" else QColor("#38bdf8") if text == "PLAY" else QColor("#334155")
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawRoundedRect(badge_rect, 6, 6)
        painter.setPen(QColor("#111827") if text != "OFF" else QColor("#cbd5e1"))
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, text)

    def _draw_elided_center(self, painter: QPainter, rect: QRect, text: str) -> None:
        metrics = QFontMetrics(painter.font())
        words = text.split()
        if len(words) > 1:
            midpoint = (len(words) + 1) // 2
            lines = [" ".join(words[:midpoint]), " ".join(words[midpoint:])]
        else:
            lines = [text]
        line_height = metrics.height()
        total_height = line_height * len(lines)
        y = rect.center().y() - total_height // 2
        for line in lines:
            elided = metrics.elidedText(line, Qt.TextElideMode.ElideRight, rect.width())
            line_rect = QRect(rect.left(), y, rect.width(), line_height)
            painter.drawText(line_rect, Qt.AlignmentFlag.AlignCenter, elided)
            y += line_height

    @staticmethod
    def _blend(base: QColor, accent: QColor, amount: float) -> QColor:
        amount = max(0.0, min(1.0, amount))
        return QColor(
            int(base.red() * (1 - amount) + accent.red() * amount),
            int(base.green() * (1 - amount) + accent.green() * amount),
            int(base.blue() * (1 - amount) + accent.blue() * amount),
        )
