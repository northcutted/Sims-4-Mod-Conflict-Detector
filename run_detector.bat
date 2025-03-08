@echo off
echo Sims 4 Mod Conflict Detector
echo ===========================
echo.

REM Check if Python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python is not installed or not in your PATH.
    echo Please install Python 3.6 or newer from https://www.python.org/
    echo.
    pause
    exit /b 1
)

REM Run the mod detector
python mod_conflict_detector.py %*

echo.
pause