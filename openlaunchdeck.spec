# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

block_cipher = None
root = Path.cwd()
hidden_imports = [
    "PySide6.QtMultimedia",
    "mido.backends.rtmidi",
]
try:
    import openlaunchdeck_native  # noqa: F401
except Exception:
    pass
else:
    hidden_imports.append("openlaunchdeck_native")

a = Analysis(
    ["openlaunchdeck/main.py"],
    pathex=[str(root)],
    binaries=[],
    datas=[
        ("openlaunchdeck/resources", "openlaunchdeck/resources"),
        ("docs", "docs"),
        ("README.md", "."),
        ("LICENSE", "."),
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="OpenLaunchDeck",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(root / "openlaunchdeck" / "resources" / "icons" / "openlaunchdeck.ico"),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="OpenLaunchDeck",
)
