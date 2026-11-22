@echo off
title SRR Bazaar - AI Stylist & Ngrok Launcher
echo =======================================================
echo   Starting SRR Bazaar Local AI Backend & Ngrok Tunnel
echo =======================================================

echo [1/2] Launching FastAPI Backend on port 8000 (with auto-reload)...
start "SRR FastAPI Backend" cmd /k ".\.venv\Scripts\activate && uvicorn app:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 3 /nobreak >nul

echo [2/2] Launching Ngrok Tunnel on port 8000...
start "SRR Ngrok Tunnel" cmd /k "ngrok http 8000"

echo.
echo Both services are now running!
echo Keep both windows open while testing on your mobile phone.
echo =======================================================
pause
