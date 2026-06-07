param(
    [string]$SourceDirectory = "",
    [string]$OutputDirectory = "",
    [string]$Configuration = "Release",
    [string]$Platform = "x64"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $Root
if (!$SourceDirectory) {
    $SourceDirectory = Join-Path $Root "driver"
}
if (!$OutputDirectory) {
    $OutputDirectory = Join-Path $RepoRoot "dist\audio_bridge"
}

function Find-MSBuild {
    $command = Get-Command msbuild.exe -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }
    $candidates = @(
        "C:\Program Files\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\MSBuild.exe",
        "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\MSBuild.exe"
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }
    throw "MSBuild was not found. Install Visual Studio Build Tools with C++."
}

function Assert-WdkInstalled {
    $wdkProps = Get-ChildItem "C:\Program Files (x86)\Windows Kits\10" -Recurse -Filter Microsoft.DriverKit.props -ErrorAction SilentlyContinue | Select-Object -First 1
    if (!$wdkProps) {
        throw "Windows Driver Kit build targets were not found. Install the WDK before building OpenLaunchDeck Audio Bridge."
    }
}

Assert-WdkInstalled
$msbuild = Find-MSBuild
$solution = Get-ChildItem -LiteralPath $SourceDirectory -Filter *.sln -ErrorAction SilentlyContinue | Select-Object -First 1
if (!$solution) {
    throw "Bridge driver source was not found at $SourceDirectory. Add the OpenLaunchDeck Audio Bridge driver solution before building."
}

New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
& $msbuild $solution.FullName /m /restore "/p:Configuration=$Configuration" "/p:Platform=$Platform"
if ($LASTEXITCODE -ne 0) {
    throw "Audio bridge driver build failed with exit code $LASTEXITCODE"
}

$packages = Get-ChildItem -LiteralPath $SourceDirectory -Recurse -Include *.inf,*.cat,*.sys -ErrorAction SilentlyContinue
if (!$packages) {
    throw "No driver package files were produced."
}

foreach ($item in $packages) {
    Copy-Item -LiteralPath $item.FullName -Destination $OutputDirectory -Force
}

Copy-Item -LiteralPath (Join-Path $Root "bridge_manifest.json") -Destination $OutputDirectory -Force
Write-Host "OpenLaunchDeck Audio Bridge package copied to $OutputDirectory"
