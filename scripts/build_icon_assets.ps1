param()

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$IconDir = Join-Path $Root "openlaunchdeck\resources\icons"
$Source = Join-Path $IconDir "openlaunchdeck.svg"
$Magick = (Get-Command magick.exe -ErrorAction Stop).Source
$Sizes = @(16, 24, 32, 48, 64, 128, 256, 512)

foreach ($Size in $Sizes) {
    $Destination = Join-Path $IconDir "openlaunchdeck_$Size.png"
    & $Magick -background none -density 384 $Source -resize "${Size}x${Size}" -strip $Destination
    if ($LASTEXITCODE -ne 0) {
        throw "Could not render the $Size px icon."
    }
}

# ICO directory entries cannot describe frames larger than 256 px.
$PngFiles = $Sizes | Where-Object { $_ -le 256 } | ForEach-Object { Join-Path $IconDir "openlaunchdeck_$_.png" }
$Ico = Join-Path $IconDir "openlaunchdeck.ico"
& $Magick @PngFiles -strip $Ico
if ($LASTEXITCODE -ne 0) {
    throw "Could not build the Windows icon."
}

Write-Host "Icon assets updated in $IconDir"
