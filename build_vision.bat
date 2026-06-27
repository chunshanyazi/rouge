@echo off
title Build Vision EXE

echo ========================================
echo    Build Vision EXE
echo ========================================
echo.

echo Installing dependencies...
echo.
pip install pyautogui opencv-python pillow numpy pyinstaller

if errorlevel 1 (
    echo.
    echo Failed to install dependencies!
    pause
    exit /b 1
)

echo.
echo Building exe...
echo.
pyinstaller --onefile --name RlyehBot_Vision --console --collect-all pyautogui --collect-all cv2 rlyeh_vision.py

if errorlevel 1 (
    echo.
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo    Build Complete!
echo    EXE is in dist\ folder
echo ========================================
echo.
pause
