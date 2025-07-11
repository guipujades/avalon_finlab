@echo off
echo === INSTALADOR DO SCRAPER DE IMOVEIS ===
echo.

REM Verifica se Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python não encontrado!
    echo Por favor, instale Python de: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python encontrado
echo.

REM Instala dependências
echo Instalando dependências Python...
pip install requests beautifulsoup4 selenium pandas lxml

echo.
echo === PRÓXIMOS PASSOS ===
echo.
echo 1. INSTALAR GOOGLE CHROME (se não tiver):
echo    https://www.google.com/chrome/
echo.
echo 2. BAIXAR CHROMEDRIVER:
echo    - Verifique sua versão do Chrome: chrome://version/
echo    - Baixe o ChromeDriver correspondente de:
echo      https://chromedriver.chromium.org/downloads
echo    - Extraia o chromedriver.exe nesta pasta
echo.
echo 3. EXECUTAR O SCRAPER:
echo    python imoveis_scraper_windows.py
echo.
echo === ESTRUTURA DOS DADOS ===
echo Os dados serão salvos em: dados_imoveis\imoveis_YYYY-MM-DD.json
echo.
pause