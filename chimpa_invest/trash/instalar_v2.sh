#!/bin/bash
# INSTALADOR AUTOMÁTICO V2 - EXTRATOR CVM COM DOWNLOAD
# ===================================================

echo "🚀 INSTALANDO EXTRATOR CVM COMPLETO V2"
echo "======================================"
echo "✨ Nova versão com download automático de documentos!"
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Instale Python 3.7+ primeiro."
    echo "📥 Download: https://www.python.org/downloads/"
    exit 1
fi

echo "✅ Python encontrado: $(python3 --version)"

# Verificar pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 não encontrado. Instale pip primeiro."
    exit 1
fi

echo "✅ pip3 encontrado"

# Instalar dependências
echo ""
echo "📦 Instalando dependências..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependências instaladas com sucesso!"
else
    echo "❌ Erro ao instalar dependências"
    echo "💡 Tente: pip3 install pandas requests openpyxl"
    exit 1
fi

# Verificar instalação
echo ""
echo "🔍 Verificando instalação..."
python3 -c "
import pandas, requests, openpyxl
print('✅ pandas OK')
print('✅ requests OK') 
print('✅ openpyxl OK')
"

if [ $? -eq 0 ]; then
    echo "✅ Todas as dependências verificadas!"
else
    echo "❌ Erro na verificação. Verifique as dependências manualmente."
    exit 1
fi

# Teste rápido
echo ""
echo "🧪 Executando teste rápido..."
python3 exemplos/teste_rapido.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 INSTALAÇÃO CONCLUÍDA COM SUCESSO!"
    echo ""
    echo "📋 PRÓXIMOS PASSOS:"
    echo "1. ⭐ Sistema completo: python3 sistema_cvm_completo.py"
    echo "2. 📚 Exemplos: python3 exemplos/exemplo_download_real.py"
    echo "3. 🔧 Teste: python3 exemplos/teste_rapido.py"
    echo ""
    echo "🆕 NOVIDADES V2:"
    echo "✨ Download automático de PDFs da CVM"
    echo "📁 Organização inteligente em pastas"
    echo "📊 Relatórios detalhados de downloads"
    echo "⚙️ Configurações avançadas"
    echo ""
    echo "📁 Dados das empresas: dados/"
    echo "📖 Documentação: docs/"
    echo "📚 Exemplos: exemplos/"
    echo ""
    echo "⚠️  ATENÇÃO: O sistema baixa arquivos reais da CVM!"
    echo "💡 Comece com poucos documentos para testar."
    echo ""
else
    echo "❌ Erro no teste. Verifique a instalação."
    exit 1
fi

