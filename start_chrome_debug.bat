@echo off
chcp 65001 >nul
title 启动调试模式Chrome

echo ========================================
echo    邪神戦記ルルイエ少女隊 - 调试模式
echo ========================================
echo.
echo 此脚本会关闭所有Chrome并以调试模式重新启动
echo.
echo 启动后：
echo 1. 在Chrome里登录DMM游戏
echo 2. 打开RlyehBot.exe
echo 3. 点击"连接浏览器"
echo.

pause

echo.
echo 正在关闭Chrome...
taskkill /f /im chrome.exe 2>nul
timeout /t 2 /nobreak >nul

echo 正在启动调试模式Chrome...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\chrome-debug"

echo.
echo Chrome已启动！端口: 9222
echo.
echo 请在Chrome中登录游戏，然后运行RlyehBot.exe
echo.
pause
