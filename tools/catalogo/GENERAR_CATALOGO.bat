@echo off
color 0E
echo ==============================================================
echo       GENERADOR DE CATALOGOS EN PDF - ROJO MALBEC
echo ==============================================================
echo.
echo Leyendo las descripciones y conectando con Google Sheets...
echo Por favor espera unos segundos...
echo.

set PYTHONIOENCODING=utf-8
python generar_catalogo_pdf.py

echo.
echo ==============================================================
echo  PROCESO TERMINADO. 
echo  Si no hubo errores rojos arriba, tu catalogo ya esta listo.
echo  Busca el archivo: Catalogo_RojoMalbec.pdf
echo ==============================================================
echo.
pause
