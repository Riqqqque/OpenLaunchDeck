from __future__ import annotations

from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPalette, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from ..constants import NAMED_COLORS
from ..models.button import ButtonConfig


CELL_SIZES = {
    "mini": QSize(88, 58),
    "compact": QSize(108, 70),
    "comfortable": QSize(128, 82),
    "large": QSize(148, 96),
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
    "navigate_deck": "Navigate",
    "switch_profile": "Profile",
    "clipboard": "Clipboard",
    "window_control": "Window",
    "mouse_control": "Mouse",
    "random_sound": "Random Sound",
}


class ButtonCell(QWidget):
    clicked = Signal()

    def __init__(self, button_id: str) -> None:
        super().__init__()
        self.button_id = button_id
        self._density = "comfortable"
        self._cell_size = CELL_SIZES[self._density]
        self.setFixedSize(self._cell_size)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
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
        action_label = ACTION_LABELS.get(action_type, action_type.replace("_", " ").title())
        state = "Playing" if playing else "Armed" if armed else "Disabled" if not button.enabled else "Ready"
        self.setToolTip(f"{button.id} - {label}\n{action_label}\n{state}")
        self.setEnabled(True)
        self.update()

    def set_density(self, density: str) -> None:
        if density not in CELL_SIZES:
            density = "comfortable"
        self._density = density
        size = CELL_SIZES[density]
        self.set_cell_size(size.width(), size.height())
        self.updateGeometry()
        self.update()

    def set_cell_size(self, width: int, height: int) -> None:
        size = QSize(max(48, int(width)), max(38, int(height)))
        if size == self._cell_size:
            return
        self._cell_size = size
        self.setFixedSize(size)
        self.updateGeometry()
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(self._cell_size)

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
            hit_rect = self.rect().adjusted(-8, -8, 8, 8)
            if was_pressed and hit_rect.contains(event.position().toPoint()):
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
        height = self._cell_size.height()
        width = self._cell_size.width()
        rect = self.rect().adjusted(1, 1, -1, -2)
        button = self._button
        action_type = button.action.type if button.action else "noop"
        label = button.label or "Empty"
        color_name = button.active_color if self._playing else button.color
        if self._armed:
            color_name = "yellow"
        if not button.enabled:
            color_name = "off"

        accent = QColor(NAMED_COLORS.get(color_name, color_name if color_name.startswith("#") else NAMED_COLORS["dim"]))
        palette = self.palette()
        base = palette.color(QPalette.ColorRole.Base)
        if button.enabled:
            base = self._blend(base, accent, 0.13 if not self._hover else 0.2)
        else:
            base = palette.color(QPalette.ColorRole.Window)
        if self._pressed:
            base = self._blend(base, accent, 0.3)

        border = self._blend(palette.color(QPalette.ColorRole.Mid), accent, 0.48 if button.enabled else 0.05)
        if self._selected:
            border = palette.color(QPalette.ColorRole.Highlight)
        elif self._armed:
            border = QColor("#facc15")
        elif self._playing:
            border = QColor("#67e8f9")
        elif self._hover:
            border = self._blend(palette.color(QPalette.ColorRole.Light), accent, 0.28)

        painter.setPen(QPen(border, 2.5 if self._selected else 1.25))
        painter.setBrush(base)
        radius = 8 if height >= 58 else 6
        painter.drawRoundedRect(rect, radius, radius)

        strip_margin = 8 if width < 84 else 11
        strip_height = 3 if height < 58 else 4
        strip = QRect(
            rect.left() + strip_margin,
            rect.top(),
            max(14, rect.width() - strip_margin * 2),
            strip_height,
        )
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(accent if button.enabled else QColor("#273244"))
        painter.drawRoundedRect(strip, 3, 3)

        painter.setPen(palette.color(QPalette.ColorRole.Text) if button.enabled else palette.color(QPalette.ColorRole.PlaceholderText))
        id_font = QFont(painter.font())
        id_font.setPointSize(7 if height < 56 else 8 if height < 82 else 9)
        id_font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(id_font)
        id_left = 8 if width < 82 else 11
        id_top = 7 if height < 58 else 9
        painter.drawText(
            rect.adjusted(id_left, id_top, -6, -6),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
            button.id,
        )

        badge = self._badge_text(button.enabled)
        if badge:
            self._draw_badge(painter, rect, badge)

        density_boost = {"mini": 1, "compact": 1, "comfortable": 1, "large": 2}.get(self._density, 1)
        if height < 48:
            title_size = 8
        elif height < 60:
            title_size = 9
        elif height < 76:
            title_size = 10
        elif height < 92:
            title_size = 11
        else:
            title_size = 12
        title_size += density_boost
        title_font = QFont(painter.font())
        title_font.setPointSize(title_size)
        title_font.setWeight(QFont.Weight.Bold)
        title_font.setStretch(94)
        painter.setFont(title_font)
        title_color = palette.color(QPalette.ColorRole.BrightText) if button.enabled else palette.color(QPalette.ColorRole.PlaceholderText)
        painter.setPen(title_color)
        title_top = 17 if height < 54 else 20 if height < 72 else 23
        action_height = 13 if height < 70 else 15 if height < 90 else 17
        action_bottom_margin = 4 if height < 64 else 6
        show_action = height >= 52 and width >= 70
        title_bottom_padding = action_height + action_bottom_margin + 4 if show_action else 6
        horizontal_padding = 6 if width < 84 else 9
        title_rect = rect.adjusted(horizontal_padding, title_top, -horizontal_padding, -title_bottom_padding)
        self._draw_fitted_center(
            painter,
            title_rect,
            label,
            minimum_size=7 if self._density in {"mini", "compact"} else 8,
        )

        if not show_action:
            return
        action_label = ACTION_LABELS.get(action_type, action_type.replace("_", " ").title())
        action_font = QFont(painter.font())
        action_font.setPointSize(8 if height < 92 else 9)
        action_font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(action_font)
        action_font, metrics = self._fit_font(action_font, action_label, max(18, rect.width() - 20), minimum_size=6)
        painter.setFont(action_font)
        action_text = metrics.elidedText(action_label, Qt.TextElideMode.ElideRight, max(18, rect.width() - 20))
        action_rect = QRect(
            rect.left() + 7,
            rect.bottom() - action_height - action_bottom_margin,
            rect.width() - 14,
            action_height,
        )
        action_color = palette.color(QPalette.ColorRole.Text if button.enabled else QPalette.ColorRole.PlaceholderText)
        action_color.setAlpha(185 if button.enabled else 150)
        painter.setPen(action_color)
        painter.drawText(action_rect, Qt.AlignmentFlag.AlignCenter, action_text)

    def _badge_text(self, enabled: bool) -> str:
        if self._armed:
            return "ARM"
        if self._playing:
            return "PLAY"
        if not enabled:
            return "OFF"
        return ""

    def _draw_badge(self, painter: QPainter, rect: QRect, text: str) -> None:
        if self._cell_size.height() < 54 or self._cell_size.width() < 78:
            return
        font = QFont(painter.font())
        font.setPointSize(7)
        font.setWeight(QFont.Weight.Bold)
        painter.setFont(font)
        metrics = QFontMetrics(font)
        width = metrics.horizontalAdvance(text) + 10
        badge_rect = QRect(rect.right() - width - 8, rect.top() + 7, width, 15)
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
        if self._cell_size.height() < 52:
            lines = [text]
        elif len(words) > 1:
            midpoint = (len(words) + 1) // 2
            lines = [" ".join(words[:midpoint]), " ".join(words[midpoint:])]
        else:
            lines = [text]

        fitted: list[tuple[str, QFont, QFontMetrics]] = []
        for line in lines:
            font, metrics = self._fit_font(base_font, line, rect.width(), minimum_size)
            fitted.append((line, font, metrics))

        line_gap = 1 if self._cell_size.height() < 76 else 2
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
