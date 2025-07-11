#!/bin/bash

# Script para renomear a pasta GitHub para avalon_finlab e criar repositório Git

echo "=== Renomeando pasta GitHub para avalon_finlab ==="

# Caminho base
BASE_PATH="/mnt/c/Users/guilh/documents"

# Verificar se a pasta GitHub existe
if [ ! -d "$BASE_PATH/GitHub" ]; then
    echo "Erro: Pasta GitHub não encontrada em $BASE_PATH"
    exit 1
fi

# Verificar se já existe uma pasta avalon_finlab
if [ -d "$BASE_PATH/avalon_finlab" ]; then
    echo "Erro: Já existe uma pasta avalon_finlab em $BASE_PATH"
    echo "Por favor, remova ou renomeie a pasta existente primeiro"
    exit 1
fi

# Renomear a pasta
echo "Renomeando GitHub para avalon_finlab..."
mv "$BASE_PATH/GitHub" "$BASE_PATH/avalon_finlab"

if [ $? -eq 0 ]; then
    echo "✓ Pasta renomeada com sucesso!"
    
    # Navegar para a nova pasta
    cd "$BASE_PATH/avalon_finlab"
    
    echo ""
    echo "=== Inicializando repositório Git ==="
    
    # Inicializar Git
    git init
    
    # Criar .gitignore
    echo "Criando arquivo .gitignore..."
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environment
env/
venv/
ENV/
env.bak/
venv.bak/

# Dados e arquivos sensíveis
*.pkl
*.pickle
*.xls
*.xlsx
*.parquet
client_secrets.json
api_keys.py
config.py
credentials.json
.env
.env.*

# Logs
*.log
logs/

# Jupyter Notebook
.ipynb_checkpoints
*.ipynb_checkpoints/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Dados temporários
*.tmp
*.bak
*.cache
temp/
tmp/

# Arquivos grandes de dados
dados_api/
*.csv
*.json
*.db
*.sqlite

# Captcha e downloads
captcha.png
chromedriver.exe
*.zip
*.tar.gz

# MetaTrader
*.ex5
*.mqh
EOF

    # Criar README.md
    echo "Criando README.md..."
    cat > README.md << 'EOF'
# Avalon FinLab

Sistema integrado de análise financeira e trading algorítmico para o mercado brasileiro.

## Estrutura do Projeto

### 📁 avaloncapital/
Sistema principal de gestão de fundos e análise quantitativa
- **aurora/**: Sistema de backtesting e otimização de portfólio
- **api_btg/**: Integração com APIs do BTG Pactual
- **precificacao/**: Módulos de precificação de renda fixa
- **futures/**: Estratégias de trading em futuros

### 📁 acompanhamento_fia/
Sistema de tracking e análise de fundos de investimento
- Cálculo de VaR (Value at Risk)
- Processamento de notas de corretagem
- Análise de performance

### 📁 flab/
Laboratório de análise financeira
- Análise consolidada de carteiras
- Métricas de performance e risco
- Geração de relatórios estatísticos

### 📁 les_juros/
Estratégias de trading em juros e renda fixa
- Pairs trading em contratos DI
- Análise de estrutura a termo
- Backtesting de estratégias

### 📁 poc_InvestmentOrchestrator/
Sistema orquestrador com arquitetura de agentes
- Agentes especializados em pesquisa financeira
- Sistema de memória compartilhada
- Integração com múltiplas APIs

### 📁 database/
Dados de mercado e carteiras
- Histórico de preços
- Composição de carteiras
- Dados fundamentalistas

## Tecnologias Utilizadas

- **Python 3.8+**
- **Pandas, NumPy**: Análise de dados
- **yfinance**: Dados de mercado
- **MetaTrader5**: Conexão com plataforma de trading
- **FastAPI/Flask**: APIs web
- **PostgreSQL/Supabase**: Armazenamento de dados

## Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/avalon_finlab.git
cd avalon_finlab

# Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instale as dependências
pip install -r requirements.txt
```

## Configuração

1. Configure as variáveis de ambiente no arquivo `.env`
2. Configure as credenciais das APIs em `config.py`
3. Ajuste os parâmetros de trading conforme necessário

## Contribuição

Pull requests são bem-vindos. Para mudanças importantes, abra uma issue primeiro para discutir as alterações propostas.

## Licença

Proprietary - Todos os direitos reservados

---

**Aviso**: Este sistema contém estratégias proprietárias de trading. O uso não autorizado é estritamente proibido.
EOF

    echo "✓ .gitignore criado"
    echo "✓ README.md criado"
    
    echo ""
    echo "=== Próximos passos ==="
    echo "1. Revise os arquivos sensíveis antes de fazer commit"
    echo "2. Execute os seguintes comandos para criar o repositório:"
    echo ""
    echo "   cd $BASE_PATH/avalon_finlab"
    echo "   git add ."
    echo "   git commit -m \"Initial commit: Avalon FinLab - Sistema de análise financeira\""
    echo ""
    echo "3. Crie um repositório no GitHub chamado 'avalon_finlab'"
    echo "4. Conecte o repositório local ao GitHub:"
    echo ""
    echo "   git remote add origin https://github.com/SEU_USUARIO/avalon_finlab.git"
    echo "   git branch -M main"
    echo "   git push -u origin main"
    echo ""
    echo "✓ Script concluído com sucesso!"
else
    echo "❌ Erro ao renomear a pasta"
    exit 1
fi