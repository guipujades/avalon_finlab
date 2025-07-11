# Sistema de Análise Financeira - Chimpa Invest

## 📋 Visão Geral

Sistema integrado que combina:
1. **Análise de Valuation Temporal** (dados históricos de 10 anos)
2. **Busca de Dados de Mercado** (via Perplexity AI - interativo)
3. **Análise Inteligente** (via ChatGPT/OpenAI)
4. **Geração de Relatórios** (detalhado + áudio 2 minutos)

## 🚀 Funcionalidades Implementadas

### 1. Sistema de Valuation Temporal
**Arquivo:** `valuation_empresa_temporal.py`

- Coleta dados de 10 anos da CVM
- Calcula métricas financeiras seguindo metodologia Insper
- Gera relatórios TXT e JSON completos
- Inclui gráficos de evolução temporal

**Como usar:**
```bash
python3 valuation_empresa_temporal.py BBAS3
```

### 2. Busca Interativa de Dados de Mercado (Perplexity)
**Arquivo:** `perplexity_client.py` + integração nos scripts de valuation

- Sistema **totalmente interativo** com controle do usuário
- 5 categorias de dados: preço atual, múltiplos setor, análise recente, número de ações, dividend yield
- Para cada pergunta: **[E]nviar / [M]odificar / [P]ular**
- Para cada resposta: **[S]im / [N]ão**
- Se rejeitada: **[F]ornecer resposta manual / [D]esconsiderar análise**

**Fluxo:**
```
❓ Pergunta: Qual o preço atual da ação BBAS3?
🤔 [E]nviar / [M]odificar / [P]ular: E
📝 Resposta: A ação está cotada a R$ 25,40...
✅ Aceitar? [S]im / [N]ão: N
🔧 [F]ornecer resposta / [D]esconsiderar: F
✏️ Digite resposta: R$ 26,15 (fonte: B3 tempo real)
✅ Resposta manual salva!
```

### 3. Agente de Análise Inteligente (ChatGPT)
**Arquivo:** `analysis_agent.py`

**Funcionalidades:**
- Análise **detalhada** (relatório completo)
- Análise **rápida** (áudio 2 minutos)
- Integração valuation + release + dados de mercado
- Suporte a respostas manuais e dados desconsiderados

**Exemplo de uso:**
```python
from analysis_agent import ChimpaAnalysisAgent

agent = ChimpaAnalysisAgent()
result = await agent.analyze_complete_valuation(
    "data/valuation_BBAS3_COMPLETO.txt",
    "documents/parsed/BANCO_DO_BRASIL_release.txt",
    "quick"  # ou "detailed"
)

# Gerar script para áudio
audio_script = agent.generate_audio_summary(result)
```

### 4. Sistema Completo Integrado
**Arquivo:** `run_complete_analysis.py`

Executa todo o pipeline:
1. Verifica dados existentes
2. Executa valuation com dados de mercado (se necessário)
3. Analisa via ChatGPT
4. Gera relatórios finais

**Como usar:**
```bash
python3 run_complete_analysis.py BBAS3
```

## 📁 Arquivos e Estrutura

```
poc/
├── valuation_empresa_temporal.py    # Valuation com análise temporal
├── valuation_empresa.py             # Valuation simples
├── perplexity_client.py             # Cliente Perplexity AI
├── analysis_agent.py                # Agente de análise ChatGPT
├── run_complete_analysis.py         # Sistema integrado
├── buscar_empresa_cvm.py            # Busca inteligente de empresas
├── document_agent.py                # Processamento de PDFs
├── demo_*.py                        # Scripts de demonstração
├── test_*.py                        # Scripts de teste
└── data/                            # Dados gerados
    ├── valuation_temporal_*.json    # Relatórios JSON
    ├── valuation_temporal_*_COMPLETO.txt  # Relatórios TXT
    ├── analysis_report_*.json       # Análises detalhadas
    ├── audio_script_*.txt           # Scripts para áudio
    └── graficos_*/                  # Gráficos gerados
```

## 🔧 Configuração

### 1. Instalar Dependências
```bash
pip3 install pandas numpy matplotlib aiohttp python-dotenv openai --break-system-packages
```

### 2. Configurar API Keys
Arquivo `.env`:
```
OPENAI_API_KEY=sk-proj-xxxxx
PERPLEXITY_API_KEY=pplx-xxxxx
```

### 3. Dados CVM
Os dados estruturados devem estar em `/database/chimpa/` (configurável).

## 📊 Tipos de Análise

### Análise Rápida (Áudio 2min)
- **Modelo:** GPT-3.5-turbo
- **Saída:** ~300 palavras (~70 segundos)
- **Foco:** Top 3 insights + risco + oportunidade + conclusão
- **Formato:** Script otimizado para áudio

### Análise Detalhada (Relatório)
- **Modelo:** GPT-4-turbo-preview
- **Saída:** ~2000 palavras
- **Foco:** Análise completa + tendências + recomendações
- **Formato:** JSON estruturado + insights detalhados

## 🎯 Exemplos de Saída

### Script para Áudio (BBAS3)
```
ANÁLISE FINANCEIRA - BANCO DO BRASIL S.A.

A situação financeira atual mostra receita líquida em crescimento, 
com margens consistentes, porém com leve queda na margem EBIT. 
O lucro líquido apresentou crescimento, refletindo gestão eficiente.

PRINCIPAIS TENDÊNCIAS: Crescimento da receita e lucro líquido 
indicando boa performance operacional...

RISCO PRINCIPAL: Instabilidade econômica do país...

OPORTUNIDADE: Expansão de serviços digitais...

CONCLUSÃO: Investimento pode ser atrativo a longo prazo...
```

### Relatório Detalhado (JSON)
```json
{
  "status": "success",
  "empresa": "BANCO DO BRASIL S.A.",
  "valuation_analysis": {
    "analysis": "Análise detalhada das métricas...",
    "metrics_analyzed": ["receita", "margens", "rentabilidade"]
  },
  "release_analysis": {
    "analysis": "Análise do release trimestral...",
    "content_type": "txt"
  },
  "integrated_analysis": {
    "integrated_analysis": "Síntese dos dados quantitativos e qualitativos..."
  },
  "metadata": {
    "processing_time": 15.3,
    "model_used": "gpt-4-turbo-preview"
  }
}
```

## 🎮 Como Usar o Sistema Completo

### Cenário 1: Análise Nova
```bash
# 1. Executar valuation com dados de mercado
python3 valuation_empresa_temporal.py BBAS3
# → Sistema interativo do Perplexity

# 2. Análise via ChatGPT
python3 run_complete_analysis.py BBAS3
```

### Cenário 2: Análise Rápida (dados existentes)
```bash
python3 test_analysis_optimized.py
```

### Cenário 3: Apenas buscar dados de mercado
```bash
python3 valuation_empresa.py BBAS3 --mercado
```

## 🔍 Sistema de Controle de Qualidade

### Dados do Perplexity
- **Aprovação manual** de cada resposta
- **Edição de perguntas** antes do envio
- **Respostas manuais** quando IA falha
- **Desconsideração** de análises sem dados
- **Alertas automáticos** sobre impactos

### Análise ChatGPT
- **Modelos otimizados** por tipo de análise
- **Prompts especializados** para mercado brasileiro
- **Fallback** via requests se biblioteca OpenAI falhar
- **Controle de tokens** para evitar custos excessivos

## 📈 Métricas Suportadas

### Valuation
- Receita, Lucro, EBIT, EBITDA
- Margens (Bruta, Líquida, EBIT, EBITDA)
- Rentabilidade (ROE, ROA, ROI, ROIC)
- Endividamento (Dívida/PL, Dívida/EBITDA)
- Liquidez (Corrente, Seca)
- Prazos (PMR, PME, PMP, Ciclo Operacional)

### Mercado
- Preço atual da ação
- Número de ações em circulação
- Dividend yield e histórico
- Múltiplos do setor
- Análises e perspectivas recentes

## 🚀 Próximos Passos

1. **Integração com TTS** para geração automática de áudio
2. **Dashboard web** para visualização
3. **Análise comparativa** entre empresas
4. **Alertas automáticos** para mudanças significativas
5. **Integração com APIs** de cotações em tempo real

## 💡 Características Únicas

### Sistema Interativo Inovador
- **Controle total** do usuário sobre dados utilizados
- **Transparência** na origem de cada informação
- **Qualidade assegurada** por validação manual
- **Adaptação inteligente** quando dados são desconsiderados

### Análise Multicamada
- **Quantitativa:** Métricas financeiras históricas
- **Qualitativa:** Releases e comunicações
- **Mercado:** Dados atuais e perspectivas
- **Integrada:** Síntese inteligente de todas as fontes

### Otimização para Uso Real
- **Áudio de 2 minutos:** Perfeito para consumo rápido
- **Relatórios detalhados:** Para análise aprofundada
- **Sistema de cache:** Evita reprocessamento
- **Tratamento de erros:** Robusto e resiliente

---

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique os arquivos de teste (`test_*.py`)
2. Execute as demonstrações (`demo_*.py`)
3. Consulte os logs de erro nos outputs
4. Verifique configuração das API keys no `.env`

**Sistema testado e funcionando para BBAS3 (Banco do Brasil)** ✅