@echo off
REM INSTALADOR AUTOMÁTICO V2 WINDOWS - EXTRATOR CVM
REM ===============================================

echo 🚀 INSTALANDO EXTRATOR CVM COMPLETO V2
echo ======================================
echo ✨ Nova versão com download automático de documentos!
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado. Instale Python 3.7+ primeiro.
    echo 📥 Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python encontrado
python --version

REM Verificar pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip não encontrado. Instale pip primeiro.
    pause
    exit /b 1
)

echo ✅ pip encontrado

REM Instalar dependências
echo.
echo 📦 Instalando dependências...
pip install -r requirements.txt

if errorlevel 1 (
    echo ❌ Erro ao instalar dependências
    echo 💡 Tente: pip install pandas requests openpyxl
    pause
    exit /b 1
)

echo ✅ Dependências instaladas com sucesso!

REM Verificar instalação
echo.
echo 🔍 Verificando instalação...
python -c "import pandas, requests, openpyxl; print('✅ pandas OK'); print('✅ requests OK'); print('✅ openpyxl OK')"

if errorlevel 1 (
    echo ❌ Erro na verificação. Verifique as dependências manualmente.
    pause
    exit /b 1
)

echo ✅ Todas as dependências verificadas!

REM Teste rápido
echo.
echo 🧪 Executando teste rápido...
python exemplos/teste_rapido.py

if errorlevel 1 (
    echo ❌ Erro no teste. Verifique a instalação.
    pause
    exit /b 1
)

echo.
echo 🎉 INSTALAÇÃO CONCLUÍDA COM SUCESSO!
echo.
echo 📋 PRÓXIMOS PASSOS:
echo 1. ⭐ Sistema completo: python sistema_cvm_completo.py
echo 2. 📚 Exemplos: python exemplos/exemplo_download_real.py
echo 3. 🔧 Teste: python exemplos/teste_rapido.py
echo.
echo 🆕 NOVIDADES V2:
echo ✨ Download automático de PDFs da CVM
echo 📁 Organização inteligente em pastas
echo 📊 Relatórios detalhados de downloads
echo ⚙️ Configurações avançadas
echo.
echo 📁 Dados das empresas: dados/
echo 📖 Documentação: docs/
echo 📚 Exemplos: exemplos/
echo.
echo ⚠️  ATENÇÃO: O sistema baixa arquivos reais da CVM!
echo 💡 Comece com poucos documentos para testar.
echo.
pause

