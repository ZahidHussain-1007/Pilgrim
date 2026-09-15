@echo off
title PilgrimAL Launcher
cd /d C:\Users\trivi\OneDrive\Desktop\Pilgrim

echo ==========================================
echo          PILGRIMAL APPLICATION
echo ==========================================
echo.

echo [1/3] Starting FastAPI worker...
start "Pilgrim Worker - FastAPI :8000" cmd /k "cd /d C:\Users\trivi\OneDrive\Desktop\Pilgrim && worker\.venv\Scripts\python.exe -m uvicorn worker.main:app --host 127.0.0.1 --port 8000"

timeout /t 3 /nobreak >null

echo [2/3] Starting RAG agent...
start "Pilgrim RAG - FastAPI :8002" cmd /k "cd /d C:\Users\trivi\OneDrive\Desktop\Pilgrim && C:\Users\trivi\AppData\Local\Programs\Python\Python313\python.exe -m uvicorn worker.rag_agent:app --host 127.0.0.1 --port 8002"

echo [3/3] Starting NestJS backend...
start "Pilgrim Backend - NestJS" cmd /k "cd /d C:\Users\trivi\OneDrive\Desktop\Pilgrim && npm run dev"

echo.
echo ==========================================
echo       PILGRIMAL SERVERS STARTED
echo ==========================================
echo.
echo FastAPI Worker: http://127.0.0.1:8000
echo RAG Agent:      http://127.0.0.1:8002
echo NestJS:         http://127.0.0.1:3000
echo.
echo Three terminal windows have been opened.
echo You can close this launcher window.
echo.

pause