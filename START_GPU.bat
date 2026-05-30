@echo off
title Studio Carton - RTX 4070 GPU
chcp 65001 > nul
echo ===================================
echo  STUDIO CARTON - GPU Local Mode
echo  RTX 4070 + Qwen 2.5 14B
echo ===================================
echo.

echo [1/4] Demarrage Ollama...
start /B "" ollama serve
timeout /t 3 /nobreak > nul

echo [2/4] Build frontend React...
cd /d C:\Users\moadf\studio-carton\frontend
call npm run build > nul 2>&1
xcopy /E /I /Y dist ..\backend\static > nul 2>&1

echo [3/4] Demarrage API (port 8000)...
cd /d C:\Users\moadf\studio-carton\backend
set PYTHONIOENCODING=utf-8
start /B "" python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
timeout /t 5 /nobreak > nul

echo [4/4] Ouverture navigateur...
start http://localhost:8000

echo.
echo Acces: http://localhost:8000
echo GPU: Qwen 2.5 14B sur RTX 4070
echo.
echo Appuie sur une touche pour arreter...
pause > nul
taskkill /F /IM python.exe /T > nul 2>&1