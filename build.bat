@echo off
chcp 936 >nul
echo ========================================
echo   RlyehBot Build Tool
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    echo Please install Python 3 first
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python found
echo.

echo Installing selenium and pyinstaller...
pip install selenium pyinstaller -q
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

pyinstaller --onefile --name RlyehBot --console rlyeh_bot.py

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
echo How to use:
echo 1. Open the "dist" folder
echo 2. Double-click RlyehBot.exe
echo 3. Login to DMM and enter the game
echo 4. Press Enter in the command window
echo.
pause
explorer dist
