$ErrorActionPreference = 'Stop'

$appRoot = Join-Path $PSScriptRoot 'app'
$backendRoot = Join-Path $appRoot 'backend'
$frontendRoot = Join-Path $appRoot 'frontend'
$python = Join-Path $backendRoot '.venv\Scripts\python.exe'
$nodeModules = Join-Path $frontendRoot 'node_modules'
$url = 'http://127.0.0.1:5175/login'
$backendUrl = 'http://127.0.0.1:8000/api/test/options/'
$logRoot = Join-Path $PSScriptRoot 'logs'

if (-not (Test-Path -LiteralPath $python) -or -not (Test-Path -LiteralPath $nodeModules)) {
    throw 'Dependencies are not installed. Run install.ps1 first.'
}

New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
$backendOut = Join-Path $logRoot 'backend.out.log'
$backendErr = Join-Path $logRoot 'backend.err.log'
$frontendOut = Join-Path $logRoot 'frontend.out.log'
$frontendErr = Join-Path $logRoot 'frontend.err.log'
Remove-Item $backendOut, $backendErr, $frontendOut, $frontendErr -Force -ErrorAction SilentlyContinue

$node = Get-Command node.exe -ErrorAction SilentlyContinue
if ($null -eq $node) { throw 'node.exe was not found. Install Node.js and add it to PATH.' }

$backendProcess = Start-Process -FilePath $python -ArgumentList @('manage.py', 'runserver', '127.0.0.1:8000') -WorkingDirectory $backendRoot -RedirectStandardOutput $backendOut -RedirectStandardError $backendErr -PassThru
$frontendProcess = Start-Process -FilePath $node.Source -ArgumentList @('.\node_modules\vite\bin\vite.js', '--configLoader', 'runner', '--host', '127.0.0.1', '--port', '5175', '--strictPort') -WorkingDirectory $frontendRoot -RedirectStandardOutput $frontendOut -RedirectStandardError $frontendErr -PassThru

Write-Host 'Waiting for frontend and backend services...'
$frontendReady = $false
$backendReady = $false
for ($attempt = 0; $attempt -lt 90; $attempt++) {
    if ($frontendProcess.HasExited) {
        $details = (Get-Content $frontendOut, $frontendErr -ErrorAction SilentlyContinue | Select-Object -Last 20) -join [Environment]::NewLine
        throw "Frontend failed to start: $details"
    }
    if ($backendProcess.HasExited) {
        $details = (Get-Content $backendOut, $backendErr -ErrorAction SilentlyContinue | Select-Object -Last 20) -join [Environment]::NewLine
        throw "Backend failed to start: $details"
    }
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 2
        if ($response.StatusCode -eq 200) { $frontendReady = $true }
    } catch {
    }
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $backendUrl -TimeoutSec 2
        if ($response.StatusCode -eq 200) { $backendReady = $true }
    } catch {
    }
    if ($frontendReady -and $backendReady) { break }
    Start-Sleep -Seconds 1
}

if (-not $frontendReady -or -not $backendReady) {
    $details = (Get-Content $backendOut, $backendErr, $frontendOut, $frontendErr -ErrorAction SilentlyContinue | Select-Object -Last 30) -join [Environment]::NewLine
    throw "Services did not become ready within 90 seconds: $details"
}

Start-Process $url
Write-Host "Application started: $url" -ForegroundColor Green
