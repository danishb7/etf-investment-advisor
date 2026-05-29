@echo off
setlocal
cd /d "%~dp0"

echo Stopping ETF Investment Advisor...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\stop-dev.ps1"
echo Done.
timeout /t 2 /nobreak >nul
