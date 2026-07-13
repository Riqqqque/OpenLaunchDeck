from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

from ..models.button import ButtonConfig
from ..models.page import Page
from ..models.profile import Profile


@dataclass(slots=True)
class ActionContext:
    logger: logging.Logger
    current_profile: Profile
    current_page: Page
    button_id: str
    button_config: ButtonConfig
    audio_engine: Any = None
    profile_service: Any = None
    lighting_service: Any = None
    device_manager: Any = None
    settings_service: Any = None
    action_registry: Any = None
    action_executor: Callable[[str, "ActionContext", dict[str, Any]], Any] | None = None
    app: Any = None
