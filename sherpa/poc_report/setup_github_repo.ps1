# Script PowerShell para configurar o repositório GitHub

Write-Host "=== Configurando repositório finlab_avalon ===" -ForegroundColor Green

# Navegue para a pasta GitHub
cd C:\Users\guilh\documents\GitHub

# Verifique se já existe um repositório Git
if (Test-Path .git) {
    Write-Host "Repositório Git já existe. Usando repositório existente..." -ForegroundColor Yellow
} else {
    Write-Host "Inicializando novo repositório Git..." -ForegroundColor Cyan
    git init
}

# Crie um README se não existir
if (-not (Test-Path README.md)) {
    Write-Host "Criando README.md..." -ForegroundColor Cyan
    @"
# FinLab Avalon

Sistema integrado de análise financeira e trading algorítmico para o mercado brasileiro.

## Estrutura do Projeto

- **avaloncapital/**: Sistema principal de gestão de fundos
- **acompanhamento_fia/**: Tracking de fundos de investimento
- **flab/**: Laboratório de análise financeira
- **les_juros/**: Estratégias de trading em juros
- **database/**: Dados de mercado e carteiras

## Tecnologias

- Python 3.8+
- Pandas, NumPy, yfinance
- MetaTrader5
- FastAPI/Flask
"@ | Out-File -FilePath README.md -Encoding UTF8
}

# Crie .gitignore se não existir
if (-not (Test-Path .gitignore)) {
    Write-Host "Criando .gitignore..." -ForegroundColor Cyan
    @"
# Python
__pycache__/
*.py[cod]
*.pyc
.Python
env/
venv/

# Dados sensíveis
*.pkl
*.xls
*.xlsx
client_secrets.json
api_keys.py
config.py
.env

# IDEs
.vscode/
.idea/

# Logs e temporários
*.log
*.tmp
*.bak

# Dados grandes
*.parquet
*.csv
*.db
"@ | Out-File -FilePath .gitignore -Encoding UTF8
}

Write-Host "`nAdicionando arquivos ao Git..." -ForegroundColor Cyan
git add .

Write-Host "Criando commit inicial..." -ForegroundColor Cyan
git commit -m "first commit: FinLab Avalon - Sistema de análise financeira"

Write-Host "Configurando branch main..." -ForegroundColor Cyan
git branch -M main

Write-Host "Adicionando repositório remoto..." -ForegroundColor Cyan
git remote add origin git@github.com:guipujades/finlab_avalon.git

Write-Host "`n=== Pronto para push! ===" -ForegroundColor Green
Write-Host "Execute o comando abaixo para enviar ao GitHub:" -ForegroundColor Yellow
Write-Host "git push -u origin main" -ForegroundColor Cyan

Write-Host "`nSe houver erro de autenticação SSH, certifique-se de que:" -ForegroundColor Yellow
Write-Host "1. Você tem uma chave SSH configurada no GitHub" -ForegroundColor White
Write-Host "2. Ou use HTTPS: git remote set-url origin https://github.com/guipujades/finlab_avalon.git" -ForegroundColor White