@echo off
title PilgrimAL Launcher
cd /d C:\Projects\Pilgrim

echo ==========================================
echo          PILGRIMAL APPLICATION
echo ==========================================
echo.

echo [1/2] Starting FastAPI RAG server...
start "Pilgrim RAG - FastAPI :8001" cmd /k "cd /d C:\Projects\Pilgrim && .venv\Scripts\python.exe worker\rag_agent.py"

timeout /t 3 /nobreak >nul

echo [2/2] Starting NestJS backend...
start "Pilgrim Backend - NestJS" cmd /k "cd /d C:\Projects\Pilgrim && npm run dev"

echo.
echo ==========================================
echo       PILGRIMAL SERVERS STARTED
echo ==========================================
echo.
echo FastAPI RAG: http://127.0.0.1:8001
echo NestJS:      http://127.0.0.1:3000
echo.
echo Two terminal windows have been opened.
echo You can close this launcher window.
echo.