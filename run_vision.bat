@echo off
chcp 65001 >nul
title RlyehBot 图像识别版

python rlyeh_vision.py

if errorlevel 1 (
    echo.
    echo 运行出错，请确保已安装依赖：
    echo pip install pyautogui opencv-python pillow numpy
    echo.
    pause
)
