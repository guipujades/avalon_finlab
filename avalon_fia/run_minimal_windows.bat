@echo off
echo.
echo ===============================================
echo   AVALON FIA - Dashboard Minimal
echo ===============================================
echo.

cd /d "%~dp0"

echo Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo Instale Python 3.x e tente novamente.
    pause
    exit /b 1
)

echo Python encontrado!
echo.

echo Iniciando dashboard...
python run_minimal.py

pause