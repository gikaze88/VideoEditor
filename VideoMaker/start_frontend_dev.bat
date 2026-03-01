@echo off
echo Arret du processus sur le port 5174...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5174 "') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo Demarrage du frontend VideoMaker (port 5174)...
cd /d "%~dp0\frontend"
npm run dev
pause
