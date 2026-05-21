@echo off
setlocal
cd /d "%~dp0"

title ETF Advisor - Stop

echo ========================================
echo   ETF Investment Advisor - Stop
echo ========================================
echo.

set STOPPED=0

echo Stopping processes on ports 8000 and 5173...
powershell -NoProfile -Command ^
  "$ports = 8000, 5173; $pids = Get-NetTCPConnection -LocalPort $ports -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique; if ($pids) { $pids | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue; Write-Host ('  Stopped PID ' + $_) }; exit 0 } else { exit 1 }"

if %ERRORLEVEL% equ 0 (
    set STOPPED=1
)

REM Fallback: close windows by title (backend/frontend dev servers)
taskkill /FI "WINDOWTITLE eq ETF Advisor - Backend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq ETF Advisor - Frontend*" /F >nul 2>&1

if %STOPPED% equ 1 (
    echo.
    echo Servers stopped.
) else (
    echo.
    echo No servers found on ports 8000 or 5173.
    echo They may already be stopped.
)

echo.
pause
