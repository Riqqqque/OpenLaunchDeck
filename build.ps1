param(
    [switch]$SkipInstaller,
    [switch]$BuildNative
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Invoke-Checked {
    param(
        [scriptblock]$Command,
        [string]$Name
    )
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE"
    }
}

if (!(Test-Path ".venv")) {
    Invoke-Checked { python -m venv .venv } "Create virtual environment"
}

$Python = Join-Path $Root ".venv\Scripts\python.exe"
Invoke-Checked { & $Python -m pip install --upgrade pip } "Upgrade pip"
Invoke-Checked { & $Python -m pip install -r requirements.txt } "Install requirements"

$AppName = (& $Python -c "from openlaunchdeck.version import APP_NAME; print(APP_NAME)").Trim()
$AppVersion = (& $Python -c "from openlaunchdeck.version import __version__; print(__version__)").Trim()
if (!$AppName -or !$AppVersion) {
    throw "Could not read app name or version from openlaunchdeck/version.py"
}
Write-Host "Building $AppName $AppVersion"

if ($BuildNative) {
    if (Get-Command cargo -ErrorAction SilentlyContinue) {
        Invoke-Checked { & $Python -m pip install "maturin>=1.9" } "Install native build helper"
        Push-Location native
        try {
            Invoke-Checked { & $Python -m maturin develop --release } "Build native helper"
        } finally {
            Pop-Location
        }
    } else {
        throw "Rust toolchain not found. Install Rust or run build.ps1 without -BuildNative."
    }
}

Invoke-Checked { & $Python -m pytest } "Run tests"
Invoke-Checked { & $Python -m PyInstaller openlaunchdeck.spec --noconfirm } "Build executable"

$ExePath = Join-Path $Root "dist\OpenLaunchDeck\OpenLaunchDeck.exe"
if (Test-Path $ExePath) {
    Write-Host "Executable: $ExePath"
}

if (!$SkipInstaller) {
    $Iscc = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($Iscc) {
        Invoke-Checked { & $Iscc.Source "/DMyAppName=$AppName" "/DMyAppVersion=$AppVersion" "installer\openlaunchdeck.iss" } "Build installer"
        $Installer = Join-Path $Root "dist\installer\${AppName}Setup-$AppVersion.exe"
        if (Test-Path $Installer) {
            $Hash = Get-FileHash $Installer -Algorithm SHA256
            $ChecksumPath = "$Installer.sha256"
            "$($Hash.Hash.ToLower())  $(Split-Path $Installer -Leaf)" | Set-Content -NoNewline -Encoding ascii $ChecksumPath
            Write-Host "Installer: $Installer"
            Write-Host "Checksum:  $ChecksumPath"
            Write-Host "SHA256:    $($Hash.Hash.ToLower())"
        } else {
            throw "Installer was not found at $Installer"
        }
    } else {
        Write-Host "Inno Setup not found; installer build skipped."
    }
}
