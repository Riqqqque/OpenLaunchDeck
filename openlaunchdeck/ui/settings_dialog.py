from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..animations import AnimationLibrary
from ..audio.input_devices import list_input_devices
from ..audio.output_devices import (
    hidden_advanced_output_count,
    hidden_duplicate_count,
    list_output_devices,
)
from ..constants import (
    LAUNCHPAD_AUXILIARY_CONTROL_LABELS,
    LAUNCHPAD_CONTROL_BINDING_LABELS,
)
from ..devices.midi_manager import MidiManager
from ..paths import APP_DATA_DIR
from .animation_preview import AnimationPreview
from .theme import apply_theme, theme_definition, theme_definitions


class PercentControl(QWidget):
    def __init__(self, value: int, parent=None, minimum: int = 0, maximum: int = 100) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(minimum, maximum)
        self.spin = QSpinBox()
        self.spin.setRange(minimum, maximum)
        self.spin.setSuffix("%")
        self.spin.setFixedWidth(108)
        self.slider.setValue(value)
        self.spin.setValue(value)
        self.slider.valueChanged.connect(self.spin.setValue)
        self.spin.valueChanged.connect(self.slider.setValue)
        layout.addWidget(self.slider, 1)
        layout.addWidget(self.spin)

    def value(self) -> int:
        return self.spin.value()


class AuxiliaryBindingsEditor(QWidget):
    def __init__(self, bindings: dict[str, str], parent=None) -> None:
        super().__init__(parent)
        self.combos: dict[str, QComboBox] = {}
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(8)
        controls = list(LAUNCHPAD_AUXILIARY_CONTROL_LABELS.items())
        for index, (control_id, label) in enumerate(controls):
            row = index % 8
            pair = index // 8
            label_widget = QLabel(label)
            label_widget.setObjectName("FieldLabel")
            combo = QComboBox()
            for binding_id, binding_label in LAUNCHPAD_CONTROL_BINDING_LABELS.items():
                combo.addItem(binding_label, binding_id)
            combo.setCurrentIndex(max(0, combo.findData(bindings.get(control_id, "none"))))
            combo.setMinimumWidth(145)
            layout.addWidget(label_widget, row, pair * 2)
            layout.addWidget(combo, row, pair * 2 + 1)
            layout.setColumnStretch(pair * 2 + 1, 1)
            self.combos[control_id] = combo

    def bindings(self) -> dict[str, str]:
        return {
            control_id: str(combo.currentData() or "none")
            for control_id, combo in self.combos.items()
        }


