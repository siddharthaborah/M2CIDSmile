@echo off
title M2CIDSmile Tool
echo ============================================
echo   M2CIDSmile Tool - Molecule Info Fetcher
echo ============================================
echo.

cd /d "%~dp0"

:: Check for Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: Install dependencies
echo Installing required packages...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet customtkinter
echo.

:: Launch the app
echo Starting M2CIDSmile Tool...
echo.
python m2cidsmile_gui.py

pause
