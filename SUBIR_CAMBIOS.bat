@echo off
chcp 65001 >nul
title Rojo Malbec - Subir Cambios y Desplegar en VPS

echo ======================================================
echo       ROJO MALBEC - CI/CD AUTOMATICO (GIT + VPS)
echo ======================================================
echo.

cd /d "%~dp0"

echo [1/5] Verificando proteccion de seguridad contra secretos...
git ls-files --cached | findstr /i /r "secrets\.toml claves \.json$ \.env" >nul
if %errorlevel% == 0 (
    echo.
    echo [ERROR CRITICO] Se detectaron archivos de claves o secretos en el indice de Git!
    echo Operacion cancelada de inmediato por seguridad.
    echo.
    pause
    exit /b 1
)

echo [2/5] Agregando archivos al area de preparacion...
git add .

echo [3/5] Creando commit automatico con fecha y hora...
set FECHA=%date%
set HORA=%time%
git commit -m "Actualizacion automatica: %FECHA% %HORA%"

echo [4/5] Enviando cambios a GitHub (main)...
git push origin main
if %errorlevel% neq 0 (
    echo.
    echo ======================================================
    echo   HUBO UN ERROR AL ENVIAR LOS CAMBIOS A GITHUB.
    echo ======================================================
    pause
    exit /b 1
)

echo.
echo [5/5] Desplegando en VPS Hetzner (ERP, Distribuidor, Preventa)...
ssh root@2.31.10.225 "cd /root/rojomalbec && git pull origin main && docker compose up -d --build erp distribuidor preventa"

if %errorlevel% == 0 (
    echo.
    echo ======================================================
    echo   TODO LISTO Y DESPLEGADO CON EXITO EN EL VPS!
    echo   - ERP: https://erp.rojomalbec.com.ar
    echo   - B2B: https://b2b.rojomalbec.com.ar
    echo   - Preventa: https://preventa.rojomalbec.com.ar
    echo ======================================================
) else (
    echo.
    echo ======================================================
    echo   HUBO UN ERROR EN EL DESPLIEGUE DEL VPS. REVISE ARRIBA.
    echo ======================================================
)
echo.
pause
