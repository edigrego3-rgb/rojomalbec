@echo off
chcp 65001 > nul
echo ========================================================
echo       GENERADOR DE CODIGOS QR - ROJO MALBEC
echo ========================================================
echo.
cd /d "%~dp0"
python generar_qrs.py
echo.
echo ========================================================
echo Abriendo la carpeta con los codigos QR y carteles...
echo ========================================================
start "" "%~dp0salida"
pause
