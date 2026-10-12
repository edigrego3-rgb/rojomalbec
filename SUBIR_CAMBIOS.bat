@echo off
chcp 65001 >nul
title Rojo Malbec - Subir Cambios al Repositorio

echo ======================================================
echo          ROJO MALBEC - SINCRONIZADOR GIT
echo ======================================================
echo.

cd /d "%~dp0"

echo [1/4] Verificando proteccion de seguridad contra secretos...
git ls-files --cached | findstr /i /r "secrets\.toml claves \.json$ \.env" >nul
if %errorlevel% == 0 (
    echo.
    echo [ERROR CRITICO] Se detectaron archivos de claves o secretos en el indice de Git!
    echo Operacion cancelada de inmediato por seguridad.
    echo.
    pause
    exit /b 1
)

echo [2/4] Agregando archivos al area de preparacion...
git add .

echo [3/4] Creando commit automatico con fecha y hora...
set FECHA=%date%
set HORA=%time%
git commit -m "Actualizacion automatica: %FECHA% %HORA%"

echo [4/4] Enviando cambios a GitHub (main)...
git push origin main

echo.
if %errorlevel% == 0 (
    echo ======================================================
    echo   CAMBIOS SUBIDOS CORRECTAMENTE A GITHUB!
    echo ======================================================
) else (
    echo ======================================================
    echo   HUBO UN ERROR AL ENVIAR LOS CAMBIOS. REVISE ARRIBA.
    echo ======================================================
)
echo.
pause
