# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from openlaunchdeck.version import APP_NAME, __version__

block_cipher = None
root = Path.cwd()


def _version_tuple(version: str) -> tuple[int, int, int, int]:
    parts = [int(part) for part in version.split(".")]
    return tuple((parts + [0, 0, 0, 0])[:4])


version_parts = _version_tuple(__version__)
version_info_path = root / "build" / "openlaunchdeck_version_info.txt"
version_info_path.parent.mkdir(parents=True, exist_ok=True)
version_info_path.write_text(
    f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={version_parts},
    prodvers={version_parts},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [
          StringStruct('CompanyName', 'Rique'),
          StringStruct('FileDescription', '{APP_NAME}'),
          StringStruct('FileVersion', '{__version__}'),
          StringStruct('InternalName', '{APP_NAME}'),
          StringStruct('LegalCopyright', 'Copyright (c) Rique'),
          StringStruct('OriginalFilename', '{APP_NAME}.exe'),
          StringStruct('ProductName', '{APP_NAME}'),
          StringStruct('ProductVersion', '{__version__}')
        ]
      )
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
""",
    encoding="utf-8",
)

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
    version=str(version_info_path),
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
