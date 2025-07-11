# Como Executar a Análise de Quebras Estruturais com Seções de Lévy

## Instalação Rápida

```bash
# 1. Instalar dependências
pip install -r requirements_levy.txt

# 2. Executar análise básica (IBOVESPA)
python run_levy_analysis.py

# 3. Ver resultados
# Abra a pasta outputs/ para visualizações e dados
```

## Guia de Uso Completo

### 1. Análise de Um Único Ativo

```bash
# Exemplo básico - Petrobras
python run_levy_analysis.py --ticker PETR4.SA

# Com período específico
python run_levy_analysis.py --ticker VALE3.SA --start 2020-01-01 --end 2024-12-31

# Com parâmetros customizados
python run_levy_analysis.py --ticker ITUB4.SA --tau 0.01 --q 10

# Análise multi-tau (testa vários valores de tau)
python run_levy_analysis.py --ticker ^BVSP --multi-tau

# Sem salvar arquivos (apenas visualizar)
python run_levy_analysis.py --ticker BTC-USD --no-save
```

### 2. Análise em Lote (Múltiplos Ativos)

```bash
# Lista específica de ativos
python run_levy_batch.py --tickers PETR4.SA VALE3.SA ITUB4.SA BBDC4.SA

# Usando arquivo de configuração
python run_levy_batch.py --config batch_config_example.json

# Com processamento paralelo
python run_levy_batch.py --workers 8 --tickers PETR4.SA VALE3.SA ITUB4.SA
```

### 3. Parâmetros Disponíveis

#### run_levy_analysis.py
- `--ticker`: Símbolo do ativo (padrão: ^BVSP)
- `--start`: Data inicial YYYY-MM-DD (padrão: 2019-01-01)
- `--end`: Data final YYYY-MM-DD (padrão: 2024-12-31)
- `--tau`: Limiar de variância acumulada (padrão: 0.005)
- `--q`: Janela para volatilidade local (padrão: 5)
- `--multi-tau`: Testar múltiplos valores de tau
- `--no-save`: Não salvar resultados em arquivos

#### run_levy_batch.py
- `--config`: Arquivo JSON com configuração
- `--tickers`: Lista de tickers para analisar
- `--start`, `--end`, `--tau`, `--q`: Mesmos do script individual
- `--workers`: Número de processos paralelos (padrão: 4)

## Exemplos de Tickers

### Índices
- `^BVSP`: Ibovespa
- `^GSPC`: S&P 500
- `^DJI`: Dow Jones
- `^IXIC`: Nasdaq

### Ações Brasileiras
- Adicione `.SA` ao código: `PETR4.SA`, `VALE3.SA`, `ITUB4.SA`

### Criptomoedas
- `BTC-USD`: Bitcoin
- `ETH-USD`: Ethereum

### Commodities
- `GC=F`: Ouro
- `CL=F`: Petróleo

## Interpretação dos Resultados

### 1. Arquivos Gerados

```
outputs/
├── figures/              # Visualizações
│   └── levy_PETR4_SA_*.png
├── data/                 # Dados processados
│   ├── breaks_*.csv      # Quebras detectadas
│   ├── features_*.csv    # Features extraídas
│   └── durations_*.csv   # Durações das seções
└── summary_*.txt         # Relatório resumido
```

### 2. Quebras Estruturais

No arquivo `breaks_*.csv`:
- `date`: Data da quebra
- `mean_before/after`: Duração média antes/depois
- `change_ratio`: Razão de mudança
  - < 0.7: Aumento de volatilidade
  - > 1.3: Redução de volatilidade
- `p_value`: Significância estatística

### 3. Features para ML

No arquivo `features_*.csv`:
- `levy_duration_mean`: Tempo médio das seções
- `levy_duration_cv`: Coeficiente de variação
- `levy_norm_kurtosis`: Curtose normalizada (próximo a 0 = sucesso)
- `levy_shapiro_pvalue`: Teste de normalidade

## Casos de Uso

### 1. Detecção de Crises
```bash
# Analisar período COVID-19
python run_levy_analysis.py --ticker ^BVSP --start 2019-06-01 --end 2021-06-01
```

### 2. Comparação de Ativos
```bash
# Comparar volatilidade de diferentes setores
python run_levy_batch.py --tickers PETR4.SA VALE3.SA ITUB4.SA MGLU3.SA
```

### 3. Otimização de Parâmetros
```bash
# Testar diferentes configurações
for tau in 0.001 0.005 0.01 0.02; do
    python run_levy_analysis.py --ticker PETR4.SA --tau $tau
done
```

## Solução de Problemas

### Erro: "No data found"
- Verifique se o ticker está correto
- Para ações brasileiras, adicione `.SA`
- Verifique se o período tem dados disponíveis

### Erro: "Module not found"
```bash
# Reinstalar dependências
pip install -r requirements_levy.txt
```

### Análise muito lenta
- Reduza o período analisado
- Use menos workers no modo batch
- Aumente o valor de tau (menos seções)

## Integração com Outros Sistemas

### Exportar para Excel
Os resultados já são salvos em CSV, facilmente importáveis no Excel.

### Usar em Python
```python
from src.features.levy_sections import LevySectionsAnalyzer

# Seus dados
analyzer = LevySectionsAnalyzer(tau=0.005, q=5)
result = analyzer.compute_levy_sections(returns)
features = analyzer.extract_features()
```

### Automatização
Crie um script cron/scheduler para executar análises periódicas:
```bash
#!/bin/bash
# daily_analysis.sh
python run_levy_batch.py --config daily_stocks.json
```

## Suporte

Para dúvidas ou problemas:
1. Verifique os logs em outputs/
2. Consulte a documentação em docs/levy_sections_README.md
3. Abra uma issue no repositório