@echo off
setlocal
cd /d "%~dp0"

title ETF Advisor - Launcher

echo ========================================
echo   ETF Investment Advisor - Start
echo ========================================
echo.

if not exist "backend\venv\Scripts\activate.bat" (
    echo [ERROR] Python venv not found.
    echo Run setup first:
    echo   cd backend
    echo   python -m venv venv
    echo   venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

if not exist "frontend\node_modules" (
    echo [ERROR] Frontend dependencies not installed.
    echo Run: cd frontend ^&^& npm install
    echo.
    pause
    exit /b 1
)

echo Starting backend  (http://127.0.0.1:8000) ...
start "ETF Advisor - Backend" cmd /k "cd /d "%~dp0backend" && venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

echo Waiting for backend to initialize...
timeout /t 3 /nobreak >nul

echo Starting frontend (http://localhost:5173) ...
start "ETF Advisor - Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo ========================================
echo   App is starting in two windows:
echo   - ETF Advisor - Backend
echo   - ETF Advisor - Frontend
echo.
echo   Open: http://localhost:5173
echo.
echo   To stop: run stop.bat or close both windows
echo ========================================
echo.
pause
