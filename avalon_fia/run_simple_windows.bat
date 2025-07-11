@echo off
echo =====================================
echo   AVALON FIA - Dashboard Simplificado
echo   (Versao sem MetaTrader 5)
echo =====================================
echo.

cd /d "%~dp0"

echo Instalando dependencias basicas...
python -m pip install flask pandas numpy requests --quiet

echo.
echo Iniciando dashboard simplificado...
echo Acesse http://localhost:5000 no seu navegador
echo.

python run_simple.py

pause