# Seções de Lévy para Detecção de Quebras Estruturais

## Resumo

Implementação do método das seções de Lévy para detectar quebras estruturais em séries temporais financeiras, baseado no artigo de Figueiredo et al. (2022) e adaptado para o projeto CrunchDAO SB.

## O que são Seções de Lévy?

As seções de Lévy são uma metodologia que transforma séries temporais do "tempo de calendário" para o "tempo de volatilidade". Em vez de analisar retornos em intervalos fixos (diários, semanais), o método agrupa os dados em seções onde cada uma acumula uma quantidade fixa de risco (variância).

### Principais Conceitos:

1. **Parada Estocástica**: Cada seção termina quando a variância acumulada atinge um limiar τ (tau)
2. **Duração Variável**: O tempo necessário para completar cada seção (δ_tau) é inversamente proporcional à volatilidade
3. **Detecção de Quebras**: Mudanças abruptas nas durações indicam quebras estruturais no regime de volatilidade

## Estrutura da Implementação

```
crunchdao_SB/
├── src/features/
│   └── levy_sections.py          # Classe principal LevySectionsAnalyzer
├── examples/
│   └── levy_structural_breaks_demo.py  # Demonstração completa
├── notebooks/
│   └── levy_sections_analysis.ipynb    # Análise interativa
├── levy_structural_breaks.R     # Implementação original em R
└── docs/
    └── levy_sections_README.md   # Este arquivo
```

## Como Usar

### Python - Exemplo Básico

```python
from src.features.levy_sections import LevySectionsAnalyzer
import numpy as np

# Calcular log-retornos
returns = np.log(prices[1:] / prices[:-1])

# Criar analisador
analyzer = LevySectionsAnalyzer(tau=0.005, q=5)

# Calcular seções de Lévy
result = analyzer.compute_levy_sections(returns)

# Detectar quebras estruturais
breaks = analyzer.detect_structural_breaks()

# Extrair features para ML
features = analyzer.extract_features()
```

### R - Exemplo Básico

```r
source("levy_structural_breaks.R")

# Calcular seções com detecção de quebras
res_levy <- compute_levy_sections_with_durations(
  log_returns = returns,
  dates = dates,
  tau = 0.005,
  q = 5
)

# Detectar quebras
res_breaks <- detect_structural_breaks(res_levy$durations, res_levy$start_dates)
```

## Parâmetros Principais

- **tau (τ)**: Limiar de variância acumulada que define o fim de cada seção
  - Valores típicos: 0.001 a 0.05
  - Menor tau → mais seções, detecção mais rápida
  - Maior tau → menos seções, sinal mais robusto

- **q**: Semi-largura da janela para estimar volatilidade local
  - Valores típicos: 3 a 15
  - Menor q → mais reativo a mudanças rápidas
  - Maior q → estimativa mais suave

## Features Extraídas

### Features das Durações (δ_tau)
- `levy_duration_mean`: Tempo médio para acumular risco τ
- `levy_duration_cv`: Coeficiente de variação das durações
- `levy_duration_kurtosis`: Curtose das durações
- `levy_duration_autocorr`: Autocorrelação das durações

### Features das Somas Seccionais (S_tau)
- `levy_sum_kurtosis`: Curtose das somas (deve tender a 0)
- `levy_norm_var_ratio`: Razão de variância normalizada (deve tender a 1)
- `levy_shapiro_pvalue`: P-valor do teste de normalidade

## Interpretação dos Resultados

### Quebras Estruturais
- **Razão < 0.7**: Aumento significativo de volatilidade
- **Razão > 1.3**: Redução significativa de volatilidade
- **P-valor < 0.01**: Quebra estatisticamente significativa

### Exemplos de Eventos Detectados
- COVID-19 (Mar/2020): Razão ~0.3 (forte aumento de volatilidade)
- Recuperação (Abr/2020): Razão ~2.5 (redução de volatilidade)
- Crise bancária SVB (Mar/2023): Razão ~0.5

## Vantagens do Método

1. **Robustez**: Não assume modelo paramétrico para volatilidade
2. **Adaptabilidade**: Ajusta-se automaticamente a mudanças de regime
3. **Interpretabilidade**: Resultados têm significado econômico claro
4. **Eficiência**: Complexidade computacional O(n)

## Integração com Machine Learning

As features de Lévy podem ser combinadas com TSFresh:

```python
# TSFresh features
tsfresh_features = extract_features(data)

# Lévy features  
levy_features = analyzer.extract_features()

# Combinar
all_features = {**tsfresh_features, **levy_features}
```

## Aplicações Práticas

1. **Detecção de Crises**: Identificar início de períodos turbulentos
2. **Gestão de Risco**: Ajustar exposição baseado em mudanças de regime
3. **Feature Engineering**: Melhorar modelos de classificação/previsão
4. **Análise de Mercado**: Comparar regimes de volatilidade entre ativos

## Referências

- Figueiredo, A., et al. (2022). "Using the Lévy sections to reduce risks in the buying strategies and asset sales that value in time." *Communications in Nonlinear Science and Numerical Simulation*, 104, 106023.
- Nascimento, C. M., et al. (2011). "Lévy sections vs. partial sums of heteroscedastic time series." *EPL (Europhysics Letters)*, 96(6), 68004.

## Contribuições

Para contribuir com melhorias:
1. Fork o repositório
2. Crie uma branch para sua feature
3. Adicione testes unitários
4. Submeta um pull request

## Licença

Este código faz parte do projeto CrunchDAO SB e segue a mesma licença do projeto principal.