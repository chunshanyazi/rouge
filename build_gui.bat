@echo off
title RlyehBot Builder
echo ========================================
echo   RlyehBot - Build EXE
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

if not exist "rlyeh_gui.py" (
    echo [ERROR] rlyeh_gui.py not found
    pause
    exit /b 1
)

echo Building, please wait...
echo This may take a few minutes
echo.

pyinstaller --onefile --windowed --name RlyehBot --collect-all selenium rlyeh_gui.py

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
