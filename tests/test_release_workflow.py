from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_release_workflow_uses_fast_packaging_flags():
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")

    assert "-UseCurrentPython" in workflow
    assert "-SkipDependencyInstall" in workflow
    assert "-SkipPipUpgrade" in workflow
    assert "-SkipTests" in workflow
    assert "-FastPackage" in workflow


def test_build_script_keeps_local_safety_defaults():
    script = (ROOT / "build.ps1").read_text(encoding="utf-8")

    assert "[switch]$SkipTests" in script
    assert "if (!$SkipTests)" in script
    assert "New-PortableZip" in script
    assert "MyAppCompression=lzma2/fast" in script


def test_windows_exe_metadata_and_icon_refresh_are_configured():
    spec = (ROOT / "openlaunchdeck.spec").read_text(encoding="utf-8")
    installer = (ROOT / "installer" / "openlaunchdeck.iss").read_text(encoding="utf-8")

    assert "StringStruct('ProductName', '{APP_NAME}')" in spec
    assert "StringStruct('ProductVersion', '{__version__}')" in spec
    assert "version=str(version_info_path)" in spec
    assert "ie4uinit.exe" in installer
    assert 'DestName: "OpenLaunchDeck.ico"' in installer
    assert 'IconFilename: "{app}\\OpenLaunchDeck.ico"' in installer
