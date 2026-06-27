@echo off
chcp 65001 >nul
echo ========================================
echo   RlyehBot 一键打包工具
echo ========================================
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] 检测到Python环境
echo.

:: 安装必要的库
echo 正在安装Selenium和PyInstaller...
pip install selenium pyinstaller -q
if errorlevel 1 (
    echo [错误] 安装库失败，请检查网络连接
    pause
    exit /b 1
)

echo [OK] 库安装完成
echo.

:: 检查脚本文件
if not exist "rlyeh_bot.py" (
    echo [错误] 未找到 rlyeh_bot.py
    echo 请确保 rlyeh_bot.py 在同一目录下
    pause
    exit /b 1
)

if not exist "config.json" (
    echo [警告] 未找到 config.json，将使用默认配置
)

echo 正在打包，请稍等...
echo 这可能需要几分钟时间...
echo.

:: 开始打包
pyinstaller --onefile --name RlyehBot --console rlyeh_bot.py

if errorlevel 1 (
    echo.
    echo [错误] 打包失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo   打包完成！
echo ========================================
echo.
echo exe文件已生成在 dist 文件夹中
echo.
echo 使用方法:
echo 1. 打开 dist 文件夹
echo 2. 双击 RlyehBot.exe 运行
echo 3. 在浏览器中手动登录DMM并进入游戏
echo 4. 回到命令行按Enter键开始自动挂机
echo.
echo 按任意键打开dist文件夹...
pause >nul
explorer dist
