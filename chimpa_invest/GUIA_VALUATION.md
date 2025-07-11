# 📊 Guia do Sistema de Valuation

## 🎯 Visão Geral
Sistema genérico de valuation que funciona para **qualquer empresa** listada na CVM.

## 🚀 Como Usar

### 1. Valuation Básico
```bash
# Por ticker
python valuation_empresa.py VALE3

# Por nome
python valuation_empresa.py "VALE S.A."

# Por código CVM
python valuation_empresa.py 4170
```

### 2. Valuation com Preço da Ação
```bash
# Com preço atual
python valuation_empresa.py PETR4 --preco 38.50

# Com preço e número de ações
python valuation_empresa.py VALE3 --preco 70.00 --acoes 4850
```

### 3. Demonstração Interativa
```bash
python demo_valuation.py
```

## 📈 Métricas Calculadas

### Indicadores Financeiros
- **Receita Líquida**: Faturamento total
- **Lucro Líquido**: Resultado final
- **EBIT**: Lucro operacional
- **Patrimônio Líquido**: Valor contábil
- **Dívida Líquida**: Dívida total - caixa

### Margens
- **Margem Líquida**: Lucro/Receita
- **Margem EBIT**: EBIT/Receita

### Rentabilidade
- **ROE**: Retorno sobre patrimônio
- **ROA**: Retorno sobre ativos

### Alavancagem
- **Dívida/PL**: Endividamento
- **Dívida/EBIT**: Capacidade de pagamento

### Múltiplos (quando preço fornecido)
- **P/L**: Preço/Lucro
- **EV/EBIT**: Valor da empresa/EBIT
- **P/VPA**: Preço/Valor patrimonial

## 📁 Dados Necessários

O sistema busca automaticamente em:
```
documents/cvm_estruturados/
├── ITR/  # Informações trimestrais
├── DFP/  # Demonstrações anuais
├── FRE/  # Formulário de referência
└── FCA/  # Cadastro
```

## 💡 Exemplos Práticos

### Análise Rápida da VALE
```bash
python valuation_empresa.py VALE3 --preco 70.00
```

### Análise Detalhada da Petrobras
```bash
python valuation_empresa.py PETR4 --preco 38.50 --acoes 13000 --output petrobras_2025.json
```

### Buscar Empresa por Nome
```bash
python valuation_empresa.py "BANCO DO BRASIL"
```

## 📊 Saída do Sistema

### 1. Relatório no Terminal
- Métricas financeiras principais
- Margens e rentabilidade
- Múltiplos de mercado

### 2. Arquivo JSON
```json
{
  "empresa": {
    "nome": "VALE S.A.",
    "ticker": "VALE3",
    "codigo_cvm": 4170
  },
  "metricas_financeiras": {
    "receita_liquida": 158000000000,
    "margem_liquida": 25.3,
    "roe": 22.5
  },
  "multiplos": {
    "P/L": 5.2,
    "EV/EBIT": 4.8
  }
}
```

## ⚡ Dicas para Apresentação

1. **Use empresas conhecidas**: VALE3, PETR4, ITUB4
2. **Demonstre com preço**: Mostra cálculo de múltiplos
3. **Compare empresas**: Rode para 2-3 empresas
4. **Mostre o JSON**: Abre o arquivo gerado

## 🔍 Empresas Disponíveis

O sistema tem dados de **todas as empresas** listadas na B3.
Principais exemplos:
- VALE3 - Vale
- PETR4 - Petrobras
- ITUB4 - Itaú
- ABEV3 - Ambev
- BBDC4 - Bradesco
- B3SA3 - B3
- WEGE3 - WEG
- RENT3 - Localiza

## ❓ Troubleshooting

### "Empresa não encontrada"
- Verificar se ticker está correto
- Tentar buscar por código CVM
- Verificar arquivo `dados/empresas_cvm_completa.json`

### "Dados insuficientes"
- Empresa pode não ter dados recentes
- Verificar pasta `documents/cvm_estruturados/`

### Múltiplos não calculados
- Fornecer o preço da ação com `--preco`