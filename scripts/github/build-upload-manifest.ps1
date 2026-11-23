param(
    [int]$MediaBatchLimitMB = 350
)

$ErrorActionPreference = 'Stop'
$projectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$outputDir = Join-Path $projectRoot 'docs\github-upload'
$manifestPath = Join-Path $outputDir 'file-manifest.csv'
$summaryPath = Join-Path $outputDir 'batch-summary.csv'
$mediaLimitBytes = $MediaBatchLimitMB * 1MB

$excludedDirectoryParts = @(
    '\.git\',
    '\backend\.venv\',
    '\frontend\node_modules\',
    '\frontend\dist\',
    '\frontend\.vite-cache\',
    '\__pycache__\',
    '\.pytest_cache\',
    '\.mypy_cache\',
    '\.ruff_cache\'
)

$excludedFileNames = @('.env', 'file-manifest.csv', 'batch-summary.csv', 'Configs.db', 'Configs.db-shm', 'Configs.db-wal')
$excludedExtensions = @('.log', '.pyc')
$lfsExtensions = @('.mp3', '.mp4', '.wav', '.flac', '.m4a', '.mov', '.avi', '.bak', '.dump', '.sql')

function Get-RelativePath([string]$fullName) {
    $rootPrefix = $projectRoot.TrimEnd('\') + '\'
    $absolute = [System.IO.Path]::GetFullPath($fullName)
    if (-not $absolute.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path is outside project root: $absolute"
    }
    return $absolute.Substring($rootPrefix.Length).Replace('\', '/')
}

function Test-Excluded([System.IO.FileInfo]$file) {
    if ($excludedFileNames -contains $file.Name) { return $true }
    if ($excludedExtensions -contains $file.Extension.ToLowerInvariant()) { return $true }
    $normalized = '\' + (Get-RelativePath $file.FullName).Replace('/', '\')
    foreach ($part in $excludedDirectoryParts) {
        if ($normalized.IndexOf($part, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) { return $true }
    }
    return $false
}

$allFiles = Get-ChildItem -LiteralPath $projectRoot -Recurse -Force -File |
    Where-Object { -not (Test-Excluded $_) } |
    Sort-Object FullName

$rows = New-Object System.Collections.Generic.List[object]
$mediaFiles = New-Object System.Collections.Generic.List[System.IO.FileInfo]

foreach ($file in $allFiles) {
    $relative = Get-RelativePath $file.FullName
    $top = ($relative -split '/')[0]
    $batch = $null

    if ($relative -in @('.gitignore', '.gitattributes', 'README.md', 'docs/github-upload/UPLOAD_PLAN.md') -or
        ($relative.EndsWith('.md') -and -not $relative.Contains('/')) -or
        $relative.StartsWith('scripts/github/')) {
        $batch = '00-bootstrap'
    }
    elseif ($relative.StartsWith('backend/media/')) {
        $mediaFiles.Add($file)
        continue
    }
    elseif ($relative.StartsWith('db/')) {
        $batch = '03-database'
    }
    elseif ($top -in @('research', 'docs', 'backup') -or $file.Extension -eq '.docx') {
        $batch = '02-research-docs'
    }
    else {
        $batch = '01-core'
    }

    $rows.Add([pscustomobject]@{
        Batch = $batch
        SizeBytes = $file.Length
        SizeMB = [math]::Round($file.Length / 1MB, 3)
        LFS = ($lfsExtensions -contains $file.Extension.ToLowerInvariant())
        Path = $relative
    })
}

$mediaBatch = 1
$mediaBatchBytes = 0L
foreach ($file in ($mediaFiles | Sort-Object FullName)) {
    if ($mediaBatchBytes -gt 0 -and ($mediaBatchBytes + $file.Length) -gt $mediaLimitBytes) {
        $mediaBatch++
        $mediaBatchBytes = 0L
    }
    $rows.Add([pscustomobject]@{
        Batch = ('media-{0:d2}' -f $mediaBatch)
        SizeBytes = $file.Length
        SizeMB = [math]::Round($file.Length / 1MB, 3)
        LFS = ($lfsExtensions -contains $file.Extension.ToLowerInvariant())
        Path = Get-RelativePath $file.FullName
    })
    $mediaBatchBytes += $file.Length
}

New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
$rows | Sort-Object Batch, Path | Export-Csv -LiteralPath $manifestPath -NoTypeInformation -Encoding UTF8

$summary = $rows | Group-Object Batch | ForEach-Object {
    $bytes = ($_.Group | Measure-Object SizeBytes -Sum).Sum
    [pscustomobject]@{
        Batch = $_.Name
        Files = $_.Count
        SizeMB = [math]::Round($bytes / 1MB, 2)
        LFSFiles = @($_.Group | Where-Object LFS).Count
    }
} | Sort-Object Batch

$summary | Export-Csv -LiteralPath $summaryPath -NoTypeInformation -Encoding UTF8
$summary | Format-Table -AutoSize
Write-Host "Manifest: $manifestPath"
Write-Host "Summary : $summaryPath"
