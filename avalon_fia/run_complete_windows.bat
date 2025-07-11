@echo off
echo =====================================
echo   AVALON FIA - Analytics Dashboard
echo   Versao Completa e Elegante
echo =====================================
echo.

cd /d "%~dp0"

echo Instalando dependencias necessarias...
python -m pip install flask pandas numpy requests matplotlib MetaTrader5 --quiet

echo.
echo Iniciando dashboard...
echo Acesse http://localhost:5000 no seu navegador
echo.

python run_complete.py

pause