from __future__ import annotations

import itertools
from collections.abc import Iterator

from PySide6.QtCore import QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from ..animations.model import FRAME_SIZE, GRID_SIZE, OFF, scale_color

UNLIT_PAD = "#1d1f27"
PREVIEW_SEED = 7
_UNLIT_EDGE = QColor(255, 255, 255, 18)
_colors: dict[str, QColor] = {}


def _qcolor(hex_color: str) -> QColor:
    # Frames repeat a small set of colors; parsing them once keeps painting cheap.
    color = _colors.get(hex_color)
    if color is None:
        if len(_colors) > 4096:
            _colors.clear()
        color = _colors[hex_color] = QColor(hex_color)
    return color


class AnimationPreview(QWidget):
    """Plays an animation on an on-screen 8x8 pad grid."""

    def __init__(self, parent=None, pad_size: int = 18, gap: int = 4, max_fps: float = 30.0) -> None:
        super().__init__(parent)
        self.setObjectName("AnimationPreview")
        self._pad_size = pad_size
        self._gap = gap
        # Small thumbnails don't need full speed; capping them keeps a gallery cheap.
        self._max_fps = max(1.0, max_fps)
        self._animation = None
        self._frames: Iterator[list[str]] | None = None
        self._frame: list[str] = [OFF] * FRAME_SIZE
        self._brightness = 1.0
        self._speed = 1.0
        self._paused = False
        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._timer.timeout.connect(self._advance)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)

    def sizeHint(self) -> QSize:
        side = GRID_SIZE * self._pad_size + (GRID_SIZE - 1) * self._gap
        return QSize(side, side)

    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()

    def set_animation(self, animation) -> None:
        self._animation = animation
        self._frames = animation.iter_frames(PREVIEW_SEED) if animation is not None else None
        self._advance()
        self._sync_timer()

    def set_frame(self, frame: list[str]) -> None:
        """Show one fixed frame (used by the editor)."""
        self._animation = None
        self._frames = None
        self._timer.stop()
        self._frame = list(frame)
        self.update()

    def set_brightness(self, percent: int) -> None:
        self._brightness = max(0.0, min(1.0, percent / 100))
        self.update()

    def set_speed(self, percent: int) -> None:
        self._speed = max(0.25, min(3.0, percent / 100))
        self._sync_timer()

    def set_paused(self, paused: bool) -> None:
        self._paused = paused
        self._sync_timer()

    def current_frame(self) -> list[str]:
        return list(self._frame)

    def _interval_ms(self) -> int:
        fps = getattr(self._animation, "fps", 10) * self._speed
        return max(33, round(1000 / max(1.0, min(30.0, self._max_fps, fps))))

    def _sync_timer(self) -> None:
        if self._frames is not None and not self._paused and self.isVisible():
            self._timer.start(self._interval_ms())
        else:
            self._timer.stop()

    def _advance(self) -> None:
        if self._frames is None:
            frame = [OFF] * FRAME_SIZE
        elif self._timer.isActive() and self.visibleRegion().isEmpty():
            # Scrolled out of view: pause instead of drawing frames nobody sees.
            return
        else:
            frame = next(self._frames)
        if frame != self._frame:
            self._frame = frame
            self.update()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._sync_timer()

    def hideEvent(self, event) -> None:
        super().hideEvent(event)
        self._timer.stop()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        side = min(self.width(), self.height())
        pad = (side - (GRID_SIZE - 1) * self._gap) / GRID_SIZE
        radius = max(2.0, pad * 0.22)
        origin_x = (self.width() - side) / 2
        origin_y = (self.height() - side) / 2
        unlit_pen = QPen(_UNLIT_EDGE, 1)
        for index, color in enumerate(itertools.islice(self._frame, FRAME_SIZE)):
            row, col = divmod(index, GRID_SIZE)
            rect = QRectF(origin_x + col * (pad + self._gap), origin_y + row * (pad + self._gap), pad, pad)
            lit = scale_color(color, self._brightness)
            if lit == OFF:
                painter.setPen(unlit_pen)
                painter.setBrush(_qcolor(UNLIT_PAD))
            else:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(_qcolor(lit))
            painter.drawRoundedRect(rect, radius, radius)
        painter.end()
