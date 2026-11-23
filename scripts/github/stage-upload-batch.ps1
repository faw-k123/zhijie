param(
    [Parameter(Mandatory = $true)]
    [string]$Batch
)

$ErrorActionPreference = 'Stop'
$projectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$manifestPath = Join-Path $projectRoot 'docs\github-upload\file-manifest.csv'

Push-Location $projectRoot
try {
    if (-not (Test-Path -LiteralPath '.git')) {
        throw 'Git is not initialized. Run: git init -b main'
    }
    if (-not (Test-Path -LiteralPath $manifestPath)) {
        throw 'Upload manifest is missing. Run build-upload-manifest.ps1 first.'
    }

    $rows = Import-Csv -LiteralPath $manifestPath | Where-Object Batch -eq $Batch
    if (-not $rows) {
        $available = (Import-Csv -LiteralPath $manifestPath | Select-Object -ExpandProperty Batch -Unique) -join ', '
        throw "Unknown batch: $Batch. Available batches: $available"
    }

    $missing = @()
    foreach ($row in $rows) {
        if (-not (Test-Path -LiteralPath $row.Path)) {
            $missing += $row.Path
            continue
        }
        & git add -- $row.Path
        if ($LASTEXITCODE -ne 0) { throw "git add failed: $($row.Path)" }
    }

    $totalBytes = ($rows | Measure-Object -Property SizeBytes -Sum).Sum
    Write-Host ("Staged batch {0}: {1} files, about {2} MB" -f $Batch, $rows.Count, [math]::Round($totalBytes / 1MB, 2))
    if ($missing.Count) {
        Write-Warning ("{0} manifest files are missing. No files were deleted." -f $missing.Count)
        $missing | ForEach-Object { Write-Warning $_ }
    }
    & git status --short
    Write-Host 'Before committing, run: git diff --cached --stat'
}
finally {
    Pop-Location
}
