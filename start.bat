@echo off
chcp 65001 >nul 2>&1
title Knowledge Reader

echo.
echo Starting Knowledge Reader ...
echo.

cd /d "%~dp0"

if exist ".python\python.exe" (
    echo Using bundled runtime .python\ ...
    start " " http://127.0.0.1:5001
    ".python\python.exe" app\app.py
    pause
    exit /b 0
)

python --version >nul 2>&1
if errorlevel 1 (
    echo Python not installed. Install Python 3.10+.
    pause
    exit /b 1
)

echo Checking dependencies ...
pip install -r requirements.txt -q 2>nul
if errorlevel 1 (
    echo Dependency install failed. Check requirements.txt.
    pause
    exit /b 1
)

echo Starting server at http://127.0.0.1:5001 ...
start "" http://127.0.0.1:5001
python app\app.py
pause
