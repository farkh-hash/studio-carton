Write-Host "Demarrage Studio Carton..." -ForegroundColor Cyan

# 1. ComfyUI
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\Users\moadf\animer_carton\ComfyUI'; .\.venv\Scripts\Activate.ps1; python main.py --listen 127.0.0.1 --port 8188" -WindowStyle Normal

# 2. Backend FastAPI
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\Users\moadf\studio-carton\backend'; .\.venv\Scripts\Activate.ps1; python -m uvicorn app.main:app --reload" -WindowStyle Normal

# 3. Frontend React
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'C:\Users\moadf\studio-carton\frontend'; npm run dev" -WindowStyle Normal

Start-Sleep -Seconds 3
Write-Host ""
Write-Host "  ComfyUI  : http://127.0.0.1:8188" -ForegroundColor Green
Write-Host "  Backend  : http://localhost:8000/docs" -ForegroundColor Green
Write-Host "  Frontend : http://localhost:5173" -ForegroundColor Green
Write-Host ""
Write-Host "ComfyUI met ~15s a demarrer, patiente avant de generer." -ForegroundColor Yellow

Start-Sleep -Seconds 18
Start-Process "http://localhost:5173"
