@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title Al-Hera Educare Home - Question Bank
color 0b

cd /d "%~dp0"

REM 1. Activate virtual environment if present
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM 2. Check if Python is installed
where python >nul 2>&1
if errorlevel 1 (
    color 0c
    echo ======================================================================
    echo [ERROR] Python is not installed or not added to PATH!
    echo Please install Python from https://www.python.org and check "Add to PATH"
    echo ======================================================================
    echo.
    pause
    exit /b 1
)

REM 3. Configure logging to only show errors (hide 200, 302, 304 logs)
set SHOW_ERRORS_ONLY=1
set WERKZEUG_LOG_LEVEL=ERROR

REM 4. Run the application launcher
python launcher.py

REM 4. Handle exit
if errorlevel 1 (
    color 0c
    echo.
    echo ======================================================================
    echo [ERROR] Server stopped or encountered an issue.
    echo ======================================================================
    pause
)
