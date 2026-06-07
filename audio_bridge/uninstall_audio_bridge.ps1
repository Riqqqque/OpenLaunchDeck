param(
    [string]$PublishedName = ""
)

$ErrorActionPreference = "Stop"

function Assert-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if (!$principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "Run this script as Administrator to uninstall the audio bridge driver."
    }
}

Assert-Administrator
if (!$PublishedName) {
    $drivers = pnputil.exe /enum-drivers
    $lines = $drivers -split "`r?`n"
    $matches = @()
    for ($index = 0; $index -lt $lines.Length; $index++) {
        if ($lines[$index] -match "OpenLaunchDeck") {
            for ($back = $index; $back -ge [Math]::Max(0, $index - 8); $back--) {
                if ($lines[$back] -match "Published Name\s*:\s*(.+)$") {
                    $matches += $Matches[1].Trim()
                    break
                }
            }
        }
    }
    $matches = $matches | Sort-Object -Unique
    if ($matches.Count -eq 0) {
        throw "No OpenLaunchDeck Audio Bridge driver package was found."
    }
    if ($matches.Count -gt 1) {
        throw "Multiple OpenLaunchDeck driver packages found. Pass -PublishedName with one of: $($matches -join ', ')"
    }
    $PublishedName = $matches[0]
}

pnputil.exe /delete-driver $PublishedName /uninstall
if ($LASTEXITCODE -ne 0) {
    throw "Driver removal failed with exit code $LASTEXITCODE"
}

Write-Host "OpenLaunchDeck Audio Bridge removal command completed."
