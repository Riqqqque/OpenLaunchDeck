from __future__ import annotations

BUTTON_ROWS = "ABCDEFGH"
BUTTON_COLUMNS = range(1, 9)
BUTTON_IDS = [f"{row}{column}" for row in BUTTON_ROWS for column in BUTTON_COLUMNS]

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
