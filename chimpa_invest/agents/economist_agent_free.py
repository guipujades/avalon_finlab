#!/usr/bin/env python3
"""
Agente Economista Livre
=======================
Analisa releases com inteligência econômica, sem buscar métricas pré-definidas.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import re


class EconomistAgentFree:
    """
    Agente economista com análise livre baseada em conhecimento financeiro.
    """
    
    def __init__(self):
        self.parsed_dir = Path("documents/parsed")
        self.summaries_dir = Path("summaries")
        self.summaries_dir.mkdir(exist_ok=True)
        
        # Base de conhecimento econômico-financeiro
        self.economic_knowledge = self._build_economic_knowledge()
        
    def _build_economic_knowledge(self) -> Dict[str, Any]:
        """
        Constrói base de conhecimento econômico-financeiro brasileiro.
        """
        return {
            "contexto_macro": {
                "selic_atual": 10.50,
                "meta_inflacao": 3.0,
                "inflacao_esperada": 4.0,
                "cambio_referencia": 5.00,
                "crescimento_pib_esperado": 2.0
            },
            "conceitos_importantes": {
                "margem_operacional": "Indica eficiência operacional - quanto maior, melhor",
                "alavancagem": "Uso de dívida - pode amplificar retornos mas aumenta risco",
                "geração_caixa": "Capacidade de converter lucro em dinheiro - fundamental",
                "capital_giro": "Recursos para operação diária - liquidez",
                "retorno_capital": "Eficiência no uso do capital investido"
            },
            "setores_economia": {
                "mineração": {
                    "drivers": ["preço commodities", "demanda China", "câmbio"],
                    "riscos": ["volatilidade preços", "regulação ambiental", "geopolítica"],
                    "métricas_chave": ["custo por tonelada", "volume produção", "preço realizado"]
                },
                "energia": {
                    "drivers": ["demanda industrial", "hidrologia", "regulação"],
                    "riscos": ["mudanças regulatórias", "clima", "transição energética"]
                },
                "varejo": {
                    "drivers": ["consumo famílias", "emprego", "crédito"],
                    "riscos": ["inadimplência", "competição", "e-commerce"]
                },
                "bancos": {
                    "drivers": ["spread bancário", "inadimplência", "volume crédito"],
                    "riscos": ["provisões", "regulação", "fintechs"]
                }
            },
            "sinais_positivos": [
                "crescimento receita acima inflação",
                "melhora margens",
                "redução custos",
                "ganho market share",
                "geração caixa robusta",
                "redução alavancagem",
                "investimentos em eficiência",
                "diversificação receitas"
            ],
            "sinais_preocupantes": [
                "queda margens",
                "aumento endividamento",
                "perda market share",
                "queima caixa",
                "aumento custos acima receita",
                "concentração riscos",
                "dependência poucos clientes",
                "problemas regulatórios"
            ]
        }
    
    def analyze_document_freely(self, doc_path: Path) -> Dict[str, Any]:
        """
        Analisa documento de forma livre, usando conhecimento econômico.
        """
        with open(doc_path, 'r', encoding='utf-8') as f:
            doc = json.load(f)
        
        # Compreender o contexto
        company_context = self._understand_company_context(doc, doc_path.name)
        
        # Análise econômica livre
        economic_analysis = self._perform_economic_analysis(doc, company_context)
        
        # Identificar pontos relevantes
        key_insights = self._extract_key_insights(doc, company_context, economic_analysis)
        
        # Formar opinião
        investment_view = self._form_investment_view(economic_analysis, key_insights)
        
        return {
            "company_context": company_context,
            "economic_analysis": economic_analysis,
            "key_insights": key_insights,
            "investment_view": investment_view,
            "document": doc_path.name,
            "analyzed_at": datetime.now().isoformat()
        }
    
    def _understand_company_context(self, doc: Dict, filename: str) -> Dict[str, Any]:
        """
        Entende o contexto da empresa analisada.
        """
        # Identificar empresa e setor
        company_name = self._identify_company(doc, filename)
        sector = self._identify_sector(company_name, doc)
        period = self._identify_period(doc)
        
        return {
            "company": company_name,
            "sector": sector,
            "period": period,
            "sector_dynamics": self.economic_knowledge["setores_economia"].get(sector, {})
        }
    
    def _perform_economic_analysis(self, doc: Dict, context: Dict) -> Dict[str, Any]:
        """
        Realiza análise econômica livre do documento.
        """
        content_str = json.dumps(doc, ensure_ascii=False).lower()
        
        analysis = {
            "tendencia_geral": self._analyze_general_trend(content_str),
            "saude_financeira": self._analyze_financial_health(content_str),
            "posicionamento_mercado": self._analyze_market_position(content_str),
            "eficiencia_operacional": self._analyze_operational_efficiency(content_str),
            "perspectivas": self._analyze_outlook(content_str)
        }
        
        # Considerar contexto setorial
        sector_dynamics = context.get("sector_dynamics", {})
        if sector_dynamics:
            analysis["fatores_setoriais"] = self._analyze_sector_factors(content_str, sector_dynamics)
        
        return analysis
    
    def _extract_key_insights(self, doc: Dict, context: Dict, analysis: Dict) -> List[str]:
        """
        Extrai insights-chave baseados na análise econômica.
        """
        insights = []
        content_str = json.dumps(doc, ensure_ascii=False)
        
        # Insights sobre performance
        if "crescimento" in analysis["tendencia_geral"]:
            insights.append(f"Empresa demonstra trajetória de crescimento no período")
        elif "pressão" in analysis["tendencia_geral"]:
            insights.append(f"Resultados sob pressão indicam desafios operacionais")
        
        # Insights sobre eficiência
        if "eficiente" in analysis["eficiencia_operacional"]:
            insights.append(f"Gestão eficiente de custos sustenta competitividade")
        
        # Insights sobre mercado
        if analysis.get("posicionamento_mercado"):
            insights.append(f"Posição de mercado {analysis['posicionamento_mercado']}")
        
        # Buscar números relevantes (sem padrão fixo)
        numbers = re.findall(r'([\d.,]+)\s*(?:bilhões|milhões|%)', content_str)
        if numbers and len(numbers) > 0:
            insights.append(f"Números relevantes identificados sugerem escala significativa de operações")
        
        # Insights setoriais
        if context["sector"] == "mineração":
            if "china" in content_str or "demanda" in content_str:
                insights.append("Dinâmica de demanda global permanece fator crítico")
            if "custo" in content_str and "tonelada" in content_str:
                insights.append("Controle de custos por tonelada essencial para competitividade")
        
        return insights[:5]  # Máximo 5 insights principais
    
    def _form_investment_view(self, analysis: Dict, insights: List[str]) -> Dict[str, Any]:
        """
        Forma visão de investimento baseada na análise.
        """
        # Contar sinais positivos vs negativos
        positive_signals = 0
        negative_signals = 0
        
        analysis_text = json.dumps(analysis, ensure_ascii=False).lower()
        
        for signal in self.economic_knowledge["sinais_positivos"]:
            if signal.lower() in analysis_text:
                positive_signals += 1
        
        for signal in self.economic_knowledge["sinais_preocupantes"]:
            if signal.lower() in analysis_text:
                negative_signals += 1
        
        # Formar visão
        if positive_signals > negative_signals * 1.5:
            stance = "POSITIVA"
            rationale = "Fundamentos sólidos superam desafios conjunturais"
        elif negative_signals > positive_signals * 1.5:
            stance = "CAUTELOSA"
            rationale = "Riscos identificados recomendam postura conservadora"
        else:
            stance = "NEUTRA"
            rationale = "Balanço equilibrado entre oportunidades e riscos"
        
        return {
            "stance": stance,
            "rationale": rationale,
            "confidence": "Moderada",  # Sempre moderada pois é análise inicial
            "key_factors": insights[:3],
            "monitoring_points": self._identify_monitoring_points(analysis)
        }
    
    def generate_executive_summary_free(self, analysis: Dict) -> str:
        """
        Gera resumo executivo livre, focado em análise econômica.
        """
        context = analysis["company_context"]
        economic = analysis["economic_analysis"]
        insights = analysis["key_insights"]
        view = analysis["investment_view"]
        
        # Construir resumo narrativo
        summary_parts = []
        
        # Cabeçalho
        summary_parts.append(f"# 💼 {context['company']} - Análise {context.get('period', 'Período')}")
        summary_parts.append(f"*Setor: {context['sector'].title()}*\n")
        
        # Visão geral (1 parágrafo)
        summary_parts.append("## 📊 Visão Geral")
        summary_parts.append(
            f"A análise dos resultados apresentados revela uma empresa em momento "
            f"{economic['tendencia_geral']}. {insights[0] if insights else 'Período de transição operacional'}. "
            f"A perspectiva {view['stance']} se justifica por {view['rationale'].lower()}."
        )
        
        # Pontos de Atenção (bullets)
        summary_parts.append("\n## 🔍 Pontos-Chave da Análise")
        for insight in insights[:3]:
            summary_parts.append(f"• {insight}")
        
        # Contexto Setorial
        if context.get("sector_dynamics"):
            summary_parts.append("\n## 🏭 Dinâmica Setorial")
            dynamics = context["sector_dynamics"]
            if dynamics.get("drivers"):
                summary_parts.append(f"Principais drivers do setor: {', '.join(dynamics['drivers'][:3])}")
        
        # Avaliação
        summary_parts.append("\n## 💡 Avaliação")
        summary_parts.append(
            f"**Visão:** {view['stance']} | "
            f"**Confiança:** {view['confidence']}\n"
        )
        
        # Monitoramento
        if view.get("monitoring_points"):
            summary_parts.append("**Monitorar:** " + ", ".join(view["monitoring_points"][:3]))
        
        # Conclusão
        summary_parts.append(
            f"\n*Análise baseada em fundamentos econômico-financeiros e "
            f"dinâmica setorial. Recomenda-se acompanhamento contínuo.*"
        )
        
        return "\n".join(summary_parts)
    
    # Funções auxiliares de análise
    def _analyze_general_trend(self, content: str) -> str:
        """Analisa tendência geral dos resultados."""
        positive_words = ["crescimento", "aumento", "melhora", "expansão", "recorde", "alta"]
        negative_words = ["queda", "redução", "pressão", "desafio", "diminui", "menor"]
        
        positive_count = sum(1 for word in positive_words if word in content)
        negative_count = sum(1 for word in negative_words if word in content)
        
        if positive_count > negative_count * 1.5:
            return "crescimento consistente"
        elif negative_count > positive_count * 1.5:
            return "pressão nos resultados"
        else:
            return "estabilidade com desafios pontuais"
    
    def _analyze_financial_health(self, content: str) -> str:
        """Avalia saúde financeira geral."""
        if "geração" in content and "caixa" in content:
            if "positiv" in content or "robust" in content:
                return "sólida geração de caixa"
            else:
                return "geração de caixa sob observação"
        
        if "dívida" in content or "endividamento" in content:
            if "redução" in content or "menor" in content:
                return "melhora no perfil de endividamento"
            else:
                return "alavancagem requer monitoramento"
        
        return "situação financeira estável"
    
    def _analyze_market_position(self, content: str) -> str:
        """Analisa posicionamento de mercado."""
        if "líder" in content or "market share" in content:
            return "sólida com potencial liderança"
        elif "competitiv" in content:
            return "competitiva em ambiente desafiador"
        else:
            return "em linha com pares do setor"
    
    def _analyze_operational_efficiency(self, content: str) -> str:
        """Avalia eficiência operacional."""
        if "custo" in content:
            if "redução" in content or "menor" in content or "queda" in content:
                return "eficiente com redução de custos"
            elif "aumento" in content or "pressão" in content:
                return "pressionada por aumento de custos"
        
        if "margem" in content or "margin" in content:
            return "foco em preservação de margens"
        
        return "em processo de otimização"
    
    def _analyze_outlook(self, content: str) -> str:
        """Analisa perspectivas futuras."""
        if "guidance" in content or "projeç" in content or "perspectiv" in content:
            return "com visibilidade para períodos futuros"
        elif "incertez" in content or "volatil" in content:
            return "cautelosa dado ambiente volátil"
        else:
            return "estável com oportunidades pontuais"
    
    def _analyze_sector_factors(self, content: str, dynamics: Dict) -> List[str]:
        """Analisa fatores setoriais específicos."""
        factors = []
        
        for driver in dynamics.get("drivers", []):
            if driver.lower() in content:
                factors.append(f"{driver} como fator relevante")
        
        for risk in dynamics.get("riscos", [])[:2]:
            if any(word in content for word in risk.lower().split()):
                factors.append(f"Atenção a {risk}")
        
        return factors[:3]
    
    def _identify_monitoring_points(self, analysis: Dict) -> List[str]:
        """Identifica pontos para monitoramento futuro."""
        points = []
        
        analysis_text = json.dumps(analysis, ensure_ascii=False).lower()
        
        if "custo" in analysis_text:
            points.append("evolução dos custos")
        if "demanda" in analysis_text:
            points.append("dinâmica de demanda")
        if "margem" in analysis_text or "margin" in analysis_text:
            points.append("comportamento das margens")
        if "caixa" in analysis_text:
            points.append("geração de caixa")
        if "dívida" in analysis_text:
            points.append("perfil de endividamento")
        
        return points[:3]
    
    def _identify_company(self, doc: Dict, filename: str) -> str:
        """Identifica a empresa do documento."""
        # Do filename
        if filename:
            parts = filename.upper().split('_')
            if parts:
                return parts[0]
        
        # Do metadata
        if isinstance(doc, dict):
            metadata = doc.get('metadata', {})
            if metadata.get('company'):
                return metadata['company']
        
        return "EMPRESA"
    
    def _identify_sector(self, company: str, doc: Dict) -> str:
        """Identifica o setor da empresa."""
        company_upper = company.upper()
        
        # Mapeamento conhecido
        sector_map = {
            "VALE": "mineração",
            "PETROBRAS": "energia",
            "PETRO": "energia",
            "ITAU": "bancos",
            "BRADESCO": "bancos",
            "AMBEV": "consumo",
            "MAGALU": "varejo",
            "MAGAZINELUIZA": "varejo"
        }
        
        for key, sector in sector_map.items():
            if key in company_upper:
                return sector
        
        # Tentar identificar pelo conteúdo
        content = str(doc).lower()
        if "minério" in content or "mineração" in content:
            return "mineração"
        elif "petróleo" in content or "óleo" in content or "gás" in content:
            return "energia"
        elif "banco" in content or "crédito" in content:
            return "bancos"
        elif "varejo" in content or "loja" in content:
            return "varejo"
        
        return "industrial"
    
    def _identify_period(self, doc: Dict) -> str:
        """Identifica o período do relatório."""
        if isinstance(doc, dict):
            metadata = doc.get('metadata', {})
            if metadata.get('period'):
                return metadata['period']
        
        content = str(doc)
        # Buscar padrões de período
        period_match = re.search(r'([1-4]T\d{2})', content)
        if period_match:
            return period_match.group(1)
        
        return "Período"
    
    def process_latest_release(self, company_name: Optional[str] = None):
        """
        Processa o release mais recente com análise livre.
        """
        print("\n🧠 AGENTE ECONOMISTA - Análise Livre")
        print("="*50)
        
        # Buscar documento mais recente
        if not self.parsed_dir.exists():
            print("❌ Pasta 'documents/parsed' não encontrada")
            return None
        
        json_files = list(self.parsed_dir.glob("*.json"))
        if not json_files:
            print("❌ Nenhum documento encontrado")
            return None
        
        # Filtrar por empresa se especificado
        if company_name:
            json_files = [f for f in json_files if company_name.upper() in f.name.upper()]
        
        if not json_files:
            print(f"❌ Nenhum documento encontrado para {company_name}")
            return None
        
        # Pegar o mais recente
        latest_file = max(json_files, key=lambda x: x.stat().st_mtime)
        print(f"📄 Analisando: {latest_file.name}")
        
        # Análise livre
        print("\n🔍 Realizando análise econômico-financeira...")
        analysis = self.analyze_document_freely(latest_file)
        
        # Gerar resumo
        print("✍️ Preparando avaliação...")
        summary = self.generate_executive_summary_free(analysis)
        
        # Salvar
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = self.summaries_dir / f"analise_livre_{analysis['company_context']['company']}_{timestamp}.md"
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        print(f"💾 Análise salva em: {summary_file}")
        
        # Exibir
        print("\n" + "="*50)
        print(summary)
        print("="*50)
        
        return {
            'analysis': analysis,
            'summary': summary,
            'file': str(summary_file)
        }


def main():
    """Teste do agente livre."""
    agent = EconomistAgentFree()
    agent.process_latest_release()


if __name__ == "__main__":
    main()