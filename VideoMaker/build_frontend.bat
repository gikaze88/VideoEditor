@echo off
echo Build du frontend VideoMaker...
cd /d "%~dp0\frontend"
npm run build
echo Build termine ! Les fichiers sont dans frontend/dist/
pause
