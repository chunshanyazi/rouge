@echo off
chcp 65001 >nul
title RlyehBot - 肉鸽模式自动脚本

echo ========================================
echo    RlyehBot - 肉鸽模式自动脚本
echo ========================================
echo.

python rlyeh_vision.py

if errorlevel 1 (
    echo.
    echo [错误] 启动失败！
    echo 请先安装依赖：双击 install_deps.bat
    echo.
    pause
)
