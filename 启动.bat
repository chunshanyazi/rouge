@echo off
chcp 65001 >nul
title RlyehBot - 邪神戦記ルルイエ少女隊

echo ========================================
echo   RlyehBot 启动器
echo ========================================
echo.

cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

pip show selenium >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装selenium...
    pip install selenium
)

echo 正在启动脚本...
echo.

python rlyeh_bot.py

pause