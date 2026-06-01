from __future__ import annotations

from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from ..constants import NAMED_COLORS
from ..models.button import ButtonConfig


CELL_SIZES = {
    "mini": QSize(74, 66),
    "compact": QSize(84, 74),
    "comfortable": QSize(102, 88),
    "large": QSize(118, 102),
}

ACTION_LABELS = {
    "noop": "No Action",
    "open_url": "URL",
    "open_path": "Path",
    "run_command": "Command",
    "powershell": "PS",
    "hotkey": "Hotkey",
    "type_text": "Type",
    "media_control": "Media",
    "volume_control": "Volume",
    "http_request": "HTTP",
    "play_sound": "Sound",
    "stop_sound": "Stop",
    "multi_action": "Multi",
    "delay": "Delay",
    "switch_page": "Page",
    "ssh_command": "SSH",
    "obs_websocket": "OBS",
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
        rect = self.rect().adjusted(3, 3, -3, -3)
        button = self._button
        action_type = button.action.type if button.action else "noop"
        label = button.label or "Empty"
        color_name = button.active_color if self._playing else button.color
        if self._armed:
            color_name = "yellow"
        if not button.enabled:
            color_name = "off"

        accent = QColor(NAMED_COLORS.get(color_name, color_name if color_name.startswith("#") else NAMED_COLORS["dim"]))
        base = QColor("#111a25")
        if button.enabled:
            base = self._blend(base, accent, 0.075 if not self._hover else 0.13)
        else:
            base = QColor("#101722")
        if self._pressed:
            base = self._blend(base, accent, 0.18)

        border = QColor("#2f3d52")
        if self._selected:
            border = QColor("#9be7ff")
        elif self._armed:
            border = QColor("#facc15")
        elif self._playing:
            border = QColor("#38bdf8")
        elif self._hover:
            border = self._blend(QColor("#64748b"), accent, 0.35)

        painter.setPen(QPen(border, 2.2 if self._selected else 1.4))
        painter.setBrush(base)
        painter.drawRoundedRect(rect, 9, 9)

        strip = QRect(rect.left() + 9, rect.top() + 8, max(18, rect.width() - 18), 5)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(accent if button.enabled else QColor("#273244"))
        painter.drawRoundedRect(strip, 3, 3)

        painter.setPen(QColor("#dbeafe") if button.enabled else QColor("#64748b"))
        id_font = QFont("Segoe UI", 6 if self._density == "mini" else 7 if self._density == "compact" else 8, QFont.Weight.DemiBold)
        painter.setFont(id_font)
        painter.drawText(rect.adjusted(11, 14, -10, -10), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, button.id)

        badge = self._badge_text(button.enabled)
        if badge:
            self._draw_badge(painter, rect, badge)

        title_font = QFont("Segoe UI", 7 if self._density == "mini" else 8 if self._density == "compact" else 9 if self._density == "comfortable" else 10, QFont.Weight.Bold)
        title_font.setStretch(94)
        painter.setFont(title_font)
        title_color = QColor("#f8fafc") if button.enabled else QColor("#94a3b8")
        painter.setPen(title_color)
        title_top = {"mini": 25, "compact": 27, "comfortable": 28, "large": 30}.get(self._density, 28)
        title_bottom_padding = {"mini": 22, "compact": 25, "comfortable": 31, "large": 35}.get(self._density, 31)
        title_rect = rect.adjusted(7, title_top, -7, -title_bottom_padding)
        self._draw_fitted_center(painter, title_rect, label, minimum_size=6 if self._density == "mini" else 7)

        action_label = ACTION_LABELS.get(action_type, action_type.replace("_", " ").title())
        action_font = QFont("Segoe UI", 5 if self._density == "mini" else 6 if self._density == "compact" else 7, QFont.Weight.DemiBold)
        painter.setFont(action_font)
        action_font, metrics = self._fit_font(action_font, action_label, max(18, rect.width() - 20), minimum_size=5 if self._density == "mini" else 6)
        painter.setFont(action_font)
        action_text = metrics.elidedText(action_label, Qt.TextElideMode.ElideRight, max(18, rect.width() - 20))
        pill_height = 11 if self._density == "mini" else 12 if self._density == "compact" else 13 if self._density == "comfortable" else 14
        pill_bottom_margin = 4 if self._density == "compact" else 5
        pill = QRect(rect.left() + 8, rect.bottom() - pill_height - pill_bottom_margin, rect.width() - 16, pill_height)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(7, 12, 20, 190))
        painter.drawRoundedRect(pill, 7, 7)
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

    def _draw_fitted_center(self, painter: QPainter, rect: QRect, text: str, minimum_size: int) -> None:
        base_font = QFont(painter.font())
        text = self._humanize_compact_label(text.strip())
        words = text.split()
        if len(words) > 1:
            midpoint = (len(words) + 1) // 2
            lines = [" ".join(words[:midpoint]), " ".join(words[midpoint:])]
        else:
            lines = [text]

        fitted: list[tuple[str, QFont, QFontMetrics]] = []
        for line in lines:
            font, metrics = self._fit_font(base_font, line, rect.width(), minimum_size)
            fitted.append((line, font, metrics))

        line_gap = 1 if self._density == "compact" else 2
        total_height = sum(metrics.height() for _, _, metrics in fitted) + max(0, len(fitted) - 1) * line_gap
        while total_height > rect.height() and any(font.pointSize() > minimum_size for _, font, _ in fitted):
            updated: list[tuple[str, QFont, QFontMetrics]] = []
            for line, font, _ in fitted:
                next_font = QFont(font)
                if next_font.pointSize() > minimum_size:
                    next_font.setPointSize(next_font.pointSize() - 1)
                updated.append((line, next_font, QFontMetrics(next_font)))
            fitted = updated
            total_height = sum(metrics.height() for _, _, metrics in fitted) + max(0, len(fitted) - 1) * line_gap

        y = rect.center().y() - total_height // 2
        for index, (line, font, metrics) in enumerate(fitted):
            painter.setFont(font)
            elided = metrics.elidedText(line, Qt.TextElideMode.ElideRight, rect.width())
            line_rect = QRect(rect.left(), y, rect.width(), metrics.height())
            painter.drawText(line_rect, Qt.AlignmentFlag.AlignCenter, elided)
            y += metrics.height() + (line_gap if index < len(fitted) - 1 else 0)

    @staticmethod
    def _fit_font(base_font: QFont, text: str, width: int, minimum_size: int) -> tuple[QFont, QFontMetrics]:
        font = QFont(base_font)
        metrics = QFontMetrics(font)
        while metrics.horizontalAdvance(text) > width and font.pointSize() > minimum_size:
            font.setPointSize(font.pointSize() - 1)
            metrics = QFontMetrics(font)
        return font, metrics

    @staticmethod
    def _humanize_compact_label(text: str) -> str:
        if " " in text or "/" in text:
            return text
        parts: list[str] = []
        start = 0
        for index in range(1, len(text)):
            if text[index].isupper() and text[index - 1].islower():
                parts.append(text[start:index])
                start = index
        if not parts:
            return text
        parts.append(text[start:])
        return " ".join(parts)

    @staticmethod
    def _blend(base: QColor, accent: QColor, amount: float) -> QColor:
        amount = max(0.0, min(1.0, amount))
        return QColor(
            int(base.red() * (1 - amount) + accent.red() * amount),
            int(base.green() * (1 - amount) + accent.green() * amount),
            int(base.blue() * (1 - amount) + accent.blue() * amount),
        )
