@echo off
title Studio Carton - GPU Local
echo ===================================
echo  STUDIO CARTON - RTX 4070 Mode
echo ===================================

echo Demarrage Ollama...
start /B ollama serve

echo Demarrage Backend FastAPI...
cd /d C:\Users\moadf\studio-carton\backend
pip install -r requirements.txt -q

echo.
echo ===================================
echo  Acces: http://localhost:8000
echo ===================================
echo.
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
