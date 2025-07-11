# 🚀 Claude API CLI - Análise de PDFs via Linha de Comando

## ✅ O que este sistema faz

Este sistema permite usar o Claude via API para analisar PDFs financeiros diretamente da linha de comando, sem precisar do Claude Desktop.

### Funcionalidades:
- 📄 Analisa PDFs individuais
- 📊 Análise em lote de múltiplos PDFs
- 💰 Calcula custos automaticamente
- 💾 Salva resultados em JSON
- 🔍 Extrai métricas financeiras estruturadas

## 🛠️ Instalação

### 1. Obter API Key da Anthropic
```bash
# Acesse: https://console.anthropic.com/
# Crie uma conta e gere uma API key
```

### 2. Configurar API Key
```bash
# Linux/macOS/WSL
export ANTHROPIC_API_KEY='sua-chave-aqui'

# Adicionar ao .bashrc para persistir
echo "export ANTHROPIC_API_KEY='sua-chave-aqui'" >> ~/.bashrc
```

### 3. Instalar Dependências
```bash
# Dependências Python
pip install anthropic PyPDF2 pdfplumber

# Ferramentas do sistema (opcional, mas recomendado)
# Linux/WSL
sudo apt-get install poppler-utils

# macOS
brew install poppler
```

## 📖 Como Usar

### Análise Individual
```bash
python claude_mcp_cli.py documents/pending/VALE_3T24.pdf
```

### Análise em Lote
```bash
# Analisa até 5 PDFs da pasta
python claude_mcp_cli.py --batch documents/pending --max-files 5
```

### Modo Interativo
```bash
# Lista PDFs e permite escolher
python claude_mcp_cli.py
```

### Com API Key Específica
```bash
python claude_mcp_cli.py --api-key sk-ant-... arquivo.pdf
```

## 💰 Custos

| Modelo | Input | Output | Custo por PDF |
|--------|-------|--------|---------------|
| Claude 3 Opus | $15/M tokens | $75/M tokens | ~$0.03-0.05 |
| Claude 3 Sonnet | $3/M tokens | $15/M tokens | ~$0.01-0.02 |
| Claude 3 Haiku | $0.25/M tokens | $1.25/M tokens | ~$0.001-0.002 |

## 📊 Exemplo de Saída

```json
{
  "status": "success",
  "pdf": "VALE_3T24.pdf",
  "analysis": {
    "empresa": {
      "nome": "Vale S.A.",
      "periodo": "3T24"
    },
    "metricas_financeiras": {
      "receita": {
        "valor": 11784,
        "moeda": "USD",
        "unidade": "milhões",
        "variacao_yoy": -15.2
      },
      "ebitda": {
        "valor": 4821,
        "margem": 40.9,
        "variacao_yoy": -25.3
      }
    },
    "destaques": [
      "Produção recorde de cobre",
      "Melhoria de margens no minério"
    ],
    "riscos": [
      "Pressão de custos energéticos",
      "Demanda chinesa volátil"
    ]
  },
  "usage": {
    "input_tokens": 15234,
    "output_tokens": 892,
    "cost_usd": 0.0315
  }
}
```

## 🔧 Limitações e Soluções

### Limitação Atual
A API do Claude não suporta upload direto de PDFs (ainda). Por isso, o sistema:
1. Extrai o texto do PDF localmente
2. Envia o texto para análise

### Vantagens desta Abordagem
- ✅ Funciona hoje com a API disponível
- ✅ Controle total sobre o processo
- ✅ Pode pré-processar e limpar dados
- ✅ Funciona via CLI sem interface gráfica

### Quando o MCP Estiver Disponível via API
No futuro, quando a Anthropic liberar MCP via API, poderemos:
```python
# Futuro - não funciona ainda
response = client.messages.create(
    model="claude-3-opus",
    attachments=[
        {
            "type": "application/pdf",
            "path": "/path/to/file.pdf"
        }
    ],
    messages=[...]
)
```

## 🎯 Casos de Uso

### 1. Análise Rápida de Earnings
```bash
# Baixar releases
python cvm_download_principal.py  # Opção 3

# Analisar todos
python claude_mcp_cli.py --batch documents/pending --max-files 10
```

### 2. Comparação Trimestral
```bash
# Analisar múltiplos trimestres
for pdf in VALE_*T24.pdf; do
    python claude_mcp_cli.py "$pdf"
done
```

### 3. Pipeline Automatizado
```python
# pipeline.py
import subprocess
from pathlib import Path

# 1. Baixar PDFs
subprocess.run(["python", "01_cvm_download_releases_multiplas_empresas.py"])

# 2. Analisar com Claude
pdfs = Path("documents/pending").glob("*.pdf")
for pdf in pdfs:
    subprocess.run(["python", "claude_mcp_cli.py", str(pdf)])

# 3. Consolidar resultados
# ... processar JSONs gerados
```

## 📝 Notas Importantes

1. **Tamanho dos PDFs**: PDFs muito grandes (>50 páginas) podem ser truncados
2. **Rate Limits**: A API tem limites de requisições por minuto
3. **Custos**: Monitore o uso para controlar custos
4. **Qualidade**: Claude 3 Opus dá melhores resultados, mas é mais caro

## 🚀 Próximos Passos

1. **Otimizar Extração**: Melhorar extração de tabelas
2. **Cache Inteligente**: Evitar reanalisar PDFs já processados
3. **Integração com Banco**: Salvar resultados em database
4. **Dashboard**: Criar visualização dos resultados

---

**Resumo**: Este sistema permite análise profissional de PDFs financeiros via CLI, usando a API do Claude para processar e extrair insights estruturados.