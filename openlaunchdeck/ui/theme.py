from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QWidget

from ..paths import THEMES_DIR


@dataclass(frozen=True, slots=True)
class ThemeDefinition:
    key: str
    name: str
    description: str
    colors: dict[str, str]

    @property
    def swatches(self) -> tuple[str, str, str, str]:
        return (
            self.colors["BACKGROUND"],
            self.colors["SURFACE"],
            self.colors["ACCENT"],
            self.colors["SECONDARY"],
        )


def _colors(**overrides: str) -> dict[str, str]:
    colors = {
        "BACKGROUND": "#090b0e",
        "SURFACE": "#11151a",
        "PANEL": "#151a20",
        "INPUT": "#0b0f13",
        "BORDER": "#29313b",
        "BORDER_STRONG": "#46515f",
        "TEXT": "#f3f6fa",
        "TEXT_STRONG": "#ffffff",
        "MUTED": "#94a0ae",
        "PLACEHOLDER": "#6f7a87",
        "ACCENT": "#2dd4bf",
        "ACCENT_HOVER": "#5eead4",
        "ACCENT_DARK": "#0f766e",
        "ACCENT_TEXT": "#031514",
        "SECONDARY": "#38bdf8",
        "HOVER": "#202731",
        "PRESSED": "#0d1116",
        "SUCCESS": "#4ade80",
        "WARNING": "#facc15",
        "ERROR": "#f87171",
        "MENU": "#11151a",
        "CHIP": "#1b222b",
        "SCROLL": "#46515f",
    }
    colors.update(overrides)
    return colors


THEMES: dict[str, ThemeDefinition] = {
    "midnight": ThemeDefinition(
        "midnight",
        "Midnight",
        "Balanced charcoal surfaces with a calm teal accent.",
        _colors(),
    ),
    "oled_black": ThemeDefinition(
        "oled_black",
        "OLED Black",
        "True black surfaces with crisp cyan controls for OLED displays.",
        _colors(
            BACKGROUND="#000000", SURFACE="#050505", PANEL="#090909", INPUT="#000000",
            BORDER="#242424", BORDER_STRONG="#4a4a4a", ACCENT="#00e5c7", ACCENT_HOVER="#50ffe8",
            ACCENT_DARK="#007d70", SECONDARY="#37bfff", HOVER="#151515", PRESSED="#030303",
            MENU="#080808", CHIP="#111111", SCROLL="#454545",
        ),
    ),
    "galaxy_oled": ThemeDefinition(
        "galaxy_oled",
        "Galaxy OLED",
        "Ink-black panels with violet controls and cyan status details.",
        _colors(
            BACKGROUND="#000000", SURFACE="#070811", PANEL="#0d0f1d", INPUT="#03040a",
            BORDER="#292b47", BORDER_STRONG="#55598a", ACCENT="#9b7bff", ACCENT_HOVER="#b7a2ff",
            ACCENT_DARK="#5b3ec4", ACCENT_TEXT="#090611", SECONDARY="#22d3ee", HOVER="#191b30",
            PRESSED="#060711", MENU="#0a0b15", CHIP="#15172a", SCROLL="#4a4e78",
        ),
    ),
    "arctic_white": ThemeDefinition(
        "arctic_white",
        "Arctic White",
        "Bright, low-glare surfaces with strong teal and blue accents.",
        _colors(
            BACKGROUND="#eef2f6", SURFACE="#ffffff", PANEL="#ffffff", INPUT="#f7f9fc",
            BORDER="#d5dce5", BORDER_STRONG="#9aa8ba", TEXT="#1d2939", TEXT_STRONG="#101828",
            MUTED="#667085", PLACEHOLDER="#98a2b3", ACCENT="#0f766e", ACCENT_HOVER="#0e8077",
            ACCENT_DARK="#115e59", ACCENT_TEXT="#ffffff", SECONDARY="#2563eb", HOVER="#e8eef5",
            PRESSED="#dce5ef", SUCCESS="#15803d", WARNING="#a16207", ERROR="#dc2626",
            MENU="#ffffff", CHIP="#edf2f7", SCROLL="#98a6b7",
        ),
    ),
    "graphite": ThemeDefinition(
        "graphite",
        "Graphite",
        "Neutral dark gray with an energetic lime highlight.",
        _colors(
            BACKGROUND="#0d0f0f", SURFACE="#151818", PANEL="#1a1e1d", INPUT="#0e1110",
            BORDER="#313735", BORDER_STRONG="#5a6560", ACCENT="#a3e635", ACCENT_HOVER="#bef264",
            ACCENT_DARK="#4d7c0f", ACCENT_TEXT="#111806", SECONDARY="#2dd4bf", HOVER="#252b29",
            PRESSED="#111413", MENU="#151817", CHIP="#222826", SCROLL="#53605b",
        ),
    ),
    "broadcast": ThemeDefinition(
        "broadcast",
        "Broadcast",
        "Studio charcoal with red command controls and cyan feedback.",
        _colors(
            BACKGROUND="#090a0c", SURFACE="#121417", PANEL="#181a1e", INPUT="#0c0e11",
            BORDER="#30343b", BORDER_STRONG="#59616d", ACCENT="#cf3340", ACCENT_HOVER="#d63d49",
            ACCENT_DARK="#941c29", ACCENT_TEXT="#ffffff", SECONDARY="#22d3ee", HOVER="#252930",
            PRESSED="#101215", MENU="#131519", CHIP="#20242a", SCROLL="#535c68",
        ),
    ),
    "high_contrast": ThemeDefinition(
        "high_contrast",
        "High Contrast",
        "Maximum separation with white text and yellow focus states.",
        _colors(
            BACKGROUND="#000000", SURFACE="#000000", PANEL="#080808", INPUT="#000000",
            BORDER="#bfc5cc", BORDER_STRONG="#ffffff", TEXT="#ffffff", TEXT_STRONG="#ffffff",
            MUTED="#d2d6da", PLACEHOLDER="#aab0b6", ACCENT="#ffe100", ACCENT_HOVER="#fff176",
            ACCENT_DARK="#d6b900", ACCENT_TEXT="#000000", SECONDARY="#00e5ff", HOVER="#202020",
            PRESSED="#080808", SUCCESS="#5cff74", WARNING="#ffe100", ERROR="#ff6262",
            MENU="#050505", CHIP="#171717", SCROLL="#ffffff",
        ),
    ),
}