class SettingsDialog(QDialog):
    def __init__(
        self,
        settings_service,
        parent=None,
        startup_service=None,
        animation_library: AnimationLibrary | None = None,
        idle_player=None,
    ) -> None:
        super().__init__(parent)
        self.animation_library = animation_library or AnimationLibrary()
        self.idle_player = idle_player
        self.setWindowTitle("Settings")
        self.setObjectName("SettingsDialog")
        self.resize(800, 680)
        self.setMinimumSize(680, 540)
        self.settings_service = settings_service
        self.startup_service = startup_service
        self._original_theme = settings_service.settings.theme
        settings = settings_service.settings

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        heading = QLabel("OpenLaunchDeck Settings")
        heading.setObjectName("SettingsTitle")
        layout.addWidget(heading)
        subtitle = QLabel("Appearance, Launchpad, audio, and app behavior are kept in separate groups.")
        subtitle.setObjectName("SettingsDescription")
        layout.addWidget(subtitle)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        layout.addWidget(self.tabs, 1)

        self._build_appearance_tab(settings)
        self._build_launchpad_tab(settings)
        self._build_soundboard_tab(settings)
        self._build_idle_animation_tab(settings)
        self._build_app_tab(settings)
        self._build_advanced_tab(settings)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setObjectName("PrimaryButton")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _build_appearance_tab(self, settings) -> None:
        self.theme = QComboBox()
        definitions = theme_definitions()
        styled = [definition for definition in definitions if definition.style != "classic"]
        classic = [definition for definition in definitions if definition.style == "classic"]
        for definition in styled:
            self.theme.addItem(f"{definition.name} style", definition.key)
        self.theme.insertSeparator(self.theme.count())
        for definition in classic:
            self.theme.addItem(definition.name, definition.key)
        self.theme.addItem("Follow Windows", "system")
        self.theme.setCurrentIndex(max(0, self.theme.findData(settings.theme)))
        self.theme_description = QLabel()
        self.theme_description.setObjectName("ThemeDescription")
        self.theme_description.setWordWrap(True)
        self.theme_swatches = QWidget()
        swatches_layout = QHBoxLayout(self.theme_swatches)
        swatches_layout.setContentsMargins(0, 0, 0, 0)
        swatches_layout.setSpacing(6)
        self._swatch_labels: list[QLabel] = []
        for _index in range(4):
            swatch = QLabel()
            swatch.setFixedSize(26, 26)
            swatches_layout.addWidget(swatch)
            self._swatch_labels.append(swatch)
        swatches_layout.addStretch(1)
        self.theme.currentIndexChanged.connect(self._preview_theme)
        self._update_theme_preview()

        self.grid_density = QComboBox()
        self.grid_density.addItem("Compact", "compact")
        self.grid_density.addItem("Comfortable", "comfortable")
        self.grid_density.addItem("Large", "large")
        self.grid_density.setCurrentIndex(max(0, self.grid_density.findData(settings.grid_density)))
        self.deck_view = QCheckBox("Open with the grid-first Deck View")
        self.deck_view.setChecked(settings.deck_view)
        self.tabs.addTab(
            self._tab(
                self._section(
                    "Style",
                    "Nebula, Studio, and Hardware each change the whole look, including the shape of the pads. "
                    "The classic themes keep the original layout in different colors. "
                    "The preview applies immediately and reverts if you cancel.",
                    [("Look", self.theme), ("", self.theme_description), ("Palette", self.theme_swatches)],
                ),
                self._section(
                    "Launchpad Grid",
                    "Pad size controls label scale and maximum keycap size. The grid always fits the available window.",
                    [("Readability", self.grid_density), ("", self.deck_view)],
                ),
            ),
            "Appearance",
        )

    def _build_launchpad_tab(self, settings) -> None:
        self.auto_connect = QCheckBox("Connect automatically when OpenLaunchDeck starts")
        self.auto_connect.setChecked(settings.auto_connect)
        self.midi_input = self._editable_port_combo(MidiManager.available_input_ports(), settings.midi_input_port, "Auto-detect input")
        self.midi_output = self._editable_port_combo(MidiManager.available_output_ports(), settings.midi_output_port, "Auto-detect output")
        self.midi_debug = QCheckBox("Include raw MIDI messages in debug logs")
        self.midi_debug.setChecked(settings.midi_debug_logging)
        self.auxiliary_bindings = AuxiliaryBindingsEditor(settings.launchpad_control_bindings)
        self.tabs.addTab(
            self._tab(
                self._section(
                    "Connection",
                    "Auto-detect is recommended. Choose exact ports only when Windows exposes more than one Launchpad port.",
                    [("", self.auto_connect), ("MIDI input", self.midi_input), ("MIDI output", self.midi_output)],
                ),
                self._section(
                    "Diagnostics",
                    "Raw logging is useful during mapping calibration and should stay off during normal play.",
                    [("", self.midi_debug)],
                ),
                self._section(
                    "Hardware Buttons",
                    "Programmer Mode exposes the top row and eight Scene buttons. These assignments are independent from the 8x8 pad grid.",
                    [("", self.auxiliary_bindings)],
                ),
            ),
            "Launchpad",
        )

    def _build_soundboard_tab(self, settings) -> None:
        devices = list_output_devices()
        self.output_device = QComboBox()
        self.output_device.addItem("System default (recommended)", "")
        self._add_device_items(self.output_device, devices)
        self._select_saved_device(self.output_device, settings.soundboard_default_output_device)
        self.global_volume = PercentControl(settings.soundboard_global_volume)
        self.stop_on_exit = QCheckBox("Stop every sound when OpenLaunchDeck exits")
        self.stop_on_exit.setChecked(settings.soundboard_stop_sounds_on_exit)

        self.voice_output_device = QComboBox()
        self.voice_output_device.addItem("Not configured", "")
        self._add_device_items(self.voice_output_device, devices)
        self._select_saved_device(self.voice_output_device, settings.soundboard_voice_chat_output_device)
        input_devices = list_input_devices()
        self.voice_mic_device = QComboBox()
        self.voice_mic_device.addItem("System default microphone", "")
        self._add_device_items(self.voice_mic_device, input_devices, "Audio input")
        self._select_saved_device(self.voice_mic_device, settings.soundboard_voice_route_microphone_device)
        self.voice_mic_enabled = QCheckBox("Mix my microphone into the voice-chat route")
        self.voice_mic_enabled.setChecked(settings.soundboard_voice_route_microphone_enabled)
        self.voice_mic_volume = PercentControl(settings.soundboard_voice_route_microphone_volume)
        self.voice_route_exclusive = QCheckBox("Keep my voice out of screen-share audio")
        self.voice_route_exclusive.setChecked(settings.soundboard_voice_route_exclusive)
        self.voice_route_exclusive.setToolTip(
            "Discord's screen share would otherwise pick up the microphone route and play your voice twice. "
            "OpenLaunchDeck takes exclusive control of the voice route device to prevent that, "
            "and falls back automatically if Windows doesn't allow it."
        )
        self.monitor_voice_routes = QCheckBox("Let me hear sounds that are routed to voice chat")
        self.monitor_voice_routes.setChecked(settings.soundboard_monitor_voice_chat)

        hidden_parts = []
        if hidden_duplicate_count(devices):
            hidden_parts.append("duplicate Windows endpoints")
        if hidden_advanced_output_count():
            hidden_parts.append("advanced mixer buses")
        device_note = QLabel(
            "The device list hides " + " and ".join(hidden_parts) + "." if hidden_parts else "Only usable playback endpoints are shown."
        )
        device_note.setObjectName("MutedText")
        device_note.setWordWrap(True)

        self.tabs.addTab(
            self._tab(
                self._section(
                    "Playback",
                    "Per-pad volume is multiplied by this global level. Playback remains non-blocking.",
                    [("Output", self.output_device), ("Global volume", self.global_volume), ("", self.stop_on_exit), ("", device_note)],
                ),
                self._section(
                    "Voice Chat Route",
                    "Configure this only when sounds should also be heard by Discord or an in-game voice chat.",
                    [
                        ("Route output", self.voice_output_device),
                        ("Microphone", self.voice_mic_device),
                        ("", self.voice_mic_enabled),
                        ("", self.voice_route_exclusive),
                        ("Microphone level", self.voice_mic_volume),
                        ("", self.monitor_voice_routes),
                    ],
                ),
            ),
            "Soundboard",
        )

    def _build_idle_animation_tab(self, settings) -> None:
        self.idle_enabled = QCheckBox("Play an animation on the Launchpad when the pads sit unused")
        self.idle_enabled.setChecked(settings.idle_animation_enabled)
        self.idle_timeout = QSpinBox()
        self.idle_timeout.setRange(3, 3600)
        self.idle_timeout.setSuffix(" seconds")
        self.idle_timeout.setValue(settings.idle_animation_timeout_seconds)
        self.idle_timeout.setMaximumWidth(200)
        self.idle_timeout.setToolTip("How long the pads must go unused before the animation starts.")
        self.idle_wake_runs_action = QCheckBox("Run the pad's action when a press stops the animation")
        self.idle_wake_runs_action.setChecked(settings.idle_animation_wake_press_runs_action)
        self.idle_wake_runs_action.setToolTip(
            "Turn this off if you want the first press to only wake the pads, like a screensaver."
        )

        self.idle_animation = QComboBox()
        self.idle_animation.setObjectName("IdleAnimationPicker")
        self._fill_idle_animation_choices(settings.idle_animation_id)
        self.idle_shuffle = QCheckBox("Pick a different animation each time")
        self.idle_shuffle.setChecked(settings.idle_animation_shuffle)
        self.idle_speed = PercentControl(settings.idle_animation_speed, minimum=25, maximum=300)
        self.idle_brightness = PercentControl(settings.idle_animation_brightness, minimum=10, maximum=100)
        self.idle_description = QLabel()
        self.idle_description.setObjectName("SettingsDescription")
        self.idle_description.setWordWrap(True)

        self.idle_preview = AnimationPreview(pad_size=16, gap=4)
        self.idle_preview_status = QLabel()
        self.idle_preview_status.setObjectName("SettingsDescription")
        self.idle_preview_status.setWordWrap(True)
        preview_on_device = QPushButton("Preview on Launchpad")
        preview_on_device.setObjectName("SecondaryButton")
        preview_on_device.setToolTip("Plays the selected animation on the Launchpad for 8 seconds. Press any pad to stop.")
        preview_on_device.clicked.connect(self._preview_idle_on_device)
        preview_panel = QWidget()
        preview_layout = QHBoxLayout(preview_panel)
        preview_layout.setContentsMargins(0, 4, 0, 0)
        preview_layout.setSpacing(16)
        preview_layout.addWidget(self.idle_preview, 0, Qt.AlignmentFlag.AlignTop)
        preview_side = QVBoxLayout()
        preview_side.setSpacing(8)
        preview_side.addWidget(self.idle_description)
        manage = QPushButton("Browse, make, and share animations…")
        manage.setObjectName("SecondaryButton")
        manage.clicked.connect(self._open_animation_library)
        preview_buttons = QHBoxLayout()
        preview_buttons.setSpacing(8)
        preview_buttons.addWidget(preview_on_device)
        preview_buttons.addWidget(manage)
        preview_buttons.addStretch(1)
        preview_side.addLayout(preview_buttons)
        preview_side.addWidget(self.idle_preview_status)
        preview_side.addStretch(1)
        preview_layout.addLayout(preview_side, 1)

        self.idle_animation.currentIndexChanged.connect(self._update_idle_preview)
        self.idle_shuffle.toggled.connect(self._update_idle_preview)
        self.idle_speed.spin.valueChanged.connect(self.idle_preview.set_speed)
        self.idle_brightness.spin.valueChanged.connect(self.idle_preview.set_brightness)
        self.idle_preview.set_speed(self.idle_speed.value())
        self.idle_preview.set_brightness(self.idle_brightness.value())
        self._update_idle_preview()

        self.tabs.addTab(
            self._tab(
                self._section(
                    "Idle Animation",
                    "After the pads go unused for a while, the Launchpad plays an animation. Any pad or button press brings your deck back instantly.",
                    [("", self.idle_enabled), ("Start after", self.idle_timeout), ("", self.idle_wake_runs_action)],
                ),
                self._section(
                    "Animation",
                    "Choose one of the built-in animations or one you made or imported. Speed and brightness apply to every animation.",
                    [
                        ("Animation", self.idle_animation),
                        ("", self.idle_shuffle),
                        ("Speed", self.idle_speed),
                        ("Brightness", self.idle_brightness),
                        ("Preview", preview_panel),
                    ],
                ),
            ),
            "Idle Animation",
        )

    def _fill_idle_animation_choices(self, selected_id: str) -> None:
        self.idle_animation.blockSignals(True)
        self.idle_animation.clear()
        user_animations = self.animation_library.user_animations()
        for animation in self.animation_library.all():
            if not getattr(animation, "builtin", False):
                continue
            self.idle_animation.addItem(animation.name, animation.id)
        if user_animations:
            self.idle_animation.insertSeparator(self.idle_animation.count())
            for animation in user_animations:
                label = f"{animation.name} by {animation.author}" if animation.author else animation.name
                self.idle_animation.addItem(label, animation.id)
        index = self.idle_animation.findData(selected_id)
        self.idle_animation.setCurrentIndex(index if index >= 0 else 0)
        self.idle_animation.blockSignals(False)

    def _open_animation_library(self) -> None:
        from .animation_library_dialog import AnimationLibraryDialog

        # The library saves its own choices; carry unsaved edits from this tab across.
        self.settings_service.update(
            idle_animation_enabled=self.idle_enabled.isChecked(),
            idle_animation_id=str(self.idle_animation.currentData() or "rainbow_wave"),
            idle_animation_shuffle=self.idle_shuffle.isChecked(),
        )
        AnimationLibraryDialog(self.animation_library, self.settings_service, self.idle_player, self).exec()
        settings = self.settings_service.settings
        self.idle_enabled.setChecked(settings.idle_animation_enabled)
        self.idle_shuffle.setChecked(settings.idle_animation_shuffle)
        self._fill_idle_animation_choices(settings.idle_animation_id)
        self._update_idle_preview()

    def _update_idle_preview(self) -> None:
        shuffle = self.idle_shuffle.isChecked()
        self.idle_animation.setEnabled(not shuffle)
        animation = self.animation_library.get(str(self.idle_animation.currentData() or ""))
        self.idle_preview.set_animation(animation)
        if shuffle:
            self.idle_description.setText("A random animation plays each time the pads go idle. Preview shows the selected one.")
        elif animation is not None:
            self.idle_description.setText(animation.description or "No description.")
        else:
            self.idle_description.setText("")

    def _preview_idle_on_device(self) -> None:
        animation_id = str(self.idle_animation.currentData() or "")
        player = self.idle_player
        if player is None:
            self.idle_preview_status.setText("Previewing on the Launchpad isn't available here.")
            return
        started = player.preview(
            animation_id,
            seconds=8,
            speed=self.idle_speed.value(),
            brightness=self.idle_brightness.value(),
        )
        self.idle_preview_status.setText(
            "Playing on your Launchpad for 8 seconds. Press any pad to stop."
            if started
            else "Connect your Launchpad to preview on it."
        )

    def _build_app_tab(self, settings) -> None:
        self.start_minimized = QCheckBox("Start in the system tray")
        self.start_minimized.setChecked(settings.start_minimized)
        self.minimize_to_tray = QCheckBox("Keep running in the tray when the window closes")
        self.minimize_to_tray.setChecked(settings.minimize_to_tray)
        self.launch_at_startup = QCheckBox("Launch when I sign in to Windows")
        self.launch_at_startup.setChecked(settings.launch_at_startup)
        self._startup_setting_available = self.startup_service is not None and self.startup_service.is_available()
        if not self._startup_setting_available:
            self.launch_at_startup.setEnabled(False)
            self.launch_at_startup.setToolTip("This setting is available in the installed Windows app.")
        self.autosave = QCheckBox("Autosave profile changes")
        self.autosave.setChecked(settings.profile_autosave)
        self.backups = QCheckBox("Create automatic profile backups")
        self.backups.setChecked(settings.backup_profiles_automatically)
        self.check_updates = QCheckBox("Check for updates after startup")
        self.check_updates.setChecked(settings.check_updates_on_startup)
        self.update_channel = QComboBox()
        self.update_channel.addItem("Stable releases", "stable")
        self.update_channel.addItem("Beta releases", "beta")
        self.update_channel.setCurrentIndex(max(0, self.update_channel.findData(settings.update_channel)))
        config_button = QPushButton("Open data folder")
        config_button.setObjectName("SecondaryButton")
        config_button.setToolTip(str(APP_DATA_DIR))
        config_button.clicked.connect(lambda: self.parent().open_folder(APP_DATA_DIR) if self.parent() else None)
        self.tabs.addTab(
            self._tab(
                self._section(
                    "Windows",
                    "OpenLaunchDeck uses a single-instance startup path so other layout tools can safely launch it too.",
                    [("", self.launch_at_startup), ("", self.start_minimized), ("", self.minimize_to_tray)],
                ),
                self._section(
                    "Profiles and Data",
                    "Profiles, settings, mappings, logs, and downloaded sounds stay under AppData.",
                    [("", self.autosave), ("", self.backups), ("User data", config_button)],
                ),
                self._section(
                    "Updates",
                    "Update checks run in the background. Installers are never installed silently.",
                    [("", self.check_updates), ("Channel", self.update_channel)],
                ),
            ),
            "App",
        )

    def _build_advanced_tab(self, settings) -> None:
        self.update_url = QLineEdit(settings.update_manifest_url)
        self.update_url.setPlaceholderText("Use the release channel default")
        self.performance_logging = QCheckBox("Record detailed latency measurements")
        self.performance_logging.setChecked(settings.enable_performance_logging)
        self.native_acceleration = QCheckBox("Use optional native helpers when available")
        self.native_acceleration.setChecked(settings.use_native_acceleration)
        self.tabs.addTab(
            self._tab(
                self._section(
                    "Diagnostics",
                    "Performance logging is quiet by default. Enable it only while investigating latency.",
                    [("", self.performance_logging), ("", self.native_acceleration)],
                ),
                self._section(
                    "Update Source",
                    "Leave this empty for normal releases. A custom manifest is intended for local testing or managed deployments.",
                    [("Manifest URL", self.update_url)],
                ),
            ),
            "Advanced",
        )

    def _tab(self, *sections: QWidget) -> QScrollArea:
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(14, 14, 14, 14)
        content_layout.setSpacing(12)
        for section in sections:
            content_layout.addWidget(section)
        content_layout.addStretch(1)
        scroll = QScrollArea()
        scroll.setObjectName("SettingsScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(content)
        return scroll

    @staticmethod
    def _section(title: str, description: str, rows: list[tuple[str, QWidget]]) -> QFrame:
        frame = QFrame()
        frame.setObjectName("SettingsSection")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(8)
        heading = QLabel(title)
        heading.setObjectName("SectionTitle")
        layout.addWidget(heading)
        note = QLabel(description)
        note.setObjectName("SettingsDescription")
        note.setWordWrap(True)
        layout.addWidget(note)
        form = QFormLayout()
        form.setContentsMargins(0, 4, 0, 0)
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(10)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        for label, widget in rows:
            form.addRow(label, widget)
        layout.addLayout(form)
        return frame

    @staticmethod
    def _editable_port_combo(ports: list[str], saved: str, automatic_label: str) -> QComboBox:
        combo = QComboBox()
        combo.setEditable(True)
        combo.addItem(automatic_label, "")
        for port in ports:
            combo.addItem(port, port)
        if saved:
            index = combo.findText(saved)
            if index < 0:
                combo.addItem(saved, saved)
                index = combo.findText(saved)
            combo.setCurrentIndex(index)
        else:
            combo.setCurrentIndex(0)
        return combo

    def _refit_parent_grid(self) -> None:
        # Styles change pad shape and the Hardware chassis, so the main grid re-measures.
        refit = getattr(self.parent(), "_schedule_grid_fit", None)
        if callable(refit):
            refit()

    def _preview_theme(self) -> None:
        self._update_theme_preview()
        apply_theme(str(self.theme.currentData() or "midnight"), self)
        self._refit_parent_grid()

    def _update_theme_preview(self) -> None:
        definition = theme_definition(str(self.theme.currentData() or "midnight"))
        self.theme_description.setText(definition.description)
        for label, color in zip(self._swatch_labels, definition.swatches, strict=True):
            label.setStyleSheet(f"background: {color}; border: 1px solid {definition.colors['BORDER_STRONG']}; border-radius: 5px;")

    def reject(self) -> None:
        apply_theme(self._original_theme, self)
        self._refit_parent_grid()
        super().reject()

    def accept(self) -> None:
        launch_at_startup = self.settings_service.settings.launch_at_startup
        if self._startup_setting_available:
            launch_at_startup = self.launch_at_startup.isChecked()
            if not self.startup_service.set_enabled(launch_at_startup):
                QMessageBox.warning(
                    self,
                    "Startup setting not changed",
                    "OpenLaunchDeck could not update the Windows startup entry. Check the log for details.",
                )
                return

        self.settings_service.update(
            theme=self.theme.currentData(),
            grid_density=self.grid_density.currentData(),
            deck_view=self.deck_view.isChecked(),
            auto_connect=self.auto_connect.isChecked(),
            start_minimized=self.start_minimized.isChecked(),
            minimize_to_tray=self.minimize_to_tray.isChecked(),
            launch_at_startup=launch_at_startup,
            midi_input_port=str(self.midi_input.currentData() or self.midi_input.currentText()).strip(),
            midi_output_port=str(self.midi_output.currentData() or self.midi_output.currentText()).strip(),
            midi_debug_logging=self.midi_debug.isChecked(),
            launchpad_control_bindings=self.auxiliary_bindings.bindings(),
            profile_autosave=self.autosave.isChecked(),
            backup_profiles_automatically=self.backups.isChecked(),
            soundboard_default_output_device=str(self.output_device.currentData() or ""),
            soundboard_voice_chat_output_device=str(self.voice_output_device.currentData() or ""),
            soundboard_voice_route_microphone_device=str(self.voice_mic_device.currentData() or ""),
            soundboard_voice_route_microphone_enabled=self.voice_mic_enabled.isChecked(),
            soundboard_voice_route_exclusive=self.voice_route_exclusive.isChecked(),
            soundboard_voice_route_microphone_volume=self.voice_mic_volume.value(),
            soundboard_monitor_voice_chat=self.monitor_voice_routes.isChecked(),
            soundboard_global_volume=self.global_volume.value(),
            soundboard_stop_sounds_on_exit=self.stop_on_exit.isChecked(),
            check_updates_on_startup=self.check_updates.isChecked(),
            update_channel=self.update_channel.currentData(),
            update_manifest_url=self.update_url.text().strip(),
            enable_performance_logging=self.performance_logging.isChecked(),
            use_native_acceleration=self.native_acceleration.isChecked(),
            idle_animation_enabled=self.idle_enabled.isChecked(),
            idle_animation_timeout_seconds=self.idle_timeout.value(),
            idle_animation_id=str(self.idle_animation.currentData() or "rainbow_wave"),
            idle_animation_shuffle=self.idle_shuffle.isChecked(),
            idle_animation_speed=self.idle_speed.value(),
            idle_animation_brightness=self.idle_brightness.value(),
            idle_animation_wake_press_runs_action=self.idle_wake_runs_action.isChecked(),
        )
        super().accept()

    def _add_device_items(self, combo: QComboBox, devices: list[dict[str, str | int]], fallback_name: str = "Audio output") -> None:
        for device in devices:
            combo.addItem(str(device.get("display_name") or device.get("description") or fallback_name), str(device.get("id") or ""))

    @staticmethod
    def _select_saved_device(combo: QComboBox, device_id: str) -> None:
        if not device_id:
            combo.setCurrentIndex(0)
            return
        index = combo.findData(device_id)
        if index < 0:
            combo.addItem("Saved device not currently available", device_id)
            index = combo.findData(device_id)
        combo.setCurrentIndex(max(0, index))
