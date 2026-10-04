from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from ..constants import (
    DEFAULT_LAUNCHPAD_CONTROL_BINDINGS,
    LAUNCHPAD_AUXILIARY_CONTROL_LABELS,
    LAUNCHPAD_CONTROL_BINDING_LABELS,
)


BOOL_FIELDS = {
    "idle_animation_enabled",
    "idle_animation_shuffle",
    "idle_animation_wake_press_runs_action",
    "auto_connect",
    "start_minimized",
    "minimize_to_tray",
    "launch_at_startup",
    "midi_debug_logging",
    "profile_autosave",
    "backup_profiles_automatically",
    "soundboard_monitor_voice_chat",
    "soundboard_voice_route_microphone_enabled",
    "soundboard_stop_sounds_on_exit",
    "check_updates_on_startup",
    "enable_performance_logging",
    "use_native_acceleration",
    "first_run_complete",
    "deck_view",
}
# Whole-number settings kept inside (minimum, maximum).
RANGED_INT_FIELDS = {
    "idle_animation_timeout_seconds": (3, 3600),
    "idle_animation_speed": (25, 300),
    "idle_animation_brightness": (10, 100),
}
PERCENT_FIELDS = {
    "soundboard_voice_route_microphone_volume",
    "soundboard_global_volume",
}
THEME_KEYS = {
    "nebula",
    "studio",
    "hardware",
    "midnight",
    "oled_black",
    "galaxy_oled",
    "arctic_white",
    "graphite",
    "broadcast",
    "high_contrast",
    "system",
}


def _coerce_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off", ""}:
            return False
    return default


def _coerce_ranged_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    if isinstance(value, bool):
        return default
    try:
        number = int(float(value))
    except (TypeError, ValueError, OverflowError):
        return default
    return max(minimum, min(maximum, number))


def _coerce_percent(value: Any, default: int) -> int:
    try:
        return max(0, min(100, int(value)))
    except (TypeError, ValueError):
        return default


@dataclass(slots=True)
class Settings:
    theme: str = "nebula"
    grid_density: str = "comfortable"
    deck_view: bool = False
    auto_connect: bool = True
    start_minimized: bool = False
    minimize_to_tray: bool = True
    launch_at_startup: bool = False
    default_profile: str = "blank"
    midi_input_port: str = ""
    midi_output_port: str = ""
    midi_debug_logging: bool = False
    launchpad_control_bindings: dict[str, str] = field(
        default_factory=lambda: dict(DEFAULT_LAUNCHPAD_CONTROL_BINDINGS)
    )
    profile_autosave: bool = True
    backup_profiles_automatically: bool = True
    soundboard_default_output_device: str = ""
    soundboard_voice_chat_output_device: str = ""
    soundboard_monitor_voice_chat: bool = True
    soundboard_voice_route_microphone_enabled: bool = False
    soundboard_voice_route_microphone_device: str = ""
    soundboard_voice_route_microphone_volume: int = 100
    soundboard_global_volume: int = 100
    soundboard_stop_sounds_on_exit: bool = True
    check_updates_on_startup: bool = False
    update_channel: str = "stable"
    update_manifest_url: str = ""
    enable_performance_logging: bool = False
    use_native_acceleration: bool = False
    first_run_complete: bool = False
    idle_animation_enabled: bool = False
    idle_animation_timeout_seconds: int = 15
    idle_animation_id: str = "rainbow_wave"
    idle_animation_shuffle: bool = False
    idle_animation_speed: int = 100
    idle_animation_brightness: int = 100
    idle_animation_wake_press_runs_action: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "Settings":
        if not isinstance(data, dict):
            return cls()
        defaults = cls()
        allowed = set(cls.__dataclass_fields__)
        values: dict[str, Any] = {}
        for key, value in data.items():
            if key not in allowed:
                continue
            default = getattr(defaults, key)
            if key in BOOL_FIELDS:
                values[key] = _coerce_bool(value, default)
            elif key in PERCENT_FIELDS:
                values[key] = _coerce_percent(value, default)
            elif key in RANGED_INT_FIELDS:
                values[key] = _coerce_ranged_int(value, default, *RANGED_INT_FIELDS[key])
            elif key == "launchpad_control_bindings":
                values[key] = _coerce_launchpad_bindings(value)
            elif isinstance(default, str):
                values[key] = value if isinstance(value, str) else default
            else:
                values[key] = value
        settings = cls(**values)
        settings.theme = {"dark": "midnight", "light": "arctic_white"}.get(settings.theme, settings.theme)
        if settings.theme not in THEME_KEYS:
            settings.theme = defaults.theme
        if settings.grid_density not in {"compact", "comfortable", "large"}:
            settings.grid_density = "comfortable"
        if settings.update_channel not in {"stable", "beta"}:
            settings.update_channel = "stable"
        settings.launchpad_control_bindings = _coerce_launchpad_bindings(settings.launchpad_control_bindings)
        settings.idle_animation_id = settings.idle_animation_id.strip()[:80] or defaults.idle_animation_id
        return settings

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _coerce_launchpad_bindings(value: Any) -> dict[str, str]:
    bindings = dict(DEFAULT_LAUNCHPAD_CONTROL_BINDINGS)
    if not isinstance(value, dict):
        return bindings
    valid_bindings = set(LAUNCHPAD_CONTROL_BINDING_LABELS)
    for control_id in LAUNCHPAD_AUXILIARY_CONTROL_LABELS:
        binding = str(value.get(control_id) or "").strip()
        if binding in valid_bindings:
            bindings[control_id] = binding
    return bindings
