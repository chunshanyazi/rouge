@echo off
title Start Chrome with Debug
echo Starting Chrome with remote debugging...
echo.
echo Close all Chrome windows first!
echo.
pause

taskkill /f /im chrome.exe 2>nul
timeout /t 2 /nobreak >nul

start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\chrome-debug"

echo.
echo Chrome started with debug port 9222
echo Now open DMM game and login
echo Then run RlyehBot.exe and click Connect
echo.
pause