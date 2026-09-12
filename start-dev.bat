@echo off
rem 知库 · 开发模式启动（--dev：改 py/模板自动热重载；Agent 2026-09-13 引入）
rem 生产/日常阅读请继续用 start.bat / start-rag.bat
cd /d "%~dp0"
if exist ".python\python.exe" (
  ".python\python.exe" "app\app.py" --dev
) else (
  python "app\app.py" --dev
)