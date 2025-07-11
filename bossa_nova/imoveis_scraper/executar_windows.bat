@echo off
echo === EXECUTANDO SCRAPER DE IMOVEIS ===
echo.

REM Verifica se o chromedriver existe
if not exist "chromedriver.exe" (
    echo [AVISO] chromedriver.exe não encontrado nesta pasta!
    echo.
    echo Baixe de: https://chromedriver.chromium.org/
    echo.
    echo Tentando executar mesmo assim (caso esteja no PATH)...
    echo.
)

REM Executa o scraper
python imoveis_scraper_windows.py

echo.
echo === EXECUÇÃO FINALIZADA ===
echo.
pause