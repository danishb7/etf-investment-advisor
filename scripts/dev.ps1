$ErrorActionPreference = 'Stop'
$Root = Split-Path $PSScriptRoot -Parent

$backendExe = Join-Path $Root 'backend\venv\Scripts\python.exe'
$backendWd = Join-Path $Root 'backend'
$frontendWd = Join-Path $Root 'frontend'
$stopScript = Join-Path $PSScriptRoot 'stop-dev.ps1'

if (-not (Test-Path $backendExe)) {
    Write-Host '[ERROR] Python venv not found. Run setup.bat first.' -ForegroundColor Red
    exit 1
}
if (-not (Test-Path (Join-Path $frontendWd 'node_modules'))) {
    Write-Host '[ERROR] Frontend dependencies missing. Run setup.bat first.' -ForegroundColor Red
    exit 1
}

& $stopScript

Write-Host ''
Write-Host '========================================'
Write-Host '  ETF Investment Advisor'
Write-Host '========================================'
Write-Host '  Backend:  http://127.0.0.1:8000'
Write-Host '  Frontend: http://localhost:5173'
Write-Host ''
Write-Host '  Press Ctrl+C to stop both servers.'
Write-Host '  Or run stop.bat from another Explorer window.'
Write-Host '========================================'
Write-Host ''

$backend = Start-Process -PassThru -FilePath $backendExe `
    -ArgumentList @('-m', 'uvicorn', 'app.main:app', '--reload', '--host', '127.0.0.1', '--port', '8000') `
    -WorkingDirectory $backendWd `
    -NoNewWindow

Start-Sleep -Seconds 2

$frontend = Start-Process -PassThru -FilePath 'cmd.exe' `
    -ArgumentList @('/c', 'npm run dev') `
    -WorkingDirectory $frontendWd `
    -NoNewWindow

try {
    Wait-Process -Id $frontend.Id
}
finally {
    Write-Host ''
    Write-Host 'Stopping servers...'
    foreach ($proc in @($frontend, $backend)) {
        if ($proc -and -not $proc.HasExited) {
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        }
    }
    & $stopScript
}
