@echo off
title RlyehBot Build Tool
echo ========================================
echo   RlyehBot - Build Tool
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

echo [OK] Python detected
echo.

echo Installing dependencies...
pip install selenium pyinstaller
if errorlevel 1 (
    echo [ERROR] Failed to install
    pause
    exit /b 1
)

echo [OK] Install complete
echo.

if not exist "rlyeh_bot.py" (
    echo [ERROR] rlyeh_bot.py not found
    pause
    exit /b 1
)

echo Building, please wait...
echo This may take a few minutes
echo.

pyinstaller --onefile --name RlyehBot --collect-all selenium --console rlyeh_bot.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Build Complete!
echo ========================================
echo.
echo EXE file is in the "dist" folder
echo.
pause
explorer dist
