#!/bin/bash
# Setup para usar Claude via API com análise de PDFs

echo "🚀 Configurando Claude API para Chimpa Invest"
echo "============================================"

# Verificar se já tem API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo ""
    echo "⚠️  API Key não encontrada!"
    echo ""
    echo "📝 Para obter sua API key:"
    echo "1. Acesse: https://console.anthropic.com/"
    echo "2. Crie uma conta ou faça login"
    echo "3. Vá em 'API Keys' e crie uma nova chave"
    echo ""
    read -p "Cole sua API key aqui: " api_key
    
    # Adicionar ao .bashrc ou .zshrc
    echo "" >> ~/.bashrc
    echo "# Anthropic API Key para Claude" >> ~/.bashrc
    echo "export ANTHROPIC_API_KEY='$api_key'" >> ~/.bashrc
    
    # Exportar para sessão atual
    export ANTHROPIC_API_KEY="$api_key"
    
    echo "✅ API Key configurada!"
else
    echo "✅ API Key já configurada"
fi

# Instalar dependências Python
echo ""
echo "📦 Instalando dependências Python..."
pip install anthropic PyPDF2 pdfplumber

# Instalar ferramentas do sistema
echo ""
echo "🔧 Instalando ferramentas do sistema..."

if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "msys" ]]; then
    # Linux ou WSL
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y poppler-utils
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    if command -v brew &> /dev/null; then
        brew install poppler
    fi
fi

echo ""
echo "✅ Configuração concluída!"
echo ""
echo "📖 Como usar:"
echo ""
echo "1. Análise individual:"
echo "   python claude_mcp_cli.py documents/pending/VALE_3T24.pdf"
echo ""
echo "2. Análise em lote:"
echo "   python claude_mcp_cli.py --batch documents/pending --max-files 3"
echo ""
echo "3. Modo interativo:"
echo "   python claude_mcp_cli.py"
echo ""
echo "💰 Custos estimados:"
echo "   - Claude 3 Opus: ~$0.03-0.05 por PDF"
echo "   - Claude 3 Sonnet: ~$0.01-0.02 por PDF"
echo ""