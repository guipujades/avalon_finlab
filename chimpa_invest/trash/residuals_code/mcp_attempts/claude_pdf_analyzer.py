#!/usr/bin/env python3
"""
Claude PDF Analyzer
===================
Usa a capacidade nativa do Claude de ler PDFs via MCP.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json
from datetime import datetime


class ClaudePDFAnalyzer:
    """
    Analisador de PDFs usando Claude diretamente via MCP.
    
    O Claude tem capacidade nativa de ler e analisar PDFs
    sem necessidade de bibliotecas externas.
    """
    
    def __init__(self):
        self.analysis_cache = {}
        
    def analyze_financial_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Solicita ao Claude para analisar um PDF financeiro.
        
        IMPORTANTE: Esta função prepara o prompt para o Claude
        analisar o PDF. O PDF deve ser fornecido ao Claude
        através da interface ou API.
        """
        
        json_template = '''{
    "empresa": {
        "nome": "",
        "ticker": "",
        "setor": ""
    },
    "periodo": {
        "trimestre": "",
        "ano": "",
        "data_release": ""
    },
    "metricas_financeiras": {
        "receita": {
            "valor": 0,
            "unidade": "milhões",
            "variacao_yoy": 0,
            "variacao_qoq": 0
        },
        "ebitda": {
            "valor": 0,
            "margem": 0,
            "variacao_yoy": 0
        },
        "lucro_liquido": {
            "valor": 0,
            "margem": 0,
            "variacao_yoy": 0
        },
        "divida_liquida": {
            "valor": 0,
            "divida_ebitda": 0
        },
        "fcf": {
            "valor": 0,
            "conversao_ebitda": 0
        }
    },
    "destaques": [],
    "riscos": [],
    "guidance": {},
    "recomendacao_implicita": "",
    "score_qualidade": 0
}'''
        
        prompt = f"""Por favor, analise o PDF financeiro localizado em: {pdf_path}
        
Extraia e organize as seguintes informações:

1. **IDENTIFICAÇÃO**
   - Empresa
   - Período (trimestre/ano)
   - Data do relatório

2. **MÉTRICAS FINANCEIRAS PRINCIPAIS**
   - Receita líquida (valor e variação %)
   - EBITDA (valor, margem e variação %)
   - Lucro líquido (valor e variação %)
   - Dívida líquida (valor e múltiplo Dívida/EBITDA)
   - Geração de caixa operacional
   - CAPEX

3. **INDICADORES OPERACIONAIS**
   - Volumes vendidos/produzidos
   - Preços médios realizados
   - Market share se mencionado
   - Eficiência operacional

4. **ANÁLISE QUALITATIVA**
   - Principais destaques positivos (bullets)
   - Principais desafios/riscos (bullets)
   - Guidance/projeções se houver
   - Mudanças estratégicas importantes

5. **COMPARAÇÃO COM PERÍODOS ANTERIORES**
   - Variações trimestrais (QoQ)
   - Variações anuais (YoY)
   - Tendências identificadas

6. **CONTEXTO SETORIAL**
   - Comentários sobre o mercado
   - Posição competitiva
   - Fatores macroeconômicos relevantes

Por favor, formate a resposta em JSON estruturado seguindo este modelo:

{json_template}
"""
        
        return {
            "prompt": prompt,
            "pdf_path": str(pdf_path),
            "timestamp": datetime.now().isoformat(),
            "instructions": "Forneça este prompt ao Claude junto com o PDF para análise completa"
        }
    
    def analyze_multiple_pdfs(self, pdf_list: List[Path]) -> Dict[str, Any]:
        """
        Prepara análise comparativa de múltiplos PDFs.
        """
        
        files_list = '\n'.join([f"- {pdf}" for pdf in pdf_list])
        
        prompt = f"""Por favor, analise comparativamente os seguintes PDFs financeiros:

{files_list}

Realize uma análise comparativa focando em:

1. **COMPARAÇÃO DE DESEMPENHO**
   - Crescimento de receita
   - Evolução de margens
   - Eficiência operacional
   - Geração de caixa

2. **POSICIONAMENTO COMPETITIVO**
   - Market share relativo
   - Vantagens competitivas
   - Exposição a riscos

3. **VALUATION RELATIVO**
   - Múltiplos implícitos
   - Qualidade dos resultados
   - Sustentabilidade do crescimento

4. **RANKING E RECOMENDAÇÕES**
   - Classificação por atratividade
   - Principais oportunidades
   - Riscos relativos

Formate como relatório executivo com tabela comparativa.
"""
        
        return {
            "prompt": prompt,
            "pdf_count": len(pdf_list),
            "files": [str(pdf) for pdf in pdf_list],
            "analysis_type": "comparative"
        }
    
    def generate_investment_thesis(self, pdf_path: Path, market_context: Dict[str, Any]) -> str:
        """
        Gera prompt para tese de investimento baseada no PDF.
        """
        
        context_str = json.dumps(market_context, indent=2, ensure_ascii=False)
        
        prompt = f"""Baseado na análise do relatório financeiro em {pdf_path} e considerando
o seguinte contexto de mercado:

{context_str}

Por favor, desenvolva uma TESE DE INVESTIMENTO completa incluindo:

1. **SUMÁRIO EXECUTIVO** (3-4 linhas)
   - Recomendação clara (COMPRA/MANUTENÇÃO/VENDA)
   - Principal driver da tese
   - Potencial de valorização

2. **PONTOS FORTES** (bullets)
   - Vantagens competitivas sustentáveis
   - Catalisadores de curto/médio prazo
   - Qualidade da gestão e execução

3. **RISCOS E MITIGANTES**
   - Principais riscos mapeados
   - Probabilidade e impacto
   - Fatores mitigantes

4. **VALUATION**
   - Múltiplos atuais vs históricos
   - Comparação com pares
   - Preço-alvo e metodologia

5. **TRIGGERS E MONITORAMENTO**
   - Eventos a monitorar
   - Métricas-chave de acompanhamento
   - Pontos de reavaliação da tese

Seja objetivo e baseie-se apenas em fatos do relatório.
"""
        
        return prompt
    
    def analyze_earnings_surprises(self, pdf_path: Path, expectations: Dict[str, Any]) -> str:
        """
        Analisa surpresas vs expectativas do mercado.
        """
        
        expectations_str = json.dumps(expectations, indent=2, ensure_ascii=False)
        
        prompt = f"""Analise o relatório em {pdf_path} comparando com as seguintes
expectativas de mercado:

{expectations_str}

Identifique:

1. **SURPRESAS POSITIVAS**
   - Métricas que superaram expectativas
   - Magnitude da surpresa (%)
   - Sustentabilidade

2. **SURPRESAS NEGATIVAS**
   - Métricas abaixo do esperado
   - Fatores pontuais vs estruturais
   - Impacto no guidance

3. **REAÇÃO ESPERADA DO MERCADO**
   - Impacto provável no preço
   - Revisões de estimativas
   - Mudança de percepção

4. **QUALITY OF EARNINGS**
   - Itens não-recorrentes
   - Qualidade do lucro reportado
   - Sustentabilidade das margens

Formate como nota rápida para traders.
"""
        
        return prompt


class SmartPDFChat:
    """
    Interface inteligente para chat sobre PDFs financeiros.
    """
    
    def __init__(self):
        self.analyzer = ClaudePDFAnalyzer()
        self.context = {}
        
    def prepare_analysis_session(self, pdf_path: Path) -> List[str]:
        """
        Prepara uma sessão de análise interativa.
        """
        
        questions = [
            "📊 Quais foram os principais destaques financeiros deste trimestre?",
            "📈 Como está a evolução das margens em relação aos trimestres anteriores?",
            "💰 Qual a situação de caixa e endividamento da empresa?",
            "🎯 A empresa manteve ou alterou seu guidance?",
            "⚠️ Quais os principais riscos mencionados pela administração?",
            "🏭 Como estão os indicadores operacionais (volumes, preços, etc)?",
            "🌍 Que fatores macroeconômicos estão impactando os resultados?",
            "💡 Há alguma mudança estratégica importante sendo implementada?",
            "📊 Como os resultados se comparam com os principais concorrentes?",
            "🔮 Qual sua avaliação sobre as perspectivas futuras da empresa?"
        ]
        
        initial_prompt = f"""Vou fazer algumas perguntas sobre o relatório financeiro em {pdf_path}.
Por favor, mantenha as respostas objetivas e baseadas apenas nas
informações contidas no documento.

Primeira pergunta: {questions[0]}
"""
        
        return {
            "initial_prompt": initial_prompt,
            "suggested_questions": questions,
            "pdf_path": str(pdf_path),
            "session_type": "interactive_analysis"
        }
    
    def generate_executive_summary(self, pdf_path: Path) -> str:
        """
        Gera prompt para sumário executivo.
        """
        
        prompt = f"""Por favor, crie um SUMÁRIO EXECUTIVO do relatório em {pdf_path}
seguindo este formato:

**[EMPRESA] - [PERÍODO]**

**RESULTADO:** [ACIMA/EM LINHA/ABAIXO] das expectativas

**NÚMEROS-CHAVE:**
• Receita: R$ XX bi ([+/-]X% a/a)
• EBITDA: R$ XX bi (margem X%), [+/-]X% a/a
• Lucro: R$ XX bi ([+/-]X% a/a)

**DESTAQUES:**
• [Principal destaque positivo]
• [Segundo destaque]
• [Terceiro destaque]

**PONTOS DE ATENÇÃO:**
• [Principal preocupação]
• [Risco ou desafio]

**OUTLOOK:** [Resumo do guidance e perspectivas]

**NOSSA VISÃO:** [Análise crítica em 2-3 linhas]

Mantenha o sumário em no máximo 1 página.
"""
        
        return prompt


