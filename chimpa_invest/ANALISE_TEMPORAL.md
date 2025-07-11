# Análise Temporal de Valuation

## Visão Geral

O sistema de valuation agora suporta duas modalidades de análise:

### 1. Análise Pontual (Padrão)
- Calcula indicadores do **último período disponível**
- Rápida e direta
- Ideal para snapshot atual da empresa

```bash
python valuation_empresa.py VALE3
```

### 2. Análise Temporal
- Calcula indicadores para **todos os períodos disponíveis**
- Mostra evolução ao longo do tempo
- Permite identificar tendências

```bash
# Opção 1: Flag no script principal
python valuation_empresa.py VALE3 --temporal

# Opção 2: Script dedicado com gráficos
python valuation_empresa_temporal.py VALE3
```

## Diferenças Principais

### Análise Pontual
```python
# Pega apenas o último período
ultimo_bal = self.bal.iloc[-1]
ultimo_dre = self.dre.iloc[-1]
```

**Resultado**: Um valor para cada indicador

### Análise Temporal
```python
# Calcula para todos os períodos
for data in datas_comuns:
    # Calcula indicadores para cada data
    metricas_periodo['roe'] = (lucro / pl) * 100
```

**Resultado**: Série histórica de cada indicador

## Exemplos de Uso

### 1. Análise Básica Temporal
```bash
python valuation_empresa.py PETR4 --temporal --preco 38.50
```

Mostra:
- Métricas do último período
- Evolução dos últimos 3 períodos
- Tendências de margem e rentabilidade

### 2. Análise Completa com Gráficos
```bash
python valuation_empresa_temporal.py VALE3 --anos 5
```

Gera:
- Relatório JSON completo com séries temporais
- Gráficos de evolução (receita, margens, ROE, endividamento)
- Estatísticas dos últimos 5 anos (média, mediana, min/max)

## Indicadores Temporais Calculados

### Demonstrações Financeiras
- Receita Líquida (evolução)
- Lucro Líquido (evolução)
- EBIT e EBITDA (evolução)

### Margens (%)
- Margem Bruta
- Margem EBIT
- Margem EBITDA
- Margem Líquida

### Rentabilidade (%)
- ROE (Return on Equity)
- ROA (Return on Assets)
- ROIC (Return on Invested Capital)

### Liquidez e Endividamento
- Liquidez Corrente
- Dívida/PL
- Dívida/EBITDA

### Indicadores de Prazos (dias)
- PMR (Prazo Médio de Recebimento)
- PME (Prazo Médio de Estocagem)
- PMP (Prazo Médio de Pagamento)
- Ciclo de Caixa

## Interpretação dos Resultados

### 1. Tendências Positivas
- Margens crescentes
- ROE estável ou crescente
- Dívida/EBITDA decrescente
- Ciclo de caixa reduzindo

### 2. Pontos de Atenção
- Margens em queda
- ROE volátil
- Endividamento crescente
- Ciclo de caixa aumentando

## Estrutura de Saída

### JSON com Análise Temporal
```json
{
  "empresa": {...},
  "periodo_dados": {
    "inicio": "2020-03-31",
    "fim": "2024-09-30",
    "total_periodos": 19
  },
  "estatisticas_5anos": {
    "margem_liquida": {
      "media": 15.3,
      "ultimo": 18.2,
      "minimo": 10.1,
      "maximo": 22.5
    }
  },
  "serie_temporal": {
    "2024-09-30": {
      "receita_liquida": 45000000000,
      "margem_liquida": 18.2,
      "roe": 22.5
    }
  }
}
```

### Gráficos Gerados
1. `receita_lucro_evolucao.png` - Barras anuais
2. `margens_evolucao.png` - Linhas com evolução das margens
3. `rentabilidade_evolucao.png` - ROE, ROA, ROIC
4. `divida_ebitda_evolucao.png` - Alavancagem

## Vantagens da Análise Temporal

1. **Identificar Ciclos**: Empresas cíclicas mostram padrões
2. **Avaliar Consistência**: ROE estável indica boa gestão
3. **Detectar Deterioração**: Margens em queda são alerta
4. **Comparar Períodos**: Pré/pós-COVID, mudanças de gestão
5. **Projetar Tendências**: Base para estimativas futuras

## Limitações

- Depende da disponibilidade de dados históricos
- ITR (trimestral) vs DFP (anual) podem ter diferenças
- Mudanças contábeis podem afetar comparabilidade
- Eventos não-recorrentes distorcem médias

## Quando Usar Cada Tipo

### Use Análise Pontual quando:
- Precisa de resposta rápida
- Quer snapshot atual
- Está comparando várias empresas

### Use Análise Temporal quando:
- Avaliando tendências
- Analisando qualidade dos resultados
- Fazendo due diligence aprofundada
- Preparando relatórios de investimento