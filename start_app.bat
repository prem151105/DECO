@echo off
echo KMRL Knowledge Engine - Port Fix and Launch Script
echo ====================================================

cd /d "%~dp0"

REM Check if port 8501 is busy
echo Checking if port 8501 is available...
netstat -ano | findstr :8501 > nul
if %errorlevel% equ 0 (
    echo Port 8501 is busy. Attempting to fix...
    python fix_port.py
    if %errorlevel% neq 0 (
        echo Could not fix port automatically.
        echo Please close other applications or run: python fix_port.py
        pause
        exit /b 1
    )
) else (
    echo Port 8501 is available.
)

REM Activate virtual environment and run app
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Starting KMRL Knowledge Engine...
python app.py

pause