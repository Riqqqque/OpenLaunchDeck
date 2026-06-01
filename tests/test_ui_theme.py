from openlaunchdeck.ui.theme import load_theme


def test_system_theme_uses_styled_fallback():
    assert "QMainWindow" in load_theme("system")
    assert "QMainWindow" in load_theme("missing")
