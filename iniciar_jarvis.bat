@echo off
title J.A.R.V.I.S. OS - STARK INDUSTRIES
color 0b
chcp 65001 > nul
cls
echo ================================================================
echo             J.A.R.V.I.S. NEURAL OPERATING SYSTEM               
echo                   INDUSTRIAS STARK - MARK LXXXV                
echo ================================================================
echo.
echo [1/2] Inicializando nucleo neuronal y modelos de IA...
cd /d "%~dp0"

REM Abrir navegador automaticamente despues de 2 segundos
start /min cmd /c "timeout /t 2 /nobreak > nul && start http://127.0.0.1:5000"

echo [2/2] Sistemas activos. Desplegando interfaz en su navegador...
echo.
echo ================================================================
echo   Acceso Local:        http://127.0.0.1:5000
echo   Para cerrar JARVIS:  Cierre esta ventana o presione Ctrl + C
echo ================================================================
echo.
.\venv\Scripts\python.exe app.py
pause
