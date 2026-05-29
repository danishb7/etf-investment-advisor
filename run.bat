@echo off
setlocal
cd /d "%~dp0"

title ETF Advisor

if not exist "backend\venv\Scripts\python.exe" (
    echo [ERROR] Python venv not found. Run setup.bat first.
    pause
    exit /b 1
)

if not exist "frontend\node_modules" (
    echo [ERROR] Frontend dependencies not installed. Run setup.bat first.
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\dev.ps1"
exit /b %ERRORLEVEL%
