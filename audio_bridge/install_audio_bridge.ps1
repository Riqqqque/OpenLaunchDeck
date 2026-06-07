param(
    [string]$DriverDirectory = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $Root
if (!$DriverDirectory) {
    $DriverDirectory = Join-Path $RepoRoot "dist\audio_bridge"
}

function Assert-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if (!$principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "Run this script as Administrator to install the audio bridge driver."
    }
}

Assert-Administrator
if (!(Test-Path $DriverDirectory)) {
    throw "Driver package directory was not found: $DriverDirectory"
}

$inf = Get-ChildItem -LiteralPath $DriverDirectory -Filter "*OpenLaunchDeck*.inf" -ErrorAction SilentlyContinue | Select-Object -First 1
if (!$inf) {
    throw "OpenLaunchDeck Audio Bridge INF was not found in $DriverDirectory"
}

$catalog = Get-ChildItem -LiteralPath $DriverDirectory -Filter *.cat -ErrorAction SilentlyContinue | Select-Object -First 1
if (!$catalog) {
    throw "Driver catalog was not found. Refusing to install an unsigned package."
}

$signature = Get-AuthenticodeSignature -LiteralPath $catalog.FullName
if ($signature.Status -ne "Valid") {
    throw "Driver catalog signature is not valid: $($signature.Status). Refusing to install."
}

pnputil.exe /add-driver $inf.FullName /install
if ($LASTEXITCODE -ne 0) {
    throw "Driver installation failed with exit code $LASTEXITCODE"
}

Write-Host "OpenLaunchDeck Audio Bridge installation command completed."
