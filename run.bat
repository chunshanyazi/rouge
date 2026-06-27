@echo off
title RlyehBot Starter
echo ========================================
echo   RlyehBot - Starter
echo ========================================
echo.

cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    echo Please install Python 3 first
    pause
    exit /b 1
)

pip show selenium >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing selenium...
    pip install selenium
)

echo Starting...
echo.

python rlyeh_bot.py

pause