@echo off
rem Abre un Chrome aparte (con su propio perfil) que el programa puede manejar.
rem La primera vez inicia sesion en Google con la cuenta Pro. Luego queda guardada.
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%LOCALAPPDATA%\VidsAutomatizador\perfil" https://docs.google.com/videos
