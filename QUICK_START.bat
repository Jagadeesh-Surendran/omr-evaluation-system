@echo off
cls
echo ========================================
echo   OMR EVALUATION SYSTEM
echo   Quick Start Script
echo ========================================
echo.
echo Starting your application...
echo.
echo Your app will be available at:
echo   http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

cd backend
call ..\.venv\Scripts\activate.bat
python app.py

pause