# Funções auxiliares para uso direto
def analyze_pdf_with_claude(pdf_path: Path, analysis_type: str = "complete") -> Dict[str, Any]:
    """
    Função simplificada para análise de PDF com Claude.
    
    Args:
        pdf_path: Caminho do PDF
        analysis_type: Tipo de análise ("complete", "summary", "thesis")
    
    Returns:
        Dicionário com prompts e instruções
    """
    analyzer = ClaudePDFAnalyzer()
    
    if analysis_type == "complete":
        return analyzer.analyze_financial_pdf(pdf_path)
    elif analysis_type == "summary":
        chat = SmartPDFChat()
        return {"prompt": chat.generate_executive_summary(pdf_path)}
    elif analysis_type == "thesis":
        market_context = {
            "selic": 10.50,
            "inflacao": 4.5,
            "dolar": 5.00,
            "ibovespa_pe": 12.5
        }
        return {"prompt": analyzer.generate_investment_thesis(pdf_path, market_context)}
    else:
        return {"error": "Tipo de análise não reconhecido"}


if __name__ == "__main__":
    # Exemplo de uso
    pdf_path = Path("documents/pending/VALE_3T24.pdf")
    
    print("🤖 INSTRUÇÕES PARA ANÁLISE COM CLAUDE")
    print("=" * 60)
    
    # Análise completa
    result = analyze_pdf_with_claude(pdf_path, "complete")
    print("\n📊 ANÁLISE COMPLETA:")
    print(result["prompt"][:500] + "...")
    
    # Sumário executivo
    result = analyze_pdf_with_claude(pdf_path, "summary")
    print("\n📝 SUMÁRIO EXECUTIVO:")
    print(result["prompt"])
    
    print("\n✅ Para usar:")
    print("1. Copie o prompt acima")
    print("2. Forneça o PDF ao Claude")
    print("3. Claude analisará diretamente o conteúdo")