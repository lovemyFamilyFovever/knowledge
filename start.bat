@echo off
chcp 65001 >nul 2>&1
title Knowledge Reader

rem Single entry point (merged start-rag.bat / start-dev.bat on 2026-09-13):
rem   start.bat           daily start (semantic search auto-enabled when deps available)
rem   start.bat --dev     dev mode (auto-reload on py / template changes)
rem Prefers bundled runtime .python\ when present; falls back to system Python.
rem Missing RAG deps never block startup - only the "?" semantic search is disabled.

set ARGS=%*
cd /d "%~dp0"

rem ---- pick interpreter: bundled runtime first, then system python ----
set PY=
if exist ".python\python.exe" (
    set PY=.python\python.exe
    echo Using bundled runtime .python\ ...
) else (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [!] Python not found. Install Python 3.10+, or restore the .python\ runtime.
        pause
        exit /b 1
    )
    set PY=python
)

rem ---- first-run convenience: install core deps only when flask is missing ----
%PY% -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies ...
    %PY% -m pip install -r requirements.txt -q
    if errorlevel 1 (
        echo [!] Dependency install failed. Check your network, or run: %PY% -m pip install -r requirements.txt
        pause
        exit /b 1
    )
)

rem ---- port 5001 guard: a stale instance makes the new one die silently ----
netstat -ano | findstr ":5001" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo [i] Port 5001 is already in use - the reader is probably ALREADY RUNNING.
    echo     Just open http://127.0.0.1:5001 in your browser.
    echo     To force restart:  netstat -ano ^| findstr :5001   then   taskkill /f /pid ^<pid^>
    start "" http://127.0.0.1:5001
    pause
    exit /b 0
)

rem ---- semantic search probe (non-blocking) ----
%PY% -c "import onnxruntime" >nul 2>&1
if errorlevel 1 (
    echo [i] Semantic search deps missing - reader works, "?" semantic search disabled.
    echo     Enable it later:  %PY% -m pip install -r requirements-rag.txt
) else (
    echo [i] Semantic search ready.
)

echo Starting server at http://127.0.0.1:5001 ...
rem ---- local private env (gitignored _local_env.bat: KB_AI_API_KEY etc.) ----
if exist "_local_env.bat" call "_local_env.bat"
start "" http://127.0.0.1:5001
%PY% app\app.py %ARGS%
pause
