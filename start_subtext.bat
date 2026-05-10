@echo off
echo ========================================
echo   Starting Subtext Discovery Engine
echo ========================================

:: Start Backend in a new window
echo [1/2] Launching Backend (FastAPI)...
start "Subtext Backend" cmd /k "cd backend && venv\Scripts\activate && python main.py"

:: Start Frontend in a new window
echo [2/2] Launching Frontend (Next.js)...
start "Subtext Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo   All systems are starting! 
echo   Keep the separate windows open to run.
echo ========================================
pause
