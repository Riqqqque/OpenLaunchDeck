param(
    [switch]$SkipInstaller,
    [switch]$BuildNative,
    [switch]$RequireInstaller,
    [switch]$UseCurrentPython,
    [switch]$SkipPipUpgrade,
    [switch]$SkipDependencyInstall,
    [switch]$SkipTests,
    [switch]$FastPackage,
    [switch]$BuildAudioBridge
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Invoke-Checked {
    param(
        [scriptblock]$Command,
        [string]$Name
    )
    $Timer = [System.Diagnostics.Stopwatch]::StartNew()
    Write-Host "==> $Name"
    & $Command
    $Timer.Stop()
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE"
    }
    Write-Host ("{0} completed in {1:n1}s" -f $Name, $Timer.Elapsed.TotalSeconds)
}

function New-PortableZip {
    param(
        [Parameter(Mandatory = $true)]
        [string]$SourceDirectory,
        [Parameter(Mandatory = $true)]
        [string]$DestinationPath,
        [switch]$Fast
    )
    if (Test-Path $DestinationPath) {
        Remove-Item -LiteralPath $DestinationPath -Force
    }
    if ($Fast) {
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [System.IO.Compression.ZipFile]::CreateFromDirectory(
            $SourceDirectory,
            $DestinationPath,
            [System.IO.Compression.CompressionLevel]::Fastest,
            $true
        )
    } else {
        Compress-Archive -Path $SourceDirectory -DestinationPath $DestinationPath -Force
    }
}

function Write-Checksum {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )
    if (!(Test-Path $Path)) {
        throw "Cannot write checksum because file was not found: $Path"
    }
    $Hash = Get-FileHash $Path -Algorithm SHA256
    $ChecksumPath = "$Path.sha256"
    "$($Hash.Hash.ToLower())  $(Split-Path $Path -Leaf)" | Set-Content -NoNewline -Encoding ascii $ChecksumPath
    Write-Host "Checksum:  $ChecksumPath"
    Write-Host "SHA256:    $($Hash.Hash.ToLower())"
}

if ($UseCurrentPython) {
    $PythonCommand = Get-Command python -ErrorAction Stop
    $Python = $PythonCommand.Source
} else {
    if (!(Test-Path ".venv")) {
        Invoke-Checked { python -m venv .venv } "Create virtual environment"
    }
    $Python = Join-Path $Root ".venv\Scripts\python.exe"
}

if (!$SkipPipUpgrade) {
    Invoke-Checked { & $Python -m pip install --upgrade pip } "Upgrade pip"
}
if (!$SkipDependencyInstall) {
    Invoke-Checked { & $Python -m pip install -r requirements.txt } "Install requirements"
}

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

if ($BuildAudioBridge) {
    Invoke-Checked { powershell -ExecutionPolicy Bypass -File audio_bridge\build_audio_bridge.ps1 } "Build audio bridge driver package"
}

if (!$SkipTests) {
    Invoke-Checked { & $Python -m pytest } "Run tests"
}
Invoke-Checked { & $Python -m PyInstaller openlaunchdeck.spec --noconfirm } "Build executable"

$ExePath = Join-Path $Root "dist\OpenLaunchDeck\OpenLaunchDeck.exe"
if (Test-Path $ExePath) {
    Write-Host "Executable: $ExePath"
}

$PortableZip = Join-Path $Root "dist\OpenLaunchDeck-$AppVersion-Windows.zip"
$ZipTimer = [System.Diagnostics.Stopwatch]::StartNew()
New-PortableZip -SourceDirectory (Join-Path $Root "dist\OpenLaunchDeck") -DestinationPath $PortableZip -Fast:$FastPackage
$ZipTimer.Stop()
Write-Host ("Create portable ZIP completed in {0:n1}s" -f $ZipTimer.Elapsed.TotalSeconds)
Write-Host "Portable ZIP: $PortableZip"
Write-Checksum -Path $PortableZip

if (!$SkipInstaller) {
    $Iscc = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($Iscc) {
        $InstallerArgs = @("/DMyAppName=$AppName", "/DMyAppVersion=$AppVersion")
        if ($FastPackage) {
            $InstallerArgs += "/DMyAppCompression=lzma2/fast"
            $InstallerArgs += "/DMyAppSolidCompression=no"
        }
        $InstallerArgs += "installer\openlaunchdeck.iss"
        Invoke-Checked { & $Iscc.Source @InstallerArgs } "Build installer"
        $Installer = Join-Path $Root "dist\installer\${AppName}Setup-$AppVersion.exe"
        if (Test-Path $Installer) {
            Write-Host "Installer: $Installer"
            Write-Checksum -Path $Installer
        } else {
            throw "Installer was not found at $Installer"
        }
    } elseif ($RequireInstaller) {
        throw "Inno Setup not found. Install Inno Setup or run without -RequireInstaller."
    } else {
        Write-Host "Inno Setup not found; installer build skipped."
    }
}
