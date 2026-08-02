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

$pageFiles = @(
    Get-ChildItem -LiteralPath $sourceRoot -Filter "*.md" -File |
        Where-Object { $_.Name -ne "README.md" } |
        Sort-Object Name
)

$requiredPages = @("Home.md", "_Sidebar.md", "_Footer.md")
foreach ($requiredPage in $requiredPages) {
    if ($pageFiles.Name -notcontains $requiredPage) {
        throw "Required wiki page is missing: $requiredPage"
    }
}

foreach ($file in $pageFiles) {
    $text = Get-Content -LiteralPath $file.FullName -Raw
    $matches = [regex]::Matches(
        $text,
        '\]\((?!https?://|mailto:|#)([^):#]+\.md)(#[^)]+)?\)'
    )
    foreach ($match in $matches) {
        $relativeTarget = $match.Groups[1].Value.Replace('/', [IO.Path]::DirectorySeparatorChar)
        $targetPath = [IO.Path]::GetFullPath((Join-Path $file.DirectoryName $relativeTarget))
        if (-not $targetPath.StartsWith($sourceRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Wiki link leaves the source folder: $($file.Name) -> $relativeTarget"
        }
        if (-not (Test-Path -LiteralPath $targetPath -PathType Leaf)) {
            throw "Broken wiki link: $($file.Name) -> $relativeTarget"
        }
    }
}

$expectedNames = @($pageFiles.Name)
$stalePages = @(
    Get-ChildItem -LiteralPath $WikiPath -Filter "*.md" -File |
        Where-Object { $expectedNames -notcontains $_.Name }
)
foreach ($file in $stalePages) {
    Remove-Item -LiteralPath $file.FullName -Force
}

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

$remainingLinks = Select-String -Path (Join-Path $WikiPath "*.md") -Pattern '\]\((?!https?://|mailto:|#)[^)]+\.md' -CaseSensitive
if ($remainingLinks) {
    $first = $remainingLinks | Select-Object -First 1
    throw "A wiki link still points to a .md file: $($first.Path):$($first.LineNumber)"
}

Write-Host "Synced $($pageFiles.Count) user-facing wiki pages to $WikiPath"
if ($stalePages.Count) {
    Write-Host "Removed $($stalePages.Count) stale wiki page(s)"
}
