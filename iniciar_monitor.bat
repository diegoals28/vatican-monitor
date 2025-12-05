@echo off
title Vatican Ticket Monitor
cd /d "%~dp0"
echo.
echo ========================================
echo   Vatican Ticket Monitor
echo ========================================
echo.
echo Iniciando servidor...
echo Abre tu navegador en: http://localhost:5001
echo.
echo Presiona CTRL+C para detener
echo ========================================
echo.
start http://localhost:5001
python app.py
pause
