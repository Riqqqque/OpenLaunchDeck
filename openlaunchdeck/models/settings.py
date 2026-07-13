from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


BOOL_FIELDS = {
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
}
PERCENT_FIELDS = {
    "soundboard_voice_route_microphone_volume",
    "soundboard_global_volume",
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


def _coerce_percent(value: Any, default: int) -> int:
    try:
        return max(0, min(100, int(value)))
    except (TypeError, ValueError):
        return default


@dataclass(slots=True)
class Settings:
    theme: str = "dark"
    grid_density: str = "comfortable"
    auto_connect: bool = True
    start_minimized: bool = False
    minimize_to_tray: bool = True
    launch_at_startup: bool = False
    default_profile: str = "blank"
    midi_input_port: str = ""
    midi_output_port: str = ""
    midi_debug_logging: bool = False
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
            elif isinstance(default, str):
                values[key] = value if isinstance(value, str) else default
            else:
                values[key] = value
        settings = cls(**values)
        if settings.theme not in {"dark", "light", "system"}:
            settings.theme = "dark"
        if settings.grid_density not in {"compact", "comfortable", "large"}:
            settings.grid_density = "comfortable"
        if settings.update_channel not in {"stable", "beta"}:
            settings.update_channel = "stable"
        return settings

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
