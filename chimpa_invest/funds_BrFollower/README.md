# Sistema de Análise de Fundos de Investimento 📊

## Visão Geral
Sistema completo para análise temporal de fundos de investimento brasileiros, com processamento de dados CVM e geração de relatórios detalhados.

## 🚀 Instalação Rápida

### 1. Requisitos
```bash
# Python 3.8+ instalado
# Instalar dependências:
pip install pandas numpy matplotlib
```

### 2. Estrutura de Pastas
```
chimpa_invest/funds_BrFollower/
├── analise_temporal_fundos.py    # Script principal
├── analise_capstone_completa.py  # Análise específica Capstone
└── dados/                         # Pasta criada automaticamente
    └── [CNPJ_LIMPO]/             # Ex: 35803288000117/
        ├── dados_fundo.pkl
        ├── dados_fundo.json
        ├── analise_temporal.png
        ├── relatorio_temporal.html
        └── csv/
```

## 📋 Como Usar

### Análise Completa de Qualquer Fundo

```bash
# Formato básico
python analise_temporal_fundos.py [CNPJ]

# Exemplos práticos:
python analise_temporal_fundos.py 35.803.288/0001-17  # Capstone
python analise_temporal_fundos.py 38.351.476/0001-40  # Outro fundo
```

### Opções Avançadas

```bash
# Com nome personalizado
python analise_temporal_fundos.py 35.803.288/0001-17 --nome "Capstone FIC FIM"

# Especificar período mínimo
python analise_temporal_fundos.py 35.803.288/0001-17 --anos 3

# Escolher formato de exportação
python analise_temporal_fundos.py 35.803.288/0001-17 --formato csv
```

## 📊 O que o Sistema Analisa

### 1. **Evolução Patrimonial**
- Patrimônio total ao longo do tempo
- Composição por tipo de ativo
- Tendências de alocação

### 2. **Indicadores de Performance**
- Retorno total e anualizado
- Volatilidade
- Sharpe Ratio
- Maximum Drawdown
- Performance por ano

### 3. **Análise de Carteira**
- Posições em ações detalhadas
- Informações sobre derivativos
- Concentração e diversificação
- Composição média

### 4. **Curva de Retorno**
- Série histórica de cotas (quando disponível)
- Retornos diários e mensais
- Retorno acumulado

## 📁 Dados Gerados

### Formatos de Saída

1. **Pickle (.pkl)**: Dados completos para análise posterior
2. **JSON (.json)**: Formato legível para integração
3. **CSV (pasta csv/)**: Múltiplos arquivos para Excel
   - evolucao_patrimonio.csv
   - posicoes_acoes.csv
   - serie_cotas.csv
   - retornos_mensais.csv
   - indicadores.csv
   - carteiras_resumo.csv

### Visualizações
- **analise_temporal.png**: 10 gráficos com análise completa
- **relatorio_temporal.html**: Relatório interativo

## 🎯 Exemplos de Uso para Apresentação

### 1. Análise Rápida do Capstone
```bash
python analise_temporal_fundos.py 35.803.288/0001-17 --nome "Capstone"
```

### 2. Comparação de Múltiplos Fundos
```bash
# Fundo 1
python analise_temporal_fundos.py 35.803.288/0001-17

# Fundo 2
python analise_temporal_fundos.py 38.351.476/0001-40

# Os dados ficam organizados em pastas separadas
```

### 3. Exportar Apenas CSV para Excel
```bash
python analise_temporal_fundos.py 35.803.288/0001-17 --formato csv
```

## 📈 Interpretando os Resultados

### Indicadores Principais
- **Retorno Total**: Performance desde o início
- **Volatilidade**: Nível de risco (baixo < 10%, moderado < 20%, alto > 20%)
- **Sharpe Ratio**: Relação retorno/risco (excelente > 2, boa > 1)
- **Max Drawdown**: Maior queda do pico

### Alertas Importantes
- ⚠️ Se não encontrar dados de cotas, análise continua sem retornos
- ✓ Período mínimo padrão: 5 anos (configurável)
- 📁 Todos os dados salvos em: `dados/[CNPJ_LIMPO]/`

## 🔧 Solução de Problemas

### Erro de Importação
```bash
# Reinstalar dependências
pip install --upgrade pandas numpy matplotlib
```

### Dados Não Encontrados
- Verificar se o CNPJ está correto
- Confirmar que existe pasta `sherpa/database/CDA`

### Para Demonstração Rápida
Use o Capstone (CNPJ: 35.803.288/0001-17) que tem dados completos

## 📞 Suporte
Em caso de dúvidas durante a apresentação, os principais pontos são:
1. Sistema processa dados oficiais da CVM
2. Análise mínima de 5 anos (configurável)
3. Múltiplos formatos de exportação
4. Visualizações automáticas
5. Relatório HTML interativo