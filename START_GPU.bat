@echo off
title Studio Carton - RTX 4070 GPU
chcp 65001 > nul
echo ===================================
echo  STUDIO CARTON - GPU Local Mode
echo  RTX 4070 + Qwen 2.5 14B
echo ===================================
echo.

echo [1/3] Demarrage Ollama...
start /B "" ollama serve
timeout /t 3 /nobreak > nul

echo [2/3] Demarrage API (port 8000)...
cd /d C:\Users\moadf\studio-carton\backend
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
start /B "" python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
timeout /t 5 /nobreak > nul

echo [3/3] Tout est pret!
echo.
echo Accede a l'app: http://localhost:8000
echo.
echo Appuie sur une touche pour arreter...
pause > nul

echo Arret en cours...
taskkill /F /IM python.exe /T > nul 2>&1
taskkill /F /IM ollama.exe /T > nul 2>&1