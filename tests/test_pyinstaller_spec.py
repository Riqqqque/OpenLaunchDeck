from pathlib import Path


def test_pyinstaller_spec_includes_dynamic_action_dependencies():
    spec_text = Path("openlaunchdeck.spec").read_text(encoding="utf-8")

    assert '"websocket"' in spec_text
