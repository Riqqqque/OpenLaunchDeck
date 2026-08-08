from openlaunchdeck.ui.theme import load_theme, normalize_theme_key, theme_definitions


def _relative_luminance(color: str) -> float:
    channels = [int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [channel / 12.92 if channel <= 0.03928 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(first: str, second: str) -> float:
    first_luminance = _relative_luminance(first)
    second_luminance = _relative_luminance(second)
    return (max(first_luminance, second_luminance) + 0.05) / (min(first_luminance, second_luminance) + 0.05)


def test_system_theme_uses_styled_fallback():
    assert "QMainWindow" in load_theme("system")
    assert "QMainWindow" in load_theme("missing")


def test_public_themes_render_without_unresolved_tokens():
    definitions = theme_definitions()
    assert len(definitions) >= 7
    for definition in definitions:
        stylesheet = load_theme(definition.key)
        assert "@BACKGROUND@" not in stylesheet
        assert definition.colors["BACKGROUND"] in stylesheet


def test_legacy_theme_names_are_normalized():
    assert normalize_theme_key("dark") == "midnight"
    assert normalize_theme_key("light") == "arctic_white"


def test_public_themes_keep_readable_text_contrast():
    for definition in theme_definitions():
        colors = definition.colors
        assert _contrast(colors["TEXT"], colors["BACKGROUND"]) >= 4.5, definition.key
        assert _contrast(colors["MUTED"], colors["SURFACE"]) >= 4.5, definition.key
        assert _contrast(colors["ACCENT_TEXT"], colors["ACCENT"]) >= 4.5, definition.key
        assert _contrast(colors["ACCENT_TEXT"], colors["ACCENT_HOVER"]) >= 4.5, definition.key
