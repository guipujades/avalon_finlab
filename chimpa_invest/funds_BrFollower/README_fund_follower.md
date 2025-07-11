# Fund Follower - Sistema de Replicação de Fundos

Sistema para replicar o comportamento de um fundo alvo sem conhecer sua composição, minimizando o tracking error.

## 📋 Descrição

O Fund Follower é um sistema que tenta replicar a curva de retorno de um fundo alvo (target) usando apenas:
- Histórico de retornos do fundo alvo
- Universo de fundos/ativos disponíveis no mercado
- Técnicas de otimização para minimizar tracking error

### Versões Implementadas

1. **Versão Otimizada**: Usa otimização para encontrar pesos que minimizam o tracking error
2. **Versão Benchmark**: Seleciona fundos baseado apenas na proximidade do beta

## 🚀 Como Usar

### 1. Preparação dos Dados

Primeiro, extraia os retornos do universo de fundos:

```python
python extrair_retornos_universo.py
```

Escolha:
- Opção 1: Extração completa (todos os fundos)
- Opção 2: Amostra pequena (100 fundos) - recomendado para testes

### 2. Executar o Fund Follower

```python
python exemplo_fund_follower.py
```

Escolha:
- Opção 1: Exemplo completo com dados reais
- Opção 2: Exemplo benchmark com dados sintéticos

### 3. Uso Programático

```python
from fund_follower_base import FundFollower

# Inicializar
follower = FundFollower("38.351.476/0001-40", "KOKORIKUS FI AÇÕES")

# Carregar dados
follower.load_target_returns()
follower.load_universe_returns(df_universo)

# Dividir dados (treino/teste)
follower.split_data(train_ratio=0.4)

# Otimizar
follower.optimize_weights_minimum_tracking_error()

# Avaliar
follower.evaluate_out_of_sample()
```

## 📊 Métricas

O sistema calcula:
- **Tracking Error**: Desvio padrão das diferenças de retorno (anualizado)
- **Correlação**: Entre o portfolio replicante e o fundo alvo
- **Beta**: Sensibilidade ao mercado (para versão benchmark)
- **Retornos acumulados**: Comparação visual de performance

## 📁 Estrutura de Arquivos

```
funds_BrFollower/
├── fund_follower_base.py      # Classe principal FundFollower
├── extrair_retornos_universo.py # Extração de retornos da CVM
├── exemplo_fund_follower.py    # Exemplos de uso
├── dados_universo/             # Dados extraídos
│   ├── retornos_mensais_universo.csv
│   ├── retornos_mensais_universo.pkl
│   └── info_fundos.csv
└── resultados_fund_follower/   # Resultados da análise
    ├── fund_follower_results.csv
    └── optimal_weights.csv
```

## 🔧 Próximos Passos

Para incluir outros ativos além de fundos, você precisará:

1. **Ações**: Baixar dados do Yahoo Finance ou outra fonte
2. **Renda Fixa**: Incluir índices como IMA-B, IMA-S
3. **ETFs**: Adicionar ETFs brasileiros disponíveis

Exemplo para adicionar ações:

```python
import yfinance as yf

# Baixar dados de ações
tickers = ['PETR4.SA', 'VALE3.SA', 'ITUB4.SA']
dados_acoes = yf.download(tickers, start='2020-01-01', end='2024-08-31')

# Calcular retornos mensais
retornos_acoes = dados_acoes['Adj Close'].pct_change().resample('M').apply(
    lambda x: (1 + x).prod() - 1
)

# Combinar com universo de fundos
universo_completo = pd.concat([df_fundos, retornos_acoes], axis=1)
```

## 📈 Melhorias Futuras

1. **Restrições adicionais**: 
   - Limites de concentração por ativo
   - Restrições de liquidez
   - Custos de transação

2. **Métodos alternativos**:
   - Regressão LASSO para seleção de ativos
   - Machine Learning (Random Forest, XGBoost)
   - Análise de estilo (style analysis)

3. **Métricas adicionais**:
   - Information Ratio
   - Downside deviation
   - Maximum drawdown

## ⚠️ Limitações

- Assume que retornos passados têm alguma persistência
- Não considera custos de transação
- Requer histórico suficiente (mínimo 2 anos)
- Performance out-of-sample pode variar significativamente

## 📝 Notas

- Os primeiros 40% dos dados são usados para treino (in-sample)
- Os 60% restantes são usados para teste (out-of-sample)
- O sistema funciona melhor com universos amplos de ativos