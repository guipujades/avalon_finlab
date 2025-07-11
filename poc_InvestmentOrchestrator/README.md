# Sistema Multi-Agente de Investimentos

Sistema simplificado de pesquisa e análise financeira com 3 agentes especializados e APIs econômicas integradas.

## Visão Geral

Sistema focado para consultas financeiras e de investimentos, combinando base de conhecimento local com pesquisa web e dados econômicos em tempo real.

### Funcionalidades Principais

- **Pesquisa Híbrida**: Combina documentos locais + busca web
- **APIs Financeiras**: Dados econômicos do BACEN em tempo real
- **Processamento Inteligente**: Análise automatizada de documentos
- **Interface Simples**: Menu direto com opções claras

### Arquitetura Simplificada

```
User Query
    ↓
Research Agent (coordenador)
    ↓
Document Agent (base local) + Web Search
    ↓
Response
```

## Agentes

1. **Research Agent** - Coordenador principal, decide estratégia
2. **Document Agent** - Gerencia base de conhecimento local
3. **Maestro Agent** - Controle de qualidade e orientações

## Instalação

### 1. Dependências
```bash
pip install -r requirements.txt
```

### 2. Configuração de API Keys
Crie arquivo `.env`:
```env
OPENAI_API_KEY=sua_chave_openai
TAVILY_KEY=sua_chave_tavily
LLAMA_CLOUD_API_KEY=sua_chave_llama_parse
```

### 3. Execução
```bash
python orchestrator.py
```

## Como Usar

### Menu Principal

```
1. PERGUNTA SIMPLES - Consultas rápidas
2. PESQUISA COMPLEXA - Análise detalhada
3. CONSULTA DOCUMENTOS - Apenas base local
4. PESQUISA WEB - Apenas internet
5. GERENCIAR SISTEMA - Comandos admin
6. CONFIGURAR MAESTRO - Ajustes de qualidade
7. TOGGLE MAESTRO - Liga/desliga controle
0. PERGUNTA LIVRE - Sistema decide automaticamente
```

### Estratégias de Resposta

O Research Agent decide automaticamente:

- **Documents Only** - Alta confiança nos documentos locais (>70%)
- **Documents + Web** - Confiança média, complementa com web (30-70%)
- **Web Only** - Baixa confiança nos documentos (<30%)

## APIs Financeiras

### BACEN API (Ativa)

Indicadores disponíveis:
- Taxa Selic, CDI, TJLP
- IPCA, IGP-M, INPC
- Dólar, Euro, Libra
- PIB, Taxa de Desemprego
- Resultado Primário, Dívida Líquida

### Uso da API

```python
from financial_apis import BacenAPIClient, FinancialAPIManager

# Cliente direto
client = BacenAPIClient()
selic = client.get_indicator('selic')
print(f"Selic: {selic['last_value']}%")

# Gerenciador unificado
manager = FinancialAPIManager()
summary = manager.get_economic_summary()
```

## Testes

- `test_simplified_research_flow.py` - Testa fluxo do Research Agent
- `financial_apis.py` - Testa APIs BACEN (executar diretamente)

## Arquivos Principais

```
orchestrator.py         # Coordenador principal
research_agent.py       # Agente de pesquisa
document_agent.py       # Gerenciador de documentos
maestro_agent.py        # Controle de qualidade
financial_apis.py       # APIs econômicas
config.py              # Configurações
```

## Uso Programático

```python
import asyncio
from orchestrator import IntelligentOrchestrator

async def main():
    orchestrator = IntelligentOrchestrator(openai_key, tavily_key)
    await orchestrator.initialize()
    
    response = await orchestrator.process_user_input(
        "Qual a taxa Selic atual?"
    )
    print(response)

asyncio.run(main())
```

## Status do Sistema

- Sistema simplificado e funcional
- API BACEN integrada e testada
- Research Agent com estratégias automáticas
- Remoção completa de Data Science Agent
- Interface limpa sem emojis

## Próximos Passos

1. Usar financial_apis.py para gerar documentos econômicos
2. Integrar dados BACEN no Document Agent
3. Expandir base de conhecimento financeiro
4. Futuro: Reativar BTG API quando disponível 