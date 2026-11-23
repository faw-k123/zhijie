$ErrorActionPreference = 'Stop'

$appRoot = Join-Path $PSScriptRoot 'app'
$backendRoot = Join-Path $appRoot 'backend'
$frontendRoot = Join-Path $appRoot 'frontend'
$venvPython = Join-Path $backendRoot '.venv\Scripts\python.exe'

function Assert-LastCommand([string]$message) {
    if ($LASTEXITCODE -ne 0) {
        throw "$message (exit code: $LASTEXITCODE)"
    }
}

if (-not (Test-Path -LiteralPath $appRoot)) { throw "App directory not found: $appRoot" }

$python = Get-Command py -ErrorAction SilentlyContinue
if ($null -eq $python) { $python = Get-Command python -ErrorAction SilentlyContinue }
if ($null -eq $python) { throw 'Python was not found. Install Python 3.11 and add it to PATH.' }

if (Test-Path -LiteralPath $venvPython) {
    & $venvPython --version *> $null
    if ($LASTEXITCODE -ne 0) {
        Remove-Item -LiteralPath (Join-Path $backendRoot '.venv') -Recurse -Force
    }
}

if (-not (Test-Path -LiteralPath $venvPython)) {
    if ($python.Name -eq 'py.exe') {
        & $python.Source -3.11 -m venv (Join-Path $backendRoot '.venv')
    } else {
        & $python.Source -m venv (Join-Path $backendRoot '.venv')
    }
    Assert-LastCommand 'Failed to create the Python virtual environment'
}

& $venvPython -m pip install --upgrade pip
Assert-LastCommand 'Failed to upgrade pip'
& $venvPython -m pip install -r (Join-Path $backendRoot 'requirements.txt')
Assert-LastCommand 'Failed to install backend dependencies'

$envFile = Join-Path $backendRoot '.env'
$envExample = Join-Path $appRoot '.env.example'
if (-not (Test-Path -LiteralPath $envFile) -and (Test-Path -LiteralPath $envExample)) {
    Copy-Item -LiteralPath $envExample -Destination $envFile
    Write-Host 'Created backend\.env. Configure databases and API services as needed.' -ForegroundColor Yellow
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw 'npm was not found. Install Node.js 22 or newer.' }

Push-Location $frontendRoot
try {
    npm install --legacy-peer-deps
    Assert-LastCommand 'Failed to install frontend dependencies'
} finally {
    Pop-Location
}

Write-Host 'Installation completed. Run start.bat to start the application.' -ForegroundColor Green
