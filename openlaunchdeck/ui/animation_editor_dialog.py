from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QKeySequence, QPainter, QPen, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QColorDialog,
    QDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ..animations.model import (
    FRAME_SIZE,
    GRID_SIZE,
    MAX_AUTHOR_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MAX_FPS,
    MAX_FRAMES,
    MAX_NAME_LENGTH,
    MIN_FPS,
    OFF,
    AnimationError,
    IdleAnimation,
    blank_frame,
)

UNLIT_PAD = "#1d1f27"
PALETTE = [
    "#ffffff", "#ff3b4e", "#ff7a1a", "#ffc93c", "#b5f23d", "#2ee86d", "#20e3b2", "#22d3ee",
    "#3b82f6", "#6d5cff", "#a855f7", "#ff5fa2", "#ff9ec7", "#7af5d8", "#8b5cf6", "#5a3420",
]
UNDO_LIMIT = 100


def frame_pixmap(frame: list[str], size: int = 44) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor("#0f1016"))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    gap = 1.0
    cell = (size - 4 - gap * (GRID_SIZE - 1)) / GRID_SIZE
    painter.setPen(Qt.PenStyle.NoPen)
    for index, color in enumerate(frame):
        row, col = divmod(index, GRID_SIZE)
        painter.setBrush(QColor(UNLIT_PAD if color == OFF else color))
        painter.drawRoundedRect(QRectF(2 + col * (cell + gap), 2 + row * (cell + gap), cell, cell), 1.2, 1.2)
    painter.end()
    return pixmap


