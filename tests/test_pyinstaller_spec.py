from pathlib import Path


def test_pyinstaller_spec_includes_dynamic_action_dependencies():
    spec_text = Path("openlaunchdeck.spec").read_text(encoding="utf-8")

    assert '"websocket"' in spec_text


def test_windows_package_excludes_unused_desktop_automation_stack():
    spec_text = Path("openlaunchdeck.spec").read_text(encoding="utf-8")

    for module in ("tkinter", "_tkinter", "pyautogui", "mouseinfo", "pyscreeze", "PIL", "Xlib"):
        assert f'"{module}"' in spec_text
