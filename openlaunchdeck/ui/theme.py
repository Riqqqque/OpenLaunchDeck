from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QWidget

from ..paths import THEMES_DIR


@dataclass(frozen=True, slots=True)
class PadStyle:
    """How the 8x8 grid is drawn for a theme."""

    key: str
    radius_ratio: float
    aspect_limit: float | None = None
    chassis: bool = False


PAD_STYLES = {
    "classic": PadStyle("classic", 0.0),
    # Soft, rounded keycaps tinted by the pad color.
    "nebula": PadStyle("nebula", 0.2, aspect_limit=1.4),
    # Flat clip tiles with a solid color header, like a DAW session view.
    "studio": PadStyle("studio", 0.05, aspect_limit=1.8),
    # Square LED pads inside a drawing of the Launchpad itself.
    "hardware": PadStyle("hardware", 0.1, aspect_limit=1.12, chassis=True),
}

# Corner radius tiers used by base.qss, from controls up to cards.
SHAPES = {
    "classic": {"RADIUS_SM": "6px", "RADIUS": "7px", "RADIUS_LG": "12px", "FONT_FAMILY": "Segoe UI"},
    "nebula": {"RADIUS_SM": "10px", "RADIUS": "14px", "RADIUS_LG": "18px", "FONT_FAMILY": "Segoe UI Variable Text"},
    "studio": {"RADIUS_SM": "3px", "RADIUS": "4px", "RADIUS_LG": "6px", "FONT_FAMILY": "Segoe UI"},
    "hardware": {"RADIUS_SM": "6px", "RADIUS": "10px", "RADIUS_LG": "14px", "FONT_FAMILY": "Segoe UI"},
}


@dataclass(frozen=True, slots=True)
class ThemeDefinition:
    key: str
    name: str
    description: str
    colors: dict[str, str]
    style: str = "classic"

    @property
    def pad_style(self) -> PadStyle:
        return PAD_STYLES.get(self.style, PAD_STYLES["classic"])

    @property
    def tokens(self) -> dict[str, str]:
        return {**SHAPES.get(self.style, SHAPES["classic"]), **self.colors}

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
    "nebula": ThemeDefinition(
        "nebula",
        "Nebula",
        "Deep violet with pink and mint accents and soft, rounded keycaps. Matches the app icon.",
        _colors(
            BACKGROUND="#0d0720", SURFACE="#150c30", PANEL="#1b113d", INPUT="#100828",
            BORDER="#2b1f58", BORDER_STRONG="#4a3a8a", TEXT="#efeaff", TEXT_STRONG="#ffffff",
            MUTED="#a99fd8", PLACEHOLDER="#7f74b3", ACCENT="#ff5fa2", ACCENT_HOVER="#ff86b9",
            ACCENT_DARK="#b8336f", ACCENT_TEXT="#2a0618", SECONDARY="#7af5d8", HOVER="#241650",
            PRESSED="#0f0826", SUCCESS="#7af5d8", WARNING="#ffd36b", ERROR="#ff6b81",
            MENU="#170d36", CHIP="#241653", SCROLL="#4a3a8a",
        ),
        style="nebula",
    ),
    "studio": ThemeDefinition(
        "studio",
        "Studio",
        "Pro-audio charcoal with an orange accent and tight, flat clip tiles.",
        _colors(
            BACKGROUND="#121214", SURFACE="#19191c", PANEL="#202024", INPUT="#151517",
            BORDER="#2c2c31", BORDER_STRONG="#46464e", TEXT="#e7e7ea", TEXT_STRONG="#ffffff",
            MUTED="#9d9da6", PLACEHOLDER="#74747d", ACCENT="#ff7a1a", ACCENT_HOVER="#ff944a",
            ACCENT_DARK="#b4500a", ACCENT_TEXT="#1a0b00", SECONDARY="#5fb3a1", HOVER="#26262b",
            PRESSED="#101012", SUCCESS="#7ccf8a", WARNING="#f2c14e", ERROR="#ef6461",
            MENU="#1b1b1e", CHIP="#26262b", SCROLL="#46464e",
        ),
        style="studio",
    ),
    "hardware": ThemeDefinition(
        "hardware",
        "Hardware",
        "The grid drawn as the real Launchpad: square LED pads, round edge buttons, black chassis.",
        _colors(
            BACKGROUND="#0a0b0e", SURFACE="#121419", PANEL="#181a20", INPUT="#0e1014",
            BORDER="#252931", BORDER_STRONG="#3b404b", TEXT="#e7e9ee", TEXT_STRONG="#ffffff",
            MUTED="#9298a5", PLACEHOLDER="#6c7280", ACCENT="#22d3ee", ACCENT_HOVER="#5ee2f4",
            ACCENT_DARK="#0e7f91", ACCENT_TEXT="#021216", SECONDARY="#a78bfa", HOVER="#1f222a",
            PRESSED="#0c0d10", SUCCESS="#4ade80", WARNING="#facc15", ERROR="#f87171",
            MENU="#121419", CHIP="#1d2027", SCROLL="#3b404b",
        ),
        style="hardware",
    ),
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


_current_definition: ThemeDefinition | None = None


def current_theme() -> ThemeDefinition:
    """The theme last applied with apply_theme(); widgets read it while painting."""
    return _current_definition or THEMES["midnight"]


def current_pad_style() -> PadStyle:
    return current_theme().pad_style


def load_theme(theme: str = "midnight") -> str:
    path = THEMES_DIR / "base.qss"
    if not path.exists():
        fallback = THEMES_DIR / "dark.qss"
        return fallback.read_text(encoding="utf-8") if fallback.exists() else ""
    definition = theme_definition(theme)
    stylesheet = path.read_text(encoding="utf-8")
    style_sheet = THEMES_DIR / f"style_{definition.style}.qss"
    if style_sheet.exists():
        stylesheet += "\n" + style_sheet.read_text(encoding="utf-8")
    for token, value in definition.tokens.items():
        stylesheet = stylesheet.replace(f"@{token}@", value)
    return stylesheet


def apply_theme(theme: str, target: QWidget | None = None) -> str:
    global _current_definition
    definition = theme_definition(theme)
    _current_definition = definition
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
