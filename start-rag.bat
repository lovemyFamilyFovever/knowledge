@echo off
chcp 65001 >nul 2>&1
title Knowledge Reader + Semantic Search

echo.
echo Starting Knowledge Reader (with semantic search runtime) ...
echo.

cd /d "%~dp0"

if not exist ".python\python.exe" (
    echo [!] .python\ runtime not found. Falling back to system python.
    echo     Semantic search will be unavailable; the reader still works.
    start "" http://127.0.0.1:5001
    python app\app.py
    pause
    exit /b 1
)

echo Starting server at http://127.0.0.1:5001 ...
start "" http://127.0.0.1:5001
".python\python.exe" app\app.py
pause
