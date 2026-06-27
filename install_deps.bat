@echo off
title Install Dependencies

echo ========================================
echo    Install Dependencies
echo ========================================
echo.

pip install pyautogui opencv-python pillow numpy

if errorlevel 1 (
    echo.
    echo Failed to install!
    pause
    exit /b 1
)

echo.
echo ========================================
echo    Install Complete!
echo ========================================
echo.
pause
