param(
    [string]$WikiPath = "$env:LOCALAPPDATA\Temp\OpenLaunchDeck.wiki",
    [string]$SourcePath = "docs\wiki"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$sourceRoot = Join-Path $repoRoot $SourcePath

if (-not (Test-Path -LiteralPath $sourceRoot)) {
    throw "Wiki source folder not found: $sourceRoot"
}

if (-not (Test-Path -LiteralPath $WikiPath)) {
    throw "Wiki repository not found: $WikiPath"
}

if (-not (Test-Path -LiteralPath (Join-Path $WikiPath ".git"))) {
    throw "Wiki path is not a git repository: $WikiPath"
}

$pageFiles = Get-ChildItem -LiteralPath $sourceRoot -Filter "*.md" -File
foreach ($file in $pageFiles) {
    Copy-Item -LiteralPath $file.FullName -Destination (Join-Path $WikiPath $file.Name) -Force
}

# GitHub Wiki pages should link to page names without the .md extension.
$wikiFiles = Get-ChildItem -LiteralPath $WikiPath -Filter "*.md" -File
foreach ($file in $wikiFiles) {
    $text = Get-Content -LiteralPath $file.FullName -Raw
    $text = [regex]::Replace(
        $text,
        '\]\((?!https?://|mailto:|#)([^):#]+)\.md(#[^)]+)?\)',
        {
            param($match)
            $target = $match.Groups[1].Value
            $anchor = $match.Groups[2].Value
            "]($target$anchor)"
        }
    )
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($file.FullName, $text, $utf8NoBom)
}

$remainingLinks = Select-String -Path (Join-Path $WikiPath "*.md") -Pattern '\]\([^)]+\.md' -CaseSensitive
if ($remainingLinks) {
    $first = $remainingLinks | Select-Object -First 1
    throw "A wiki link still points to a .md file: $($first.Path):$($first.LineNumber)"
}

Write-Host "Synced $($pageFiles.Count) wiki pages to $WikiPath"
