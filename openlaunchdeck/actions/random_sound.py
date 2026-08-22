from __future__ import annotations

import os
import random
from pathlib import Path

from .base import ActionResult, BaseAction

SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".ogg"}
MAX_SCANNED_ENTRIES = 50_000


class RandomSoundAction(BaseAction):
    type_name = "random_sound"
    display_name = "Random Sound From Folder"
    description = "Choose a random WAV, MP3, or OGG file from a local folder and play it."
    config_fields = [
        {
            "name": "folder_path",
            "label": "Sound Folder",
            "type": "path",
            "placeholder": "Choose a folder containing sounds",
        },
        {"name": "include_subfolders", "label": "Include Subfolders", "type": "bool", "default": False},
        {"name": "volume", "label": "Clip Volume", "type": "number", "min": 0, "max": 100, "default": 80, "suffix": "%"},
        {"name": "route_to_voice_chat", "label": "Also Send To Voice Chat", "type": "bool", "default": False},
        {"name": "loop", "label": "Loop Until Stopped", "type": "bool", "default": False},
        {
            "name": "behavior_when_already_playing",
            "label": "When Pressed Again",
            "type": "choice",
            "choices": ["restart", "overlap", "ignore", "toggle_stop"],
            "default": "restart",
        },
        {"name": "active_color", "label": "Playing Color", "type": "color", "default": "cyan"},
        {"name": "stop_on_page_change", "label": "Stop When Page Changes", "type": "bool", "default": False},
    ]
    blocking = True

    def validate(self, config: dict) -> list[str]:
        if not str(config.get("folder_path") or "").strip():
            return ["Choose a sound folder."]
        behavior = str(config.get("behavior_when_already_playing") or "restart")
        if behavior not in {"restart", "overlap", "ignore", "toggle_stop"}:
            return ["Choose a valid behavior for repeated presses."]
        return []

    def execute(self, context, config: dict) -> ActionResult:
        folder = Path(str(config.get("folder_path") or "").strip().strip('"')).expanduser()
        source_page_id = (
            context.profile_service.current_page_id
            if context.profile_service is not None
            else context.current_page.id
        )
        if not folder.exists() or not folder.is_dir():
            return ActionResult.fail(f"Sound folder does not exist: {folder}")
        try:
            selected = _choose_sound(folder, bool(config.get("include_subfolders", False)))
        except OSError as exc:
            return ActionResult.fail(f"Could not read the sound folder: {exc}")
        if selected is None:
            return ActionResult.fail("No supported WAV, MP3, or OGG files were found in the folder.")
        if (
            bool(config.get("stop_on_page_change", False))
            and context.profile_service is not None
            and context.profile_service.current_page_id != source_page_id
        ):
            return ActionResult.fail("The page changed before the sound could start.")
        if context.action_executor is None:
            return ActionResult.fail("Action dispatcher is unavailable.")
        sound_config = {
            "file_path": str(selected),
            "volume": config.get("volume", 80),
            "route_to_voice_chat": bool(config.get("route_to_voice_chat", False)),
            "loop": bool(config.get("loop", False)),
            "behavior_when_already_playing": config.get("behavior_when_already_playing", "restart"),
            "active_color": config.get("active_color", "cyan"),
            "stop_on_page_change": bool(config.get("stop_on_page_change", False)),
            "_page_id": source_page_id,
        }
        return context.action_executor("play_sound", context, sound_config)


def _choose_sound(folder: Path, recursive: bool) -> Path | None:
    selected: Path | None = None
    match_count = 0
    scanned = 0
    if recursive:
        pending = [folder]

        def paths():
            nonlocal scanned
            while pending and scanned < MAX_SCANNED_ENTRIES:
                current = pending.pop()
                with os.scandir(current) as entries:
                    for entry in entries:
                        scanned += 1
                        if scanned > MAX_SCANNED_ENTRIES:
                            return
                        if entry.is_dir(follow_symlinks=False):
                            pending.append(Path(entry.path))
                        elif entry.is_file(follow_symlinks=False):
                            yield Path(entry.path)
    else:
        def paths():
            nonlocal scanned
            with os.scandir(folder) as entries:
                for entry in entries:
                    scanned += 1
                    if scanned > MAX_SCANNED_ENTRIES:
                        return
                    if entry.is_file(follow_symlinks=False):
                        yield Path(entry.path)

    for path in paths():
        if path.suffix.casefold() not in SUPPORTED_AUDIO_EXTENSIONS:
            continue
        match_count += 1
        if random.randrange(match_count) == 0:
            selected = path
    return selected
