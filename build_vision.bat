@echo off
chcp 65001 >nul
title 打包图像识别版exe

echo ========================================
echo    打包图像识别版 exe
echo ========================================
echo.

echo 正在检查依赖...
pip install pyautogui opencv-python pillow numpy pyinstaller -q

echo.
echo 正在打包...
pyinstaller --onefile --name RlyehBot_Vision --console --collect-all pyautogui --collect-all cv2 rlyeh_vision.py

echo.
echo 打包完成！exe 在 dist 文件夹里
echo.
pause
