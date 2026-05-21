@echo off
setlocal
cd /d "%~dp0"

title ETF Advisor - Setup

echo ========================================
echo   ETF Investment Advisor - First-time setup
echo ========================================
echo.

echo [1/3] Creating Python virtual environment...
cd backend
if not exist "venv\Scripts\python.exe" (
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create venv. Is Python 3.11+ installed?
        pause
        exit /b 1
    )
)
venv\Scripts\python.exe -m pip install -r requirements.txt -q
if not exist ".env" (
    copy .env.example .env >nul
    echo Created backend\.env - add FRED_API_KEY if you have one.
)
cd ..

echo.
echo [2/3] Installing frontend dependencies...
cd frontend
call npm install
cd ..

echo.
echo [3/3] Done.
echo.
echo Next steps:
echo   1. Optional: edit backend\.env and set FRED_API_KEY
echo   2. Double-click run.bat to start the app
echo   3. Double-click stop.bat to shut down
echo.
pause
