@echo off
cd /d "%~dp0"
python generar_videos.py %*
pause
