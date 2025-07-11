# Estratégia de Pairs Trading com Contratos DI

## Visão Geral

Esta estratégia implementa pairs trading (arbitragem estatística) entre contratos DI futuros de diferentes vencimentos, explorando a reversão à média do spread entre as taxas.

## Arquivos

### 1. `estrategia_pairs_di.py`
Implementação principal da estratégia com classe `DiPairsTrading`.

### 2. `test_pairs_strategy.py`
Script de teste e otimização integrado com os utilitários existentes.

## Como Funciona

### Conceito Base
- Monitora o **spread** (diferença) entre dois DIs de vencimentos diferentes
- Usa **Bandas de Bollinger** para identificar desvios extremos
- Opera quando o spread sai das bandas, esperando reversão à média

### Sinais de Trading

#### Compra Spread (Posição Long)
- **Condição**: Spread < Banda Inferior
- **Operação**: Compra DI longo + Vende DI curto
- **Saída**: Quando spread volta à média móvel

#### Venda Spread (Posição Short)
- **Condição**: Spread > Banda Superior
- **Operação**: Vende DI longo + Compra DI curto
- **Saída**: Quando spread volta à média móvel

## Exemplo de Uso

```python
from estrategia_pairs_di import DiPairsTrading
import pickle
import pandas as pd

# Carrega dados
with open('futures_v2.pkl', 'rb') as f:
    df = pickle.load(f)

# Cria estratégia
strategy = DiPairsTrading(
    di_long='DI1F25',    # DI Janeiro 2025
    di_short='DI1F26',   # DI Janeiro 2026
    window=20,           # Janela de 20 dias
    n_std=2.0           # 2 desvios padrão
)

# Define vencimentos
venc_long = pd.Timestamp('2025-01-02')
venc_short = pd.Timestamp('2026-01-02')

# Executa backtest
results = strategy.backtest(df, venc_long, venc_short)

# Plota resultados
strategy.plot_strategy(results)
```

## Parâmetros Otimizáveis

### 1. **Window (Janela)**
- **Padrão**: 20 dias
- **Range típico**: 15-30 dias
- **Impacto**: Janelas menores = mais sinais, mais ruído

### 2. **N_Std (Desvios Padrão)**
- **Padrão**: 2.0
- **Range típico**: 1.5-3.0
- **Impacto**: Valores maiores = menos sinais, maior confiabilidade

### 3. **Custo Operacional**
- **Padrão**: 5 pontos por operação
- **Considerar**: Slippage, taxas de bolsa, corretagem

## Métricas de Performance

### Principais Indicadores
- **Win Rate**: Taxa de acerto (ideal > 55%)
- **Sharpe Ratio**: Retorno ajustado ao risco (ideal > 1.0)
- **Resultado Médio**: Ganho médio por trade
- **Drawdown Máximo**: Maior perda acumulada

### Exemplo de Output
```
=== MÉTRICAS DA ESTRATÉGIA ===
total_trades: 25
wins: 16
losses: 9
win_rate: 64.00%
resultado_medio: 15.20
resultado_total: 380.00
sharpe_ratio: 1.35
```

## Análise de Correlação

O script `test_pairs_strategy.py` inclui análise automática de correlação para identificar os melhores pares:

```python
# Identifica pares com correlação entre 0.9 e 0.99
good_pairs = analyze_di_correlations(df, di_list)
```

## Otimização de Parâmetros

Grid search automático para encontrar melhores parâmetros:

```python
# Testa combinações de window e n_std
best_params, best_results = optimize_parameters(
    df, di_long, di_short, venc_long, venc_short
)
```

## Riscos e Considerações

### 1. **Risco de Quebra de Correlação**
- Pares podem descolar permanentemente
- Solução: Stop loss baseado em desvio máximo

### 2. **Eventos de Mercado**
- Decisões do COPOM podem alterar dinâmica
- Solução: Evitar operar próximo a reuniões

### 3. **Liquidez**
- Vencimentos longos têm menor liquidez
- Solução: Focar em vencimentos até 2 anos

### 4. **Custos Operacionais**
- Slippage pode ser significativo
- Solução: Considerar custos realistas no backtest

## Melhorias Sugeridas

1. **Stop Loss Dinâmico**
```python
if abs(spread_atual - entrada_spread) > 3 * desvio_padrao:
    fecha_posicao()  # Stop loss
```

2. **Filtros Adicionais**
- Volume mínimo
- Horário de operação
- Volatilidade do mercado

3. **Position Sizing**
- Ajustar tamanho baseado em volatilidade
- Kelly Criterion para otimização

4. **Machine Learning**
- Prever melhor momento de entrada
- Classificador para qualidade do sinal

## Execução Completa

Para rodar análise completa com otimização:

```bash
python test_pairs_strategy.py
```

Isso irá:
1. Analisar correlações entre DIs
2. Otimizar parâmetros para melhor par
3. Gerar relatório detalhado
4. Plotar gráficos de performance

## Interpretação dos Gráficos

### Gráfico Superior: Spread e Bandas
- **Linha azul**: Spread entre os DIs
- **Linha preta tracejada**: Média móvel
- **Linhas vermelha/verde pontilhadas**: Bandas de Bollinger
- **Triângulos verdes**: Compra spread
- **Triângulos vermelhos**: Venda spread
- **X preto**: Fechamento de posição

### Gráfico Inferior: Performance Acumulada
- Mostra evolução do resultado ao longo do tempo
- Permite identificar períodos de drawdown

## Conclusão

Esta estratégia é robusta para mercados com alta correlação entre vencimentos. O sucesso depende de:
- Escolha adequada dos pares
- Otimização dos parâmetros
- Gestão de risco apropriada
- Custos operacionais realistas

Para mercados brasileiros de DI, historicamente apresenta bons resultados com Sharpe Ratio > 1.0 quando bem parametrizada.