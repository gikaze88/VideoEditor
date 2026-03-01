@echo off
echo Arret du processus sur le port 8001...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8001 "') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo Demarrage du backend VideoMaker (port 8001)...
cd /d "%~dp0"
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload
pause
