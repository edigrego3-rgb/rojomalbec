if not "%1" == "min" start /min cmd /c %0 min & exit/b
@echo off
cd /d "%~dp0"
streamlit run app_v3.py
pause
