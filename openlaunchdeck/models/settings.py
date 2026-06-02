from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


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
        allowed = {field for field in cls.__dataclass_fields__}
        values = {key: value for key, value in data.items() if key in allowed}
        settings = cls(**values)
        settings.soundboard_global_volume = max(0, min(100, int(settings.soundboard_global_volume)))
        if settings.grid_density not in {"compact", "comfortable", "large"}:
            settings.grid_density = "comfortable"
        if settings.update_channel not in {"stable", "beta"}:
            settings.update_channel = "stable"
        return settings

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
