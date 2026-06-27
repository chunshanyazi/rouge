@echo off
title RlyehBot Vision

python rlyeh_vision.py

if errorlevel 1 (
    echo.
    echo Error! Please install dependencies first:
    echo pip install pyautogui opencv-python pillow numpy
    echo.
    pause
)
