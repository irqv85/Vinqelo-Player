@echo off
setlocal

cd /d "%~dp0"

set "PYTHON=%~dp0.venv\Scripts\python.exe"
set "PYTHONW=%~dp0.venv\Scripts\pythonw.exe"
set "LAUNCHER=%PYTHON%"

if exist "%PYTHONW%" set "LAUNCHER=%PYTHONW%"

if not exist "%LAUNCHER%" goto :missing_python
if not exist "%~dp0main.py" goto :missing_main

if /I "%~1"=="--check" (
    echo Vinqelo Player esta listo para ejecutarse.
    exit /b 0
)

start "" /D "%~dp0" "%LAUNCHER%" "%~dp0main.py"
exit /b 0

:missing_python
echo.
echo No se encontro el entorno de Python de Vinqelo Player.
echo Verifica que exista la carpeta: %~dp0.venv
echo.
pause
exit /b 1

:missing_main
echo.
echo No se encontro main.py en la carpeta de Vinqelo Player.
echo.
pause
exit /b 1
