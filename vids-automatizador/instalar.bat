@echo off
cd /d "%~dp0"
echo Instalando lo necesario...
python -m pip install -r requirements.txt
python -m playwright install chromium
echo.
echo Listo. Ahora instala Ollama desde https://ollama.com y ejecuta:
echo     ollama pull qwen2.5vl:3b
pause
