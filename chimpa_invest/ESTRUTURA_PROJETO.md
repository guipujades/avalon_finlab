# 📁 Estrutura do Projeto Chimpa Invest

## 🎯 Visão Geral
Sistema completo para análise de investimentos com foco em fundos e empresas listadas na CVM.

## 📂 Estrutura de Pastas

```
chimpa_invest/
│
├── 📊 SCRIPTS PRINCIPAIS
│   ├── 00_cvm_extrator_dados_ipe.py      # Extrator de dados IPE/CVM
│   ├── 01_cvm_download_releases_multiplas_empresas.py  # Download de releases
│   ├── 02_cvm_download_documentos_estruturados.py     # Download docs estruturados
│   ├── 03_analise_economista.py          # Análise com agente economista
│   ├── document_agent.py                 # Leitor inteligente de documentos
│   ├── valuation_vale_2025.py           # Valuation específico VALE
│   └── valuation_vale_completo.py       # Valuation completo
│
├── 📁 agents/                            # Agentes de IA
│   ├── economist_agent_free.py          # Agente economista
│   └── financial_knowledge.py           # Base de conhecimento financeiro
│
├── 📁 sistema/                           # Sistema unificado
│   ├── extrator_cvm_unificado.py       # Extrator unificado
│   └── gerador_lista_empresas.py       # Gerador de listas
│
├── 📁 documents/                         # Documentos processados
│   ├── cvm_estruturados/                # Docs estruturados CVM
│   ├── parsed/                          # Documentos parseados
│   ├── processed/                       # Documentos processados
│   ├── pending/                         # Aguardando processamento
│   ├── residuals/                       # Documentos residuais
│   └── summaries/                       # Resumos gerados
│
├── 📁 dados/                            # Dados de empresas
│   ├── empresas_cvm_completa.json      # Base completa empresas
│   ├── empresas_cvm_completa.xlsx     # Excel com dados
│   └── indice_busca_empresas.json     # Índice para busca rápida
│
├── 📁 funds_BrFollower/                 # Análise de fundos
│   ├── analise_temporal_fundos.py      # Script principal fundos
│   ├── demo_apresentacao.py            # Demo interativa
│   └── dados/                          # Saída das análises
│
├── 📁 docs/                             # Documentação
│   ├── CHANGELOG.md                    # Histórico de mudanças
│   └── GUIA_DOWNLOAD.md               # Guia de download
│
├── 📁 valuations/                       # Resultados valuations
├── 📁 cache_analises/                   # Cache de análises
├── 📁 analises_mcp/                     # Análises MCP
│
├── 📄 requirements.txt                  # Dependências Python
├── 📄 requirements_agents.txt           # Dependências agentes
└── 📄 README_SISTEMA_CVM.md            # Documentação principal
```

## 🚀 Como Usar

### 1. Download de Dados CVM
```bash
# Extrair dados IPE
python 00_cvm_extrator_dados_ipe.py

# Download releases múltiplas empresas
python 01_cvm_download_releases_multiplas_empresas.py

# Download documentos estruturados
python 02_cvm_download_documentos_estruturados.py
```

### 2. Análise de Documentos
```bash
# Processar PDFs com agente
python document_agent.py

# Análise econômica
python 03_analise_economista.py
```

### 3. Valuation
```bash
# Valuation completo da VALE
python valuation_vale_completo.py
```

### 4. Análise de Fundos
```bash
cd funds_BrFollower
python analise_temporal_fundos.py [CNPJ]
```

## 📋 Arquivos Essenciais

- **Extração de Dados**: Scripts 00, 01, 02
- **Análise**: document_agent.py, 03_analise_economista.py
- **Valuation**: valuation_vale_*.py
- **Fundos**: funds_BrFollower/analise_temporal_fundos.py

## 🗑️ Limpeza
Arquivos de teste e desenvolvimento foram movidos para `trash/`