from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..animations.model import AnimationError, IdleAnimation
from .animation_editor_dialog import AnimationEditorDialog
from .animation_preview import AnimationPreview

CARD_COLUMNS = 3
# Most chat apps cap a message near this length (Discord: 2,000 characters).
CHAT_MESSAGE_LIMIT = 2000
FILE_FILTER = "OpenLaunchDeck animation (*.json)"


class AnimationCard(QFrame):
    clicked = Signal(str)

    def __init__(self, animation, in_use: bool, parent=None) -> None:
        super().__init__(parent)
        self.animation_id = animation.id
        self.setObjectName("AnimationCard")
        self.setProperty("selected", False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        self.preview = AnimationPreview(pad_size=12, gap=3)
        self.preview.set_animation(animation)
        layout.addWidget(self.preview, 0, Qt.AlignmentFlag.AlignHCenter)
        name = QLabel(animation.name)
        name.setObjectName("AnimationCardTitle")
        name.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(name)
        if getattr(animation, "builtin", False):
            meta = "Built-in"
        else:
            meta = f"by {animation.author}" if animation.author else "Yours"
        if in_use:
            meta += "  ·  In use"
        caption = QLabel(meta)
        caption.setObjectName("AnimationCardMeta")
        caption.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(caption)

    def set_selected(self, selected: bool) -> None:
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.animation_id)
        super().mousePressEvent(event)


class AnimationLibraryDialog(QDialog):
    """Browse, preview, create, import, and share idle animations."""

    def __init__(self, library, settings_service, idle_player=None, parent=None) -> None:
        super().__init__(parent)
        self.library = library
        self.settings_service = settings_service
        self.idle_player = idle_player
        self.selected_id = settings_service.settings.idle_animation_id
        self._filter = "all"
        self._cards: dict[str, AnimationCard] = {}

        self.setObjectName("AnimationLibraryDialog")
        self.setWindowTitle("Idle Animations")
        self.resize(1040, 720)
        self.setMinimumSize(820, 560)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        header = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(2)
        title = QLabel("Idle Animations")
        title.setObjectName("SettingsTitle")
        subtitle = QLabel("Pick what your Launchpad plays when it sits idle, make your own, or import ones other people share.")
        subtitle.setObjectName("SettingsDescription")
        subtitle.setWordWrap(True)
        titles.addWidget(title)
        titles.addWidget(subtitle)
        header.addLayout(titles, 1)
        for label, handler, primary in (
            ("New animation", self._new_animation, True),
            ("Import file…", self._import_file, False),
            ("Paste share code…", self._import_share_code, False),
        ):
            button = QPushButton(label)
            button.setObjectName("PrimaryButton" if primary else "SecondaryButton")
            button.clicked.connect(handler)
            header.addWidget(button, 0, Qt.AlignmentFlag.AlignTop)
        root.addLayout(header)

        filters = QHBoxLayout()
        filters.setSpacing(6)
        self._filter_group = QButtonGroup(self)
        for key, label in (("all", "All"), ("builtin", "Built-in"), ("mine", "Yours and imported")):
            chip = QPushButton(label)
            chip.setObjectName("FilterChip")
            chip.setCheckable(True)
            chip.setChecked(key == "all")
            chip.clicked.connect(lambda _checked=False, k=key: self._set_filter(k))
            self._filter_group.addButton(chip)
            filters.addWidget(chip)
        filters.addStretch(1)
        root.addLayout(filters)

        body = QHBoxLayout()
        body.setSpacing(16)
        root.addLayout(body, 1)

        self.grid_host = QWidget()
        self.grid = QGridLayout(self.grid_host)
        self.grid.setContentsMargins(0, 0, 6, 0)
        self.grid.setSpacing(12)
        scroll = QScrollArea()
        scroll.setObjectName("AnimationGridScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(self.grid_host)
        body.addWidget(scroll, 3)

        detail = QFrame()
        detail.setObjectName("SettingsSection")
        detail.setMinimumWidth(300)
        detail_layout = QVBoxLayout(detail)
        detail_layout.setContentsMargins(18, 18, 18, 18)
        detail_layout.setSpacing(10)
        self.detail_preview = AnimationPreview(pad_size=26, gap=5)
        detail_layout.addWidget(self.detail_preview, 0, Qt.AlignmentFlag.AlignHCenter)
        self.detail_name = QLabel()
        self.detail_name.setObjectName("SettingsTitle")
        self.detail_name.setWordWrap(True)
        self.detail_meta = QLabel()
        self.detail_meta.setObjectName("SectionTitle")
        self.detail_description = QLabel()
        self.detail_description.setObjectName("SettingsDescription")
        self.detail_description.setWordWrap(True)
        for widget in (self.detail_name, self.detail_meta, self.detail_description):
            detail_layout.addWidget(widget)
        detail_layout.addStretch(1)

        self.use_button = QPushButton("Use as idle animation")
        self.use_button.setObjectName("PrimaryButton")
        self.use_button.clicked.connect(self._use_selected)
        self.device_button = QPushButton("Preview on Launchpad")
        self.device_button.setObjectName("SecondaryButton")
        self.device_button.clicked.connect(self._preview_on_device)
        self.device_button.setVisible(idle_player is not None)
        self.edit_button = QPushButton("Edit")
        self.edit_button.setObjectName("SecondaryButton")
        self.edit_button.clicked.connect(self._edit_selected)
        self.share_button = QPushButton("Copy share code")
        self.share_button.setObjectName("SecondaryButton")
        self.share_button.setToolTip("Copies a code you can paste in a chat. Others use Paste share code to add it.")
        self.share_button.clicked.connect(self._copy_share_code)
        self.export_button = QPushButton("Export file…")
        self.export_button.setObjectName("SecondaryButton")
        self.export_button.clicked.connect(self._export_selected)
        self.delete_button = QPushButton("Delete")
        self.delete_button.setObjectName("DangerButton")
        self.delete_button.clicked.connect(self._delete_selected)
        detail_layout.addWidget(self.use_button)
        detail_layout.addWidget(self.device_button)
        action_grid = QGridLayout()
        action_grid.setSpacing(8)
        action_grid.addWidget(self.edit_button, 0, 0)
        action_grid.addWidget(self.share_button, 0, 1)
        action_grid.addWidget(self.export_button, 1, 0)
        action_grid.addWidget(self.delete_button, 1, 1)
        detail_layout.addLayout(action_grid)
        self.status = QLabel()
        self.status.setObjectName("SettingsDescription")
        self.status.setWordWrap(True)
        detail_layout.addWidget(self.status)
        body.addWidget(detail, 2)

        footer = QHBoxLayout()
        footer.addStretch(1)
        close = QPushButton("Done")
        close.setObjectName("SecondaryButton")
        close.clicked.connect(self.accept)
        footer.addWidget(close)
        root.addLayout(footer)

        self._rebuild()

    # Grid

    def _visible_animations(self):
        animations = self.library.all()
        if self._filter == "builtin":
            return [item for item in animations if getattr(item, "builtin", False)]
        if self._filter == "mine":
            return [item for item in animations if not getattr(item, "builtin", False)]
        return animations

    def _set_filter(self, key: str) -> None:
        self._filter = key
        self._rebuild()

    def _rebuild(self) -> None:
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        self._cards.clear()
        in_use = self.settings_service.settings.idle_animation_id
        animations = self._visible_animations()
        for index, animation in enumerate(animations):
            card = AnimationCard(animation, animation.id == in_use)
            card.clicked.connect(self._select)
            self.grid.addWidget(card, index // CARD_COLUMNS, index % CARD_COLUMNS)
            self._cards[animation.id] = card
        if not animations:
            empty = QLabel("You haven't made or imported any animations yet. Start one with New animation, or paste a share code from a friend.")
            empty.setObjectName("SettingsDescription")
            empty.setWordWrap(True)
            self.grid.addWidget(empty, 0, 0, 1, CARD_COLUMNS)
        self.grid.setRowStretch(self.grid.rowCount(), 1)
        if self.selected_id not in self._cards:
            self.selected_id = animations[0].id if animations else ""
        self._select(self.selected_id)

    def _select(self, animation_id: str) -> None:
        self.selected_id = animation_id
        for card_id, card in self._cards.items():
            card.set_selected(card_id == animation_id)
        animation = self.library.get(animation_id) if animation_id else None
        has_selection = animation is not None
        builtin = bool(getattr(animation, "builtin", False))
        for button in (self.use_button, self.device_button, self.edit_button, self.share_button, self.export_button):
            button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection and not builtin)
        self.delete_button.setToolTip("" if not builtin else "Built-in animations can't be deleted.")
        self.edit_button.setText("Edit a copy" if builtin else "Edit")
        self.detail_preview.set_animation(animation)
        if animation is None:
            self.detail_name.setText("No animation selected")
            self.detail_meta.setText("")
            self.detail_description.setText("")
            return
        self.detail_name.setText(animation.name)
        source = "Built-in" if builtin else (f"By {animation.author}" if animation.author else "Made by you")
        frames = "Generated live" if builtin else f"{animation.frame_count} frames"
        self.detail_meta.setText(f"{source}  ·  {animation.fps} fps  ·  {frames}")
        self.detail_description.setText(animation.description or "No description.")

    # Actions

    def _use_selected(self) -> None:
        if not self.selected_id:
            return
        self.settings_service.update(
            idle_animation_id=self.selected_id,
            idle_animation_shuffle=False,
            idle_animation_enabled=True,
        )
        if self.idle_player is not None:
            self.idle_player.settings_changed()
        name = self.library.get(self.selected_id).name
        self.status.setText(f"{name} plays after {self.settings_service.settings.idle_animation_timeout_seconds} seconds idle.")
        self._rebuild()

    def _preview_on_device(self) -> None:
        if self.idle_player is None or not self.selected_id:
            return
        started = self.idle_player.preview(self.selected_id, seconds=8)
        self.status.setText(
            "Playing on your Launchpad for 8 seconds. Press any pad to stop."
            if started
            else "Connect your Launchpad to preview on it."
        )

    def _open_editor(self, animation: IdleAnimation | None) -> None:
        editor = AnimationEditorDialog(self.library, animation, self.idle_player, self)
        if editor.exec() and editor.saved_animation is not None:
            self.selected_id = editor.saved_animation.id
            if self._filter == "builtin":
                self._filter = "all"
                self._filter_group.buttons()[0].setChecked(True)
            self.status.setText(f"Saved {editor.saved_animation.name}.")
            self._rebuild()

    def _new_animation(self) -> None:
        self._open_editor(None)

    def _edit_selected(self) -> None:
        if not self.selected_id:
            return
        try:
            animation = self.library.as_frames(self.selected_id)
        except AnimationError as exc:
            self.status.setText(str(exc))
            return
        if self.library.is_builtin(self.selected_id):
            animation.name = f"{animation.name} Remix"[:60]
            animation.author = ""
            animation.id = ""
        else:
            animation.id = self.selected_id
        self._open_editor(animation)

    def _copy_share_code(self) -> None:
        if not self.selected_id:
            return
        try:
            code = self.library.share_code(self.selected_id)
        except AnimationError as exc:
            self.status.setText(str(exc))
            return
        QApplication.clipboard().setText(code)
        if len(code) > CHAT_MESSAGE_LIMIT:
            self.status.setText(
                f"Share code copied ({len(code):,} characters). That's longer than most chat messages allow, "
                "so use Export file to share it in a chat."
            )
        else:
            self.status.setText(f"Share code copied ({len(code):,} characters). Paste it anywhere to share.")

    def _export_selected(self) -> None:
        if not self.selected_id:
            return
        animation = self.library.get(self.selected_id)
        default_name = "".join(char if char.isalnum() else "_" for char in animation.name).strip("_") or "animation"
        path, _ = QFileDialog.getSaveFileName(self, "Export animation", f"{default_name}.json", FILE_FILTER)
        if not path:
            return
        try:
            self.library.export_file(self.selected_id, Path(path))
        except (AnimationError, OSError) as exc:
            QMessageBox.warning(self, "Export failed", f"The animation couldn't be exported.\n\n{exc}")
            return
        self.status.setText(f"Exported to {Path(path).name}.")

    def _import_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import animation", "", FILE_FILTER + ";;All files (*)")
        if not path:
            return
        try:
            animation = self.library.import_file(Path(path))
        except (AnimationError, OSError) as exc:
            QMessageBox.warning(self, "Import failed", f"That file couldn't be imported.\n\n{exc}")
            return
        self._show_imported(animation)

    def _import_share_code(self) -> None:
        clipboard = QApplication.clipboard().text().strip()
        default = clipboard if clipboard.startswith("OLDA1:") else ""
        code, accepted = QInputDialog.getMultiLineText(
            self, "Paste share code", "Paste an animation share code (it starts with OLDA1:)", default
        )
        if not accepted or not code.strip():
            return
        try:
            animation = self.library.import_share_code(code)
        except (AnimationError, OSError) as exc:
            QMessageBox.warning(self, "Import failed", str(exc))
            return
        self._show_imported(animation)

    def _show_imported(self, animation: IdleAnimation) -> None:
        self.selected_id = animation.id
        if self._filter == "builtin":
            self._filter = "all"
            self._filter_group.buttons()[0].setChecked(True)
        credit = f" by {animation.author}" if animation.author else ""
        self.status.setText(f"Added {animation.name}{credit}.")
        self._rebuild()

    def _delete_selected(self) -> None:
        if not self.selected_id or self.library.is_builtin(self.selected_id):
            return
        animation = self.library.get(self.selected_id)
        answer = QMessageBox.question(
            self,
            "Delete animation?",
            f"Delete {animation.name}? A backup copy is kept in the backups folder.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        was_in_use = self.settings_service.settings.idle_animation_id == self.selected_id
        self.library.delete(self.selected_id)
        if was_in_use:
            self.settings_service.update(idle_animation_id="rainbow_wave")
        self.status.setText(f"Deleted {animation.name}.")
        self.selected_id = ""
        self._rebuild()
