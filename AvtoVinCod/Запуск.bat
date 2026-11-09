@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 goto run_py
where python >nul 2>nul
if not errorlevel 1 goto run_python
echo Python не найден. Установите его с https://www.python.org/downloads/
echo При установке отметьте галочку "Add python.exe to PATH".
goto end
:run_py
py avtovincod.py
goto end
:run_python
python avtovincod.py
:end
pause
