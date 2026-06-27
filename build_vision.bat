@echo off
title Build Vision EXE

echo ========================================
echo    Build Vision EXE
echo ========================================
echo.

echo Checking dependencies...
pip install pyautogui opencv-python pillow numpy pyinstaller -q

echo.
echo Building...
pyinstaller --onefile --name RlyehBot_Vision --console --collect-all pyautogui --collect-all cv2 rlyeh_vision.py

echo.
echo Done! EXE is in dist folder
echo.
pause
