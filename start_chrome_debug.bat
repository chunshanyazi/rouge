@echo off
chcp 65001 >nul
title 启动调试模式Chrome

echo ========================================
echo    邪神戦記ルルイエ少女隊 - 调试模式
echo ========================================
echo.

pause

echo.
echo 正在关闭Chrome...
taskkill /f /im chrome.exe 2>nul
timeout /t 2 /nobreak >nul

echo 正在启动调试模式Chrome...

if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\chrome-debug"
) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\chrome-debug"
) else (
    echo Chrome未找到！尝试从开始菜单启动...
    start "" "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Google Chrome\Google Chrome.lnk"
    timeout /t 3 /nobreak >nul
    taskkill /f /im chrome.exe 2>nul
    timeout /t 2 /nobreak >nul
    for /f "tokens=2*" %%A in ('reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe" /ve') do (
        start "" "%%B" --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\chrome-debug"
    )
)

echo.
echo Chrome已启动！端口: 9222
echo.
echo 请在Chrome中登录游戏，然后运行RlyehBot.exe
echo.
pause
