from __future__ import annotations

from PySide6.QtCore import QPointF, QRect, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPalette, QPen, QRadialGradient
from PySide6.QtWidgets import QSizePolicy, QWidget

from ..constants import NAMED_COLORS
from ..models.button import ButtonConfig
from .theme import current_theme

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
        style = current_theme().pad_style.key
        if style in {"nebula", "studio", "hardware"}:
            getattr(self, f"_paint_{style}")(painter)
            return
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

        density_boost = {"mini": 1, "compact": 1, "comfortable": 2, "large": 3}.get(self._density, 1)
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

    # Styled pads (Nebula, Studio, Hardware)

    def _pad_state(self) -> tuple[ButtonConfig, str, bool, QColor]:
        button = self._button
        action_type = button.action.type if button.action else "noop"
        color_name = button.active_color if self._playing else button.color
        if self._armed:
            color_name = "yellow"
        empty = action_type == "noop" and not button.label
        accent = QColor(NAMED_COLORS.get(color_name, color_name if color_name.startswith("#") else NAMED_COLORS["dim"]))
        if color_name in {"dim", "off"}:
            accent = QColor(NAMED_COLORS["blue"])
        return button, action_type, empty, accent

    def _title_point_size(self) -> int:
        height = self._cell_size.height()
        base = 8 if height < 48 else 9 if height < 60 else 10 if height < 76 else 11 if height < 92 else 12
        return base + {"mini": 1, "compact": 1, "comfortable": 2, "large": 3}.get(self._density, 1)

    def _small_font(self, painter: QPainter, bold: bool = True) -> QFont:
        font = QFont(painter.font())
        height = self._cell_size.height()
        font.setPointSize(7 if height < 56 else 8 if height < 92 else 9)
        font.setWeight(QFont.Weight.DemiBold if bold else QFont.Weight.Normal)
        return font

    def _draw_label(self, painter: QPainter, rect: QRect, text: str, color: QColor) -> None:
        font = QFont(painter.font())
        font.setPointSize(self._title_point_size())
        font.setWeight(QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(color)
        self._draw_fitted_center(painter, rect, text, minimum_size=7 if self._density in {"mini", "compact"} else 8)

    def _draw_action_caption(self, painter: QPainter, rect: QRect, action_type: str, color: QColor, align) -> None:
        label = ACTION_LABELS.get(action_type, action_type.replace("_", " ").title())
        font, metrics = self._fit_font(self._small_font(painter), label, max(18, rect.width()), minimum_size=6)
        painter.setFont(font)
        painter.setPen(color)
        painter.drawText(rect, align, metrics.elidedText(label, Qt.TextElideMode.ElideRight, max(18, rect.width())))

    @staticmethod
    def _with_alpha(color: QColor, alpha: int) -> QColor:
        result = QColor(color)
        result.setAlpha(alpha)
        return result

    @staticmethod
    def _readable_on(fill: QColor) -> QColor:
        luminance = 0.2126 * fill.redF() + 0.7152 * fill.greenF() + 0.0722 * fill.blueF()
        return QColor("#0b0b10") if luminance > 0.55 else QColor("#ffffff")

    def _paint_nebula(self, painter: QPainter) -> None:
        tokens = current_theme().colors
        button, action_type, empty, accent = self._pad_state()
        width, height = self._cell_size.width(), self._cell_size.height()
        rect = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        radius = min(rect.width(), rect.height()) * 0.2
        panel = QColor(tokens["PANEL"])
        if not button.enabled:
            fill, edge = QColor(tokens["SURFACE"]), QColor(tokens["BORDER"])
        elif empty:
            fill = self._blend(QColor(tokens["BACKGROUND"]), panel, 0.85 if not self._hover else 1.0)
            edge = self._with_alpha(QColor(tokens["BORDER"]), 140 if not self._hover else 255)
        else:
            fill = self._blend(panel, accent, 0.3 if not self._hover else 0.4)
            edge = self._blend(panel, accent, 0.6)
        if self._pressed:
            fill = self._blend(fill, accent, 0.25)
        painter.setPen(QPen(edge, 1))
        painter.setBrush(fill)
        painter.drawRoundedRect(rect, radius, radius)
        if self._selected or self._armed or self._playing:
            ring = QColor(tokens["ACCENT"]) if self._selected else QColor("#ffd36b") if self._armed else QColor(tokens["SECONDARY"])
            painter.setPen(QPen(ring, 2.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), radius, radius)

        inner = rect.toRect().adjusted(9 if width >= 84 else 6, 7 if height >= 58 else 5, -8, -6)
        id_font = self._small_font(painter)
        painter.setFont(id_font)
        muted = QColor(tokens["MUTED"])
        if not empty and button.enabled:
            dot = 6 if height >= 58 else 5
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(accent)
            painter.drawEllipse(QRectF(inner.left(), inner.top() + 4, dot, dot))
            painter.setPen(muted)
            painter.drawText(inner.adjusted(dot + 5, 0, 0, 0), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, button.id)
        else:
            painter.setPen(self._with_alpha(muted, 150))
            painter.drawText(inner, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, button.id)

        badge = self._badge_text(button.enabled)
        if badge:
            self._draw_badge(painter, rect.toRect(), badge)
        if empty:
            if self._hover and button.enabled:
                self._draw_plus(painter, rect, muted)
            return
        show_action = height >= 52 and width >= 70
        caption_height = 15 if height < 90 else 17
        label_rect = inner.adjusted(0, 13 if height >= 58 else 10, 0, -(caption_height if show_action else 0))
        label_color = QColor(tokens["TEXT_STRONG"]) if button.enabled else QColor(tokens["PLACEHOLDER"])
        self._draw_label(painter, label_rect, button.label or "Untitled", label_color)
        if show_action:
            caption = QRect(inner.left(), inner.bottom() - caption_height, inner.width(), caption_height)
            self._draw_action_caption(painter, caption, action_type, muted, Qt.AlignmentFlag.AlignCenter)

    def _paint_studio(self, painter: QPainter) -> None:
        tokens = current_theme().colors
        button, action_type, empty, accent = self._pad_state()
        width, height = self._cell_size.width(), self._cell_size.height()
        rect = QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -1.5)
        radius = 3.0
        muted = QColor(tokens["MUTED"])
        tile = QColor(tokens["PANEL"]) if not empty else self._blend(QColor(tokens["BACKGROUND"]), QColor(tokens["PANEL"]), 0.55)
        if self._hover:
            tile = QColor(tokens["HOVER"])
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(tile)
        painter.drawRoundedRect(rect, radius, radius)
        small = self._small_font(painter)
        if not empty:
            band_height = max(16.0, rect.height() * 0.42)
            band = QRectF(rect.left(), rect.top(), rect.width(), band_height)
            band_color = accent if button.enabled else QColor(tokens["BORDER_STRONG"])
            if not self._hover:
                band_color = self._blend(band_color, QColor("#000000"), 0.12)
            if self._pressed:
                band_color = self._blend(band_color, QColor("#ffffff"), 0.2)
            painter.setBrush(band_color)
            painter.drawRoundedRect(band, radius, radius)
            painter.drawRect(QRectF(band.left(), band.bottom() - radius, band.width(), radius))
            label_rect = band.toRect().adjusted(8, 2, -8, -2)
            font = QFont(painter.font())
            font.setPointSize(max(8, self._title_point_size() - 2))
            font.setWeight(QFont.Weight.Bold)
            font, metrics = self._fit_font(font, button.label or "Untitled", label_rect.width(), minimum_size=7)
            painter.setFont(font)
            painter.setPen(self._readable_on(band_color))
            painter.drawText(
                label_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                metrics.elidedText(button.label or "Untitled", Qt.TextElideMode.ElideRight, label_rect.width()),
            )
            if height >= 50:
                caption = QRect(int(rect.left()) + 8, int(band.bottom()) + 4, int(rect.width()) - 16, 16)
                self._draw_action_caption(
                    painter, caption, action_type, QColor(tokens["TEXT"]), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
                )
        painter.setFont(small)
        painter.setPen(self._with_alpha(muted, 170))
        painter.drawText(
            rect.toRect().adjusted(6, 4, -7, -5), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom, button.id
        )
        badge = self._badge_text(button.enabled)
        if badge and not empty:
            self._draw_badge(painter, rect.toRect().adjusted(0, int(rect.height() * 0.42) - 4, 0, 0), badge)
        if self._selected or self._armed or self._playing:
            ring = QColor(tokens["ACCENT"]) if self._selected else QColor("#f2c14e") if self._armed else QColor(tokens["SECONDARY"])
            painter.setPen(QPen(ring, 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), radius, radius)
        elif empty and self._hover:
            self._draw_plus(painter, rect, muted)

    def _paint_hardware(self, painter: QPainter) -> None:
        tokens = current_theme().colors
        button, action_type, empty, accent = self._pad_state()
        width, height = self._cell_size.width(), self._cell_size.height()
        rect = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        radius = min(rect.width(), rect.height()) * 0.1
        lit = not empty and button.enabled
        if lit:
            led = accent if not self._pressed else self._blend(accent, QColor("#ffffff"), 0.3)
            glow = QRadialGradient(rect.center(), max(rect.width(), rect.height()) * 0.75)
            glow.setColorAt(0.0, self._blend(led, QColor("#ffffff"), 0.32 if self._hover else 0.22))
            glow.setColorAt(0.55, led)
            glow.setColorAt(1.0, self._blend(led, QColor("#000000"), 0.28))
            painter.setPen(QPen(self._blend(led, QColor("#000000"), 0.45), 1))
            painter.setBrush(glow)
        else:
            rubber = QColor("#2b2e36" if not self._hover else "#33363f")
            painter.setPen(QPen(QColor("#1a1c21"), 1))
            painter.setBrush(rubber)
        painter.drawRoundedRect(rect, radius, radius)
        if not lit:
            # A faint top highlight so unlit pads read as raised rubber.
            painter.setPen(QPen(QColor(255, 255, 255, 18), 1))
            painter.drawLine(QPointF(rect.left() + radius, rect.top() + 1.5), QPointF(rect.right() - radius, rect.top() + 1.5))

        text_color = self._readable_on(accent) if lit else QColor(tokens["MUTED"])
        inner = rect.toRect().adjusted(8, 6, -7, -6)
        painter.setFont(self._small_font(painter))
        painter.setPen(self._with_alpha(text_color, 170 if lit else 120))
        painter.drawText(inner, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, button.id)
        badge = self._badge_text(button.enabled)
        if badge:
            self._draw_badge(painter, rect.toRect(), badge)
        if self._selected or self._armed or self._playing:
            ring = QColor("#ffffff") if self._selected else QColor("#facc15") if self._armed else QColor(tokens["ACCENT"])
            painter.setPen(QPen(ring, 2.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), radius, radius)
        if empty:
            if self._hover and button.enabled:
                self._draw_plus(painter, rect, QColor(tokens["MUTED"]))
            return
        show_action = height >= 56 and width >= 70
        caption_height = 14 if height < 90 else 16
        label_rect = inner.adjusted(0, 12, 0, -(caption_height if show_action else 0))
        self._draw_label(painter, label_rect, button.label or "Untitled", text_color)
        if show_action:
            caption = QRect(inner.left(), inner.bottom() - caption_height, inner.width(), caption_height)
            self._draw_action_caption(painter, caption, action_type, self._with_alpha(text_color, 190), Qt.AlignmentFlag.AlignCenter)

    @staticmethod
    def _draw_plus(painter: QPainter, rect: QRectF, color: QColor) -> None:
        size = max(6.0, min(rect.width(), rect.height()) * 0.14)
        center = rect.center()
        painter.setPen(QPen(color, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(center.x() - size, center.y()), QPointF(center.x() + size, center.y()))
        painter.drawLine(QPointF(center.x(), center.y() - size), QPointF(center.x(), center.y() + size))

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
