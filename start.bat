@echo off
chcp 65001 >nul 2>&1
title 知库 Knowledge Reader

echo.
echo   知库 — 个人知识库单一入口
echo.

cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo Python 未安装，请先安装 Python 3.10+
    pause
    exit /b 1
)

pip install -r requirements.txt -q 2>nul
echo   依赖就绪，启动 http://127.0.0.1:5001 ...
start "" http://127.0.0.1:5001
python app\app.py
pause
