@echo off
chcp 65001 >nul
REM FitCoach Garmin API - Windows 快速启动脚本

echo.
echo ═════════════════════════════════════════════════════════
echo   FitCoach Garmin API - 本地开发服务器
echo ═════════════════════════════════════════════════════════
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误：未检测到 Python
    echo.
    echo 请先安装 Python 3.7 或更高版本：
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo ✅ Python 已安装
echo.

REM 检查环境变量
if "%GARMIN_EMAIL%"=="" (
    echo ⚠️  警告：未设置 GARMIN_EMAIL 环境变量
    echo.
    set /p GARMIN_EMAIL="请输入 Garmin 邮箱: "
)

if "%GARMIN_PASSWORD%"=="" (
    echo ⚠️  警告：未设置 GARMIN_PASSWORD 环境变量
    echo.
    set /p GARMIN_PASSWORD="请输入 Garmin 密码: "
)

echo.
echo ═════════════════════════════════════════════════════════
echo   正在启动服务器...
echo ═════════════════════════════════════════════════════════
echo.

REM 启动服务器
python garmin-api.py

pause
