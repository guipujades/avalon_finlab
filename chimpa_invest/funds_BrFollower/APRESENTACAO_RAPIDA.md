# 🚀 GUIA RÁPIDO PARA APRESENTAÇÃO

## DEMONSTRAÇÃO EM 3 MINUTOS

### 1️⃣ Mostrar o Sistema Funcionando
```bash
# Abrir terminal na pasta:
cd C:\Users\guilh\Documents\GitHub\chimpa_invest\funds_BrFollower

# Executar demonstração interativa:
python demo_apresentacao.py
```

### 2️⃣ Análise Rápida - Capstone
```bash
python analise_temporal_fundos.py 35.803.288/0001-17
```

**Mostrar:**
- Terminal processando dados
- Pasta `dados\35803288000117\` criada
- Abrir `relatorio_temporal.html` no navegador
- Mostrar gráfico `analise_temporal.png`

### 3️⃣ Pontos-Chave da Apresentação

#### O QUE O SISTEMA FAZ:
✅ Analisa fundos de investimento com dados oficiais CVM
✅ Processa últimos 5 anos automaticamente
✅ Calcula indicadores de performance
✅ Gera relatórios visuais automáticos
✅ Exporta dados em múltiplos formatos

#### DIFERENCIAIS:
📊 **10 visualizações** automáticas
📈 **Indicadores profissionais**: Sharpe, Volatilidade, Drawdown
💾 **3 formatos de dados**: Pickle, JSON, CSV
🌐 **Relatório HTML** interativo

#### EXEMPLO PRÁTICO:
"Com apenas 1 comando, analisamos 5 anos de dados do fundo Capstone,
gerando relatório completo com indicadores de risco e retorno"

## COMANDOS ESSENCIAIS

```bash
# 1. Análise básica
python analise_temporal_fundos.py [CNPJ]

# 2. Com nome personalizado
python analise_temporal_fundos.py [CNPJ] --nome "Nome do Fundo"

# 3. Exportar só CSV
python analise_temporal_fundos.py [CNPJ] --formato csv
```

## ESTRUTURA GERADA
```
dados/
└── 35803288000117/
    ├── analise_temporal.png      ← Abrir este
    ├── relatorio_temporal.html   ← Mostrar este
    ├── dados_fundo.pkl
    ├── dados_fundo.json
    └── csv/
        └── [6 arquivos CSV]
```

## SE DER ERRO
- Verificar se está na pasta correta
- Usar Capstone: `35.803.288/0001-17`
- Mostrar que funciona mesmo sem cotas

## FECHAR COM CHAVE DE OURO
"Sistema pronto para produção, processa qualquer fundo brasileiro
em segundos, gerando análise profissional completa"