from __future__ import annotations

BUTTON_ROWS = "ABCDEFGH"
BUTTON_COLUMNS = range(1, 9)
BUTTON_IDS = [f"{row}{column}" for row in BUTTON_ROWS for column in BUTTON_COLUMNS]

LAUNCHPAD_AUXILIARY_CONTROL_LABELS: dict[str, str] = {
    "top_up": "Up Arrow",
    "top_down": "Down Arrow",
    "top_left": "Left Arrow",
    "top_right": "Right Arrow",
    "session": "Session",
    "drums": "Drums",
    "keys": "Keys",
    "user": "User",
    **{f"scene_{index}": f"Scene {index}" for index in range(1, 9)},
}

LAUNCHPAD_CONTROL_BINDING_LABELS: dict[str, str] = {
    "none": "Do nothing",
    "previous_page": "Previous page",
    "next_page": "Next page",
    "previous_profile": "Previous profile",
    "next_profile": "Next profile",
    "default_page": "Default page",
    "stop_all_sounds": "Stop all sounds",
    **{f"page_{index}": f"Open page {index}" for index in range(1, 9)},
}

DEFAULT_LAUNCHPAD_CONTROL_BINDINGS: dict[str, str] = {
    "top_up": "previous_profile",
    "top_down": "next_profile",
    "top_left": "previous_page",
    "top_right": "next_page",
    "session": "default_page",
    "drums": "none",
    "keys": "none",
    "user": "stop_all_sounds",
    **{f"scene_{index}": f"page_{index}" for index in range(1, 9)},
}

NAMED_COLORS: dict[str, str] = {
    "off": "#000000",
    "dim": "#20242c",
    "white": "#f5f7fb",
    "red": "#ef4444",
    "green": "#22c55e",
    "blue": "#3b82f6",
    "yellow": "#facc15",
    "purple": "#a855f7",
    "orange": "#f97316",
    "cyan": "#06b6d4",
    "pink": "#ec4899",
}

DEFAULT_BUTTON_COLOR = "blue"
DEFAULT_DANGEROUS_ARM_SECONDS = 5.0
DEFAULT_DANGEROUS_CONFIRM_DELAY_SECONDS = 0.35
DEFAULT_COMMAND_TIMEOUT_SECONDS = 30
DEFAULT_HTTP_TIMEOUT_SECONDS = 10