class PadCanvas(QWidget):
    """An 8x8 paintable pad grid. Left button paints, right button erases."""

    stroke_started = Signal()
    cell_painted = Signal(int, bool)  # index, erase
    cell_picked = Signal(int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("AnimationCanvas")
        self.frame: list[str] = blank_frame()
        self.onion: list[str] | None = None
        self.editable = True
        self.pick_mode = False
        self._hover = -1
        self._last_cell = -1
        self._erasing = False
        self.setMouseTracking(True)
        self.setMinimumSize(280, 280)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def sizeHint(self) -> QSize:
        return QSize(400, 400)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return width

    def set_frame(self, frame: list[str], onion: list[str] | None = None) -> None:
        self.frame = frame
        self.onion = onion
        self.update()

    def _geometry(self) -> tuple[float, float, float, float]:
        side = min(self.width(), self.height())
        gap = max(3.0, side * 0.018)
        pad = (side - gap * (GRID_SIZE - 1)) / GRID_SIZE
        return (self.width() - side) / 2, (self.height() - side) / 2, pad, gap

    def _cell_at(self, point: QPointF) -> int:
        origin_x, origin_y, pad, gap = self._geometry()
        col = int((point.x() - origin_x) // (pad + gap))
        row = int((point.y() - origin_y) // (pad + gap))
        if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
            return row * GRID_SIZE + col
        return -1

    def mousePressEvent(self, event) -> None:
        cell = self._cell_at(event.position())
        if cell < 0 or not self.editable:
            return
        if self.pick_mode or event.modifiers() & Qt.KeyboardModifier.AltModifier:
            self.cell_picked.emit(cell)
            return
        self._erasing = event.button() == Qt.MouseButton.RightButton
        self._last_cell = cell
        self.stroke_started.emit()
        self.cell_painted.emit(cell, self._erasing)

    def mouseMoveEvent(self, event) -> None:
        cell = self._cell_at(event.position())
        if cell != self._hover:
            self._hover = cell
            self.update()
        buttons = event.buttons()
        if not self.editable or self.pick_mode or cell < 0 or cell == self._last_cell:
            return
        if buttons & (Qt.MouseButton.LeftButton | Qt.MouseButton.RightButton):
            self._last_cell = cell
            self.cell_painted.emit(cell, self._erasing)

    def mouseReleaseEvent(self, _event) -> None:
        self._last_cell = -1

    def leaveEvent(self, event) -> None:
        self._hover = -1
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        origin_x, origin_y, pad, gap = self._geometry()
        radius = pad * 0.2
        for index, color in enumerate(self.frame):
            row, col = divmod(index, GRID_SIZE)
            rect = QRectF(origin_x + col * (pad + gap), origin_y + row * (pad + gap), pad, pad)
            if color == OFF and self.onion is not None and self.onion[index] != OFF:
                fill = QColor(self.onion[index])
                fill.setAlpha(60)
                painter.setBrush(QColor(UNLIT_PAD))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(rect, radius, radius)
                painter.setBrush(fill)
            else:
                painter.setBrush(QColor(UNLIT_PAD if color == OFF else color))
            outline = QColor(255, 255, 255, 120 if index == self._hover and self.editable else 22)
            painter.setPen(QPen(outline, 1.5 if index == self._hover else 1))
            painter.drawRoundedRect(rect, radius, radius)
        painter.end()


class ColorSwatch(QToolButton):
    def __init__(self, color: str, parent=None) -> None:
        super().__init__(parent)
        self.color = color
        self.setObjectName("AnimationSwatch")
        self.setCheckable(True)
        self.setFixedSize(26, 26)
        self.setToolTip(color)
        self.set_color(color)

    def set_color(self, color: str) -> None:
        self.color = color
        self.setToolTip(color)
        self.setStyleSheet(
            f"QToolButton#AnimationSwatch {{ background: {color}; border: 2px solid rgba(255,255,255,0.12); border-radius: 7px; }}"
            "QToolButton#AnimationSwatch:checked { border: 2px solid #ffffff; }"
        )


class AnimationEditorDialog(QDialog):
    """Create or edit a frame-based idle animation."""

    def __init__(self, library, animation: IdleAnimation | None = None, idle_player=None, parent=None) -> None:
        super().__init__(parent)
        self.library = library
        self.idle_player = idle_player
        self.saved_animation: IdleAnimation | None = None
        source = animation or IdleAnimation(id="", name="", frames=[blank_frame()], fps=10)
        self._animation_id = source.id
        self.frames: list[list[str]] = [list(frame) for frame in source.frames] or [blank_frame()]
        self.current = 0
        self.color = PALETTE[1]
        self._undo: list[tuple[list[list[str]], int]] = []
        self._redo: list[tuple[list[list[str]], int]] = []
        self._dirty = False
        self._play_index = 0

        self.setObjectName("AnimationEditorDialog")
        self.setWindowTitle("Edit Animation" if source.id else "New Animation")
        self.resize(980, 720)
        self.setMinimumSize(820, 600)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)
        title = QLabel(self.windowTitle())
        title.setObjectName("SettingsTitle")
        root.addWidget(title)
        hint = QLabel("Left-click or drag to paint, right-click to erase, Alt-click to pick a color. Ctrl+Z undoes.")
        hint.setObjectName("SettingsDescription")
        hint.setWordWrap(True)
        root.addWidget(hint)

        body = QHBoxLayout()
        body.setSpacing(18)
        root.addLayout(body, 1)

        # Left: canvas and frame tools.
        left = QVBoxLayout()
        left.setSpacing(10)
        body.addLayout(left, 3)
        self.canvas = PadCanvas()
        self.canvas.stroke_started.connect(self._push_undo)
        self.canvas.cell_painted.connect(self._paint_cell)
        self.canvas.cell_picked.connect(self._pick_cell)
        left.addWidget(self.canvas, 1)

        tools = QHBoxLayout()
        tools.setSpacing(6)
        self.fill_button = self._tool("Fill", "Fill the whole frame with the current color", self._fill_frame)
        self.clear_button = self._tool("Clear", "Turn every pad in this frame off", self._clear_frame)
        self.pick_button = self._tool("Pick", "Click a pad to use its color", None, checkable=True)
        self.pick_button.toggled.connect(self._set_pick_mode)
        tools.addWidget(self.fill_button)
        tools.addWidget(self.clear_button)
        tools.addWidget(self.pick_button)
        tools.addSpacing(12)
        for label, tip, d_row, d_col in (
            ("←", "Shift pads left", 0, -1),
            ("→", "Shift pads right", 0, 1),
            ("↑", "Shift pads up", -1, 0),
            ("↓", "Shift pads down", 1, 0),
        ):
            tools.addWidget(self._tool(label, tip, lambda _checked=False, r=d_row, c=d_col: self._shift_frame(r, c)))
        tools.addStretch(1)
        self.onion_check = QCheckBox("Show previous frame")
        self.onion_check.setToolTip("Faintly shows the previous frame on unlit pads so motion is easier to line up.")
        self.onion_check.toggled.connect(lambda _checked: self._refresh_canvas())
        tools.addWidget(self.onion_check)
        left.addLayout(tools)

        # Right: palette, frames, playback, details.
        right = QVBoxLayout()
        right.setSpacing(12)
        body.addLayout(right, 2)

        right.addWidget(self._heading("Color"))
        palette_grid = QGridLayout()
        palette_grid.setSpacing(6)
        self._swatch_group = QButtonGroup(self)
        self._swatch_group.setExclusive(True)
        self.swatches: list[ColorSwatch] = []
        for index, color in enumerate(PALETTE):
            swatch = ColorSwatch(color)
            swatch.clicked.connect(lambda _checked=False, s=swatch: self._choose_color(s.color))
            self._swatch_group.addButton(swatch)
            palette_grid.addWidget(swatch, index // 8, index % 8)
            self.swatches.append(swatch)
        self.swatches[1].setChecked(True)
        right.addLayout(palette_grid)
        color_row = QHBoxLayout()
        self.current_color_chip = QLabel()
        self.current_color_chip.setFixedSize(34, 26)
        self.current_color_label = QLabel()
        custom = QPushButton("Custom color…")
        custom.setObjectName("SecondaryButton")
        custom.clicked.connect(self._custom_color)
        color_row.addWidget(self.current_color_chip)
        color_row.addWidget(self.current_color_label, 1)
        color_row.addWidget(custom)
        right.addLayout(color_row)

        right.addWidget(self._heading("Frames"))
        self.frame_list = QListWidget()
        self.frame_list.setObjectName("AnimationFrameStrip")
        self.frame_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.frame_list.setFlow(QListWidget.Flow.LeftToRight)
        self.frame_list.setWrapping(True)
        self.frame_list.setIconSize(QSize(44, 44))
        self.frame_list.setGridSize(QSize(58, 70))
        self.frame_list.setMovement(QListWidget.Movement.Static)
        self.frame_list.setMinimumHeight(160)
        self.frame_list.currentRowChanged.connect(self._select_frame)
        right.addWidget(self.frame_list, 1)
        frame_buttons = QHBoxLayout()
        frame_buttons.setSpacing(6)
        for label, tip, handler in (
            ("Add", "Add a blank frame after this one", self._add_frame),
            ("Duplicate", "Copy this frame", self._duplicate_frame),
            ("Delete", "Remove this frame", self._delete_frame),
            ("◀", "Move this frame earlier", lambda: self._move_frame(-1)),
            ("▶", "Move this frame later", lambda: self._move_frame(1)),
        ):
            button = QPushButton(label)
            button.setObjectName("SecondaryButton")
            button.setToolTip(tip)
            button.clicked.connect(handler)
            frame_buttons.addWidget(button)
        right.addLayout(frame_buttons)

        playback = QHBoxLayout()
        self.play_button = QPushButton("Play")
        self.play_button.setObjectName("SecondaryButton")
        self.play_button.setCheckable(True)
        self.play_button.toggled.connect(self._toggle_play)
        self.fps = QSpinBox()
        self.fps.setRange(MIN_FPS, MAX_FPS)
        self.fps.setSuffix(" fps")
        self.fps.setValue(max(MIN_FPS, min(MAX_FPS, source.fps)))
        self.fps.setToolTip("Frames per second. The Idle Animation speed setting scales this further.")
        self.fps.valueChanged.connect(self._mark_dirty)
        self.fps.valueChanged.connect(self._sync_play_timer)
        self.frame_info = QLabel()
        self.frame_info.setObjectName("SettingsDescription")
        playback.addWidget(self.play_button)
        playback.addWidget(self.fps)
        playback.addWidget(self.frame_info, 1)
        self.device_preview_button = QPushButton("Preview on Launchpad")
        self.device_preview_button.setObjectName("SecondaryButton")
        self.device_preview_button.clicked.connect(self._preview_on_device)
        self.device_preview_button.setVisible(idle_player is not None)
        playback.addWidget(self.device_preview_button)
        right.addLayout(playback)

        details = QFormLayout()
        details.setHorizontalSpacing(12)
        details.setVerticalSpacing(8)
        self.name_edit = QLineEdit(source.name)
        self.name_edit.setMaxLength(MAX_NAME_LENGTH)
        self.name_edit.setPlaceholderText("Neon Sweep")
        self.author_edit = QLineEdit(source.author)
        self.author_edit.setMaxLength(MAX_AUTHOR_LENGTH)
        self.author_edit.setPlaceholderText("Your name, shown when you share it")
        self.description_edit = QPlainTextEdit(source.description)
        self.description_edit.setPlaceholderText("What it looks like, in a sentence")
        self.description_edit.setFixedHeight(64)
        for widget in (self.name_edit, self.author_edit):
            widget.textEdited.connect(self._mark_dirty)
        self.description_edit.textChanged.connect(self._mark_dirty)
        details.addRow("Name", self.name_edit)
        details.addRow("Author", self.author_edit)
        details.addRow("Description", self.description_edit)
        right.addLayout(details)

        footer = QHBoxLayout()
        self.status = QLabel()
        self.status.setObjectName("SettingsDescription")
        footer.addWidget(self.status, 1)
        cancel = QPushButton("Cancel")
        cancel.setObjectName("SecondaryButton")
        cancel.clicked.connect(self.reject)
        save = QPushButton("Save animation")
        save.setObjectName("PrimaryButton")
        save.setDefault(True)
        save.clicked.connect(self._save)
        footer.addWidget(cancel)
        footer.addWidget(save)
        root.addLayout(footer)

        self._play_timer = QTimer(self)
        self._play_timer.timeout.connect(self._advance_playback)
        QShortcut(QKeySequence.StandardKey.Undo, self, activated=self.undo)
        QShortcut(QKeySequence.StandardKey.Redo, self, activated=self.redo)
        QShortcut(QKeySequence("Ctrl+Shift+Z"), self, activated=self.redo)

        self._choose_color(self.color)
        self._rebuild_strip()
        self._dirty = False

    # Building helpers

    @staticmethod
    def _heading(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("SectionTitle")
        return label

    def _tool(self, text: str, tip: str, handler, checkable: bool = False) -> QToolButton:
        button = QToolButton()
        button.setObjectName("AnimationTool")
        button.setText(text)
        button.setToolTip(tip)
        button.setCheckable(checkable)
        button.setMinimumHeight(30)
        if handler is not None:
            button.clicked.connect(handler)
        return button

    # State

    def _mark_dirty(self, *_args) -> None:
        self._dirty = True

    def _snapshot(self) -> tuple[list[list[str]], int]:
        return [list(frame) for frame in self.frames], self.current

    def _push_undo(self) -> None:
        self._undo.append(self._snapshot())
        del self._undo[:-UNDO_LIMIT]
        self._redo.clear()
        self._dirty = True

    def undo(self) -> None:
        if self._undo:
            self._redo.append(self._snapshot())
            self.frames, self.current = self._undo.pop()
            self._rebuild_strip()

    def redo(self) -> None:
        if self._redo:
            self._undo.append(self._snapshot())
            self.frames, self.current = self._redo.pop()
            self._rebuild_strip()

    # Color

    def _choose_color(self, color: str) -> None:
        self.color = color
        for swatch in self.swatches:
            swatch.setChecked(swatch.color == color)
        self.current_color_chip.setStyleSheet(
            f"background: {color}; border-radius: 6px; border: 1px solid rgba(255,255,255,0.2);"
        )
        self.current_color_label.setText(color.upper())

    def _custom_color(self) -> None:
        chosen = QColorDialog.getColor(QColor(self.color), self, "Pad color")
        if chosen.isValid():
            self._choose_color(chosen.name().lower())

    def _set_pick_mode(self, enabled: bool) -> None:
        self.canvas.pick_mode = enabled
        self.canvas.setCursor(Qt.CursorShape.PointingHandCursor if enabled else Qt.CursorShape.CrossCursor)

    def _pick_cell(self, index: int) -> None:
        color = self.frames[self.current][index]
        if color != OFF:
            self._choose_color(color)
        self.pick_button.setChecked(False)

    # Frame editing

    def _paint_cell(self, index: int, erase: bool) -> None:
        self.frames[self.current][index] = OFF if erase else self.color
        self._refresh_canvas()
        self._refresh_thumbnail(self.current)

    def _fill_frame(self) -> None:
        self._push_undo()
        self.frames[self.current] = [self.color] * FRAME_SIZE
        self._refresh_current()

    def _clear_frame(self) -> None:
        self._push_undo()
        self.frames[self.current] = blank_frame()
        self._refresh_current()

    def _shift_frame(self, d_row: int, d_col: int) -> None:
        self._push_undo()
        frame = self.frames[self.current]
        shifted = blank_frame()
        for index, color in enumerate(frame):
            row, col = divmod(index, GRID_SIZE)
            target = ((row + d_row) % GRID_SIZE) * GRID_SIZE + (col + d_col) % GRID_SIZE
            shifted[target] = color
        self.frames[self.current] = shifted
        self._refresh_current()

    def _add_frame(self) -> None:
        if self._at_frame_limit():
            return
        self._push_undo()
        self.frames.insert(self.current + 1, blank_frame())
        self.current += 1
        self._rebuild_strip()

    def _duplicate_frame(self) -> None:
        if self._at_frame_limit():
            return
        self._push_undo()
        self.frames.insert(self.current + 1, list(self.frames[self.current]))
        self.current += 1
        self._rebuild_strip()

    def _delete_frame(self) -> None:
        if len(self.frames) == 1:
            self._clear_frame()
            return
        self._push_undo()
        del self.frames[self.current]
        self.current = min(self.current, len(self.frames) - 1)
        self._rebuild_strip()

    def _move_frame(self, offset: int) -> None:
        target = self.current + offset
        if not 0 <= target < len(self.frames):
            return
        self._push_undo()
        self.frames[self.current], self.frames[target] = self.frames[target], self.frames[self.current]
        self.current = target
        self._rebuild_strip()

    def _at_frame_limit(self) -> bool:
        if len(self.frames) >= MAX_FRAMES:
            self.status.setText(f"Animations can have up to {MAX_FRAMES} frames.")
            return True
        return False

    # Views

    def _select_frame(self, row: int) -> None:
        if 0 <= row < len(self.frames) and not self.play_button.isChecked():
            self.current = row
            self._refresh_canvas()

    def _rebuild_strip(self) -> None:
        self.frame_list.blockSignals(True)
        self.frame_list.clear()
        for index, frame in enumerate(self.frames):
            item = QListWidgetItem(QIcon(frame_pixmap(frame)), str(index + 1))
            item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter)
            self.frame_list.addItem(item)
        self.frame_list.setCurrentRow(self.current)
        self.frame_list.blockSignals(False)
        self._refresh_canvas()

    def _refresh_thumbnail(self, index: int) -> None:
        item = self.frame_list.item(index)
        if item is not None:
            item.setIcon(QIcon(frame_pixmap(self.frames[index])))

    def _refresh_current(self) -> None:
        self._refresh_thumbnail(self.current)
        self._refresh_canvas()

    def _refresh_canvas(self) -> None:
        onion = None
        if self.onion_check.isChecked() and self.current > 0:
            onion = self.frames[self.current - 1]
        self.canvas.set_frame(self.frames[self.current], onion)
        self.frame_info.setText(f"Frame {self.current + 1} of {len(self.frames)}")

    # Playback

    def _toggle_play(self, playing: bool) -> None:
        self.play_button.setText("Stop" if playing else "Play")
        self.canvas.editable = not playing
        self._play_index = self.current
        self._sync_play_timer()
        if not playing:
            self._refresh_canvas()

    def _sync_play_timer(self, *_args) -> None:
        if self.play_button.isChecked():
            self._play_timer.start(max(33, round(1000 / self.fps.value())))
        else:
            self._play_timer.stop()

    def _advance_playback(self) -> None:
        self._play_index = (self._play_index + 1) % len(self.frames)
        self.canvas.set_frame(self.frames[self._play_index])
        self.frame_info.setText(f"Playing frame {self._play_index + 1} of {len(self.frames)}")

    def current_animation(self) -> IdleAnimation:
        return IdleAnimation.from_dict(
            {
                "id": self._animation_id,
                "name": self.name_edit.text() or "Untitled",
                "author": self.author_edit.text(),
                "description": self.description_edit.toPlainText()[:MAX_DESCRIPTION_LENGTH],
                "fps": self.fps.value(),
                "frames": self.frames,
            }
        )

    def _preview_on_device(self) -> None:
        if self.idle_player is None:
            return
        started = self.idle_player.preview(self.current_animation(), seconds=8)
        self.status.setText(
            "Playing on your Launchpad for 8 seconds." if started else "Connect your Launchpad to preview on it."
        )

    # Closing

    def _save(self) -> None:
        if not self.name_edit.text().strip():
            self.status.setText("Give the animation a name before saving.")
            self.name_edit.setFocus()
            return
        try:
            animation = self.current_animation()
            animation.id = self._animation_id
            self.saved_animation = self.library.save(animation)
        except (AnimationError, OSError) as exc:
            self.status.setText(f"Couldn't save: {exc}")
            return
        self._dirty = False
        self.accept()

    def reject(self) -> None:
        if self._dirty:
            answer = QMessageBox.question(
                self,
                "Discard changes?",
                "This animation has unsaved changes. Close without saving?",
                QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            )
            if answer != QMessageBox.StandardButton.Discard:
                return
        self._play_timer.stop()
        super().reject()

    def done(self, result: int) -> None:
        self._play_timer.stop()
        super().done(result)