THEME_ALIASES = {"dark": "midnight", "light": "arctic_white"}


def theme_definitions() -> tuple[ThemeDefinition, ...]:
    return tuple(THEMES.values())


def normalize_theme_key(theme: str | None) -> str:
    key = str(theme or "midnight").strip().casefold()
    key = THEME_ALIASES.get(key, key)
    return key if key in THEMES or key == "system" else "midnight"


def _resolved_theme_key(theme: str | None) -> str:
    key = normalize_theme_key(theme)
    if key != "system":
        return key
    app = QApplication.instance()
    if app is not None:
        try:
            if app.styleHints().colorScheme() == Qt.ColorScheme.Light:
                return "arctic_white"
        except (AttributeError, RuntimeError):
            pass
    return "midnight"


def theme_definition(theme: str | None) -> ThemeDefinition:
    return THEMES[_resolved_theme_key(theme)]


def load_theme(theme: str = "midnight") -> str:
    path = THEMES_DIR / "base.qss"
    if not path.exists():
        fallback = THEMES_DIR / "dark.qss"
        return fallback.read_text(encoding="utf-8") if fallback.exists() else ""
    stylesheet = path.read_text(encoding="utf-8")
    for token, value in theme_definition(theme).colors.items():
        stylesheet = stylesheet.replace(f"@{token}@", value)
    return stylesheet


def apply_theme(theme: str, target: QWidget | None = None) -> str:
    definition = theme_definition(theme)
    colors = definition.colors
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(colors["BACKGROUND"]))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(colors["TEXT"]))
    palette.setColor(QPalette.ColorRole.Base, QColor(colors["INPUT"]))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(colors["PANEL"]))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(colors["MENU"]))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(colors["TEXT"]))
    palette.setColor(QPalette.ColorRole.Text, QColor(colors["TEXT"]))
    palette.setColor(QPalette.ColorRole.Button, QColor(colors["SURFACE"]))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(colors["TEXT"]))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(colors["TEXT_STRONG"]))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(colors["PLACEHOLDER"]))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(colors["ACCENT"]))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(colors["ACCENT_TEXT"]))
    palette.setColor(QPalette.ColorRole.Mid, QColor(colors["BORDER"]))
    palette.setColor(QPalette.ColorRole.Light, QColor(colors["BORDER_STRONG"]))
    application = QApplication.instance()
    if application is not None:
        application.setPalette(palette)
        application.setStyleSheet(load_theme(theme))
    elif target is not None:
        target.setPalette(palette)
        target.setStyleSheet(load_theme(theme))
    return definition.key
