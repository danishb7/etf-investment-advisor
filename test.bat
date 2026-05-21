@echo off
setlocal
cd /d "%~dp0backend"

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Run setup.bat first.
    exit /b 1
)

venv\Scripts\python.exe -m pip install -r requirements-dev.txt -q
venv\Scripts\python.exe -m pytest %*
exit /b %ERRORLEVEL%
