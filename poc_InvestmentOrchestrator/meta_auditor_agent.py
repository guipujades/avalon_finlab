#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
META-AUDITOR AGENT - Auditoria Sistêmica com Gemini
Avalia todo o processo multi-agente e sugere melhorias
UTILIZA GEMINI (Google) para análise meta-sistêmica
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import asyncio

# Importação do Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# NOVO: Import do cost tracker
from cost_tracker import track_gemini_call

# NOVO: Import do sistema de histórico completo
from process_history import process_history_manager

@dataclass
class SystemAuditResult:
    """Resultado da auditoria sistêmica"""
    overall_efficiency: float  # 0-1
    integration_quality: float  # 0-1
    process_optimization_score: float  # 0-1
    bottlenecks_identified: List[str]
    improvement_suggestions: List[str]
    system_health_assessment: str
    agent_performance_analysis: Dict
    recommended_changes: List[str]
    meta_insights: str

@dataclass
class ProcessData:
    """Dados completos do processo para auditoria"""
    query: str
    research_response: str
    supervisor_feedback: Dict
    maestro_feedback: Dict
    execution_flow: List[Dict]
    timing_data: Dict
    user_satisfaction: Optional[int]
    final_response: str

class MetaAuditorAgent:
    """Meta-auditor que usa Gemini para avaliar todo o sistema"""
    
    def __init__(self, gemini_key: str = None):
        """
        Inicializa o Meta-Auditor Agent com Gemini
        """
        # Configuração do Gemini
        self.gemini_key = gemini_key or os.getenv("GEMINI_API_KEY")
        
        if self.gemini_key:
            import google.generativeai as genai
            genai.configure(api_key=self.gemini_key)
            self.model = genai.GenerativeModel('gemini-1.5-pro')
            self.gemini_available = True
        else:
            self.model = None
            self.gemini_available = False
        
        # Histórico de auditorias
        self.audit_history = []
        self.history_file = "meta_auditor_history.json"
        
        # Carregar histórico existente
        self._load_history()
        
        # Configurações
        self.audit_config = {
            "max_audit_time": 30.0,  # segundos
            "min_efficiency_threshold": 0.6,
            "quality_weight": 0.4,
            "timing_weight": 0.3,
            "integration_weight": 0.3
        }
        
        # Métricas do sistema
        self.system_metrics = {
            "total_audits": 0,
            "avg_efficiency": 0.0,
            "critical_issues_found": 0,
            "improvements_suggested": 0
        }
        
        # Padrões conhecidos de problemas
        self.known_issues = {
            "integration_failures": [
                "timeout entre agentes",
                "dados perdidos na transferência",
                "formato inconsistente"
            ],
            "efficiency_bottlenecks": [
                "múltiplas chamadas LLM desnecessárias",
                "processamento sequencial onde poderia ser paralelo",
                "cache não utilizado adequadamente"
            ],
            "quality_issues": [
                "supervisão insuficiente",
                "feedback loop inadequado",
                "validação incompleta"
            ]
        }
        
        # NOVO: Acesso ao histórico completo do sistema
        self.process_history_manager = process_history_manager
    
    async def audit_complete_process(self, process_data: ProcessData) -> SystemAuditResult:
        """Executa auditoria completa do processo com acesso ao histórico sistêmico"""
        
        print("META-AUDITOR: Iniciando auditoria sistêmica completa...")
        start_time = datetime.now()
        
        try:
            # NOVO: Obtém histórico completo para auditoria contextualizada
            complete_system_history = self.process_history_manager.get_complete_history_for_agents()
            
            # Constrói contexto expandido incluindo histórico
            expanded_context = self._build_expanded_audit_context(process_data, complete_system_history)
            
            if not self.gemini_available:
                print("META-AUDITOR: Gemini indisponível - auditoria limitada")
                return self._create_limited_audit(process_data, complete_system_history)
            
            # Análise de eficiência com contexto histórico
            efficiency_analysis = await self._analyze_efficiency_with_history(expanded_context, complete_system_history)
            
            # Análise de integrações sistêmicas
            integration_analysis = await self._analyze_system_integrations(expanded_context, complete_system_history)
            
            # Análise de performance dos agentes
            agent_performance = await self._analyze_agent_performance_trends(expanded_context, complete_system_history)
            
            # Análise de saúde sistêmica
            system_health = await self._analyze_comprehensive_system_health(expanded_context, complete_system_history)
            
            # Geração de insights meta-sistêmicos
            meta_insights = await self._generate_comprehensive_meta_insights(
                expanded_context, efficiency_analysis, integration_analysis, 
                agent_performance, system_health, complete_system_history
            )
            
            # Compila resultado final da auditoria
            audit_result = self._compile_comprehensive_audit_result(
                efficiency_analysis, integration_analysis, agent_performance, 
                system_health, meta_insights, complete_system_history
            )
            
            # Registra auditoria no histórico
            self._record_comprehensive_audit(process_data, audit_result, complete_system_history)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            print(f"META-AUDITOR: Auditoria completa em {execution_time:.2f}s - Eficiência: {audit_result.overall_efficiency:.2f}")
            
            return audit_result
            
        except Exception as e:
            print(f"META-AUDITOR: Erro na auditoria sistêmica - {str(e)}")
            return self._create_fallback_audit_with_history(complete_system_history if 'complete_system_history' in locals() else {})
    
    def _build_expanded_audit_context(self, process_data: ProcessData, system_history: Dict) -> str:
        """Constrói contexto expandido para auditoria incluindo todo o histórico sistêmico"""
        
        # Contexto do processo atual
        current_context = self._build_audit_context(process_data)
        
        # NOVO: Contexto histórico expandido
        historical_context = f"""

HISTÓRICO SISTÊMICO COMPLETO:
{'='*50}

MÉTRICAS DE PERFORMANCE HISTÓRICAS:
{json.dumps(system_history.get("performance_metrics", {}), ensure_ascii=False, indent=2)}

PADRÕES DE PROCESSO IDENTIFICADOS:
{json.dumps(system_history.get("process_patterns", {}), ensure_ascii=False, indent=2)}

ANÁLISE DE CUSTOS SISTÊMICOS:
{json.dumps(system_history.get("cost_analysis", {}), ensure_ascii=False, indent=2)}

TENDÊNCIAS DE SATISFAÇÃO:
{json.dumps(system_history.get("user_satisfaction_trends", {}), ensure_ascii=False, indent=2)}

CONVERSAS COM AGENTES (insight arquitetural):
{json.dumps(system_history.get("agent_conversations", {}), ensure_ascii=False, indent=2)}

PROCESSOS RECENTES DETALHADOS:
{json.dumps(system_history.get("recent_processes", [])[-5:], ensure_ascii=False, indent=2)}

STEPS DETALHADOS DO SISTEMA:
{json.dumps(system_history.get("all_process_steps", [])[-20:], ensure_ascii=False, indent=2)}

TOTAL DE PROCESSOS ANALISADOS: {system_history.get("total_processes", 0)}
"""
        
        return current_context + historical_context
    
    async def _analyze_efficiency_with_history(self, context: str, system_history: Dict) -> Dict:
        """Análise de eficiência considerando todo o histórico sistêmico"""
        
        efficiency_prompt = f"""Como Meta-Auditor sistêmico com acesso ao histórico completo, analise a eficiência do sistema:

{context}

ANÁLISE REQUERIDA:
1. Eficiência atual vs histórica
2. Tendências de melhoria/degradação
3. Identificação de gargalos recorrentes
4. Padrões de falha sistêmica
5. Oportunidades de otimização baseadas no histórico

Considerando o histórico completo de {system_history.get("total_processes", 0)} processos, analise:

EFICIÊNCIA DE PIPELINE:
- Tempo médio vs processos anteriores
- Gargalos identificados historicamente
- Padrões de falha recorrentes

EFICIÊNCIA DE AGENTES:
- Performance individual baseada no histórico
- Padrões de uso eficiente
- Necessidade de ajustes

EFICIÊNCIA DE CUSTOS:
- Tendências de gasto
- ROI das operações
- Otimizações possíveis

Retorne APENAS um JSON válido sem nenhum texto adicional:
{{
    "current_efficiency": 0.8,
    "historical_comparison": {{
        "trend": "improving",
        "efficiency_change": 0.1,
        "historical_avg": 0.7
    }},
    "bottlenecks_identified": ["exemplo de gargalo"],
    "performance_by_agent": {{
        "research_agent": {{"efficiency": 0.8, "trend": "stable"}},
        "supervisor_agent": {{"efficiency": 0.8, "trend": "stable"}},
        "maestro_agent": {{"efficiency": 0.7, "trend": "stable"}}
    }},
    "cost_efficiency": {{
        "cost_per_process": 0.001,
        "cost_trend": "stable",
        "optimization_potential": 0.3
    }},
    "recurring_issues": ["problemas recorrentes"],
    "improvement_opportunities": ["oportunidades identificadas"]
}}"""

        try:
            efficiency_response = await self._call_gemini(efficiency_prompt, "comprehensive_efficiency", "system_audit")
            
            # Melhor tratamento da resposta do Gemini
            if not efficiency_response or efficiency_response.strip() == "":
                print("META-AUDITOR: Resposta vazia do Gemini - usando fallback")
                return self._create_fallback_efficiency_analysis(system_history)
            
            # Tenta limpar a resposta antes do parsing
            cleaned_response = efficiency_response.strip()
            
            # Remove possíveis marcadores de código
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response.replace('```json', '').replace('```', '').strip()
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response.replace('```', '').strip()
            
            analysis = json.loads(cleaned_response)
            
            # NOVO: Adiciona métricas calculadas do histórico
            analysis["calculated_metrics"] = self._calculate_historical_efficiency_metrics(system_history)
            
            return analysis
        except json.JSONDecodeError as e:
            print(f"META-AUDITOR: Erro no parsing JSON - {e}")
            print(f"META-AUDITOR: Resposta recebida: {efficiency_response[:200] if efficiency_response else 'VAZIA'}")
            return self._create_fallback_efficiency_analysis(system_history)
        except Exception as e:
            print(f"META-AUDITOR: Erro na análise de eficiência - {e}")
            return self._create_fallback_efficiency_analysis(system_history)
    
    async def _analyze_system_integrations(self, context: str, system_history: Dict) -> Dict:
        """Análise de integrações sistêmicas com base no histórico"""
        
        integration_prompt = f"""Analise as integrações sistêmicas considerando o histórico completo:

{context}

Avalie especificamente:

INTEGRAÇÃO ENTRE AGENTES:
- Comunicação Orchestrator ↔ Research Agent
- Comunicação Research Agent ↔ Maestro
- Fluxo Supervisor → Meta-Auditor
- Sincronização de dados entre componentes

INTEGRAÇÃO DE DADOS:
- Consistência do histórico de processos
- Sincronização de conversas entre agentes
- Integridade dos dados de custo
- Persistência e recuperação de dados

INTEGRAÇÃO DE FUNCIONALIDADES:
- Pipeline completo de processamento
- Sistema de feedback e aprendizado
- Modos Admin vs Usuário
- Sistema de conversas diretas

Baseado no histórico de {system_history.get("total_processes", 0)} processos e conversas registradas:

Retorne APENAS um JSON válido:
{{
    "integration_score": 0.8,
    "agent_communication": {{
        "orchestrator_research": {{"quality": 0.8, "issues": []}},
        "research_maestro": {{"quality": 0.8, "issues": []}},
        "supervisor_meta": {{"quality": 0.8, "issues": []}}
    }},
    "data_consistency": {{
        "score": 0.8,
        "consistency_issues": [],
        "sync_problems": []
    }},
    "feature_integration": {{
        "pipeline_integrity": 0.8,
        "mode_switching": 0.9,
        "conversation_system": 0.8
    }},
    "integration_bottlenecks": ["exemplo"],
    "recommended_improvements": ["exemplo"]
}}"""

        try:
            integration_response = await self._call_gemini(integration_prompt, "system_integration", "integration_audit")
            
            if not integration_response or integration_response.strip() == "":
                print("META-AUDITOR: Resposta vazia do Gemini para integração - usando fallback")
                return self._create_fallback_integration_analysis()
            
            # Limpa resposta
            cleaned_response = integration_response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response.replace('```json', '').replace('```', '').strip()
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response.replace('```', '').strip()
            
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            print(f"META-AUDITOR: Erro no parsing JSON de integração - {e}")
            return self._create_fallback_integration_analysis()
        except Exception as e:
            print(f"META-AUDITOR: Erro na análise de integração - {e}")
            return self._create_fallback_integration_analysis()
    
    async def _analyze_agent_performance_trends(self, context: str, system_history: Dict) -> Dict:
        """Análise de performance dos agentes com tendências históricas"""
        
        agent_conversations = system_history.get("agent_conversations", {})
        
        performance_prompt = f"""Analise a performance individual de cada agente baseado no histórico completo:

{context}

CONVERSAS DIRETAS COM AGENTES:
{json.dumps(agent_conversations, ensure_ascii=False, indent=2)}

Para cada agente, analise:

MAESTRO AGENT:
- Qualidade das orientações fornecidas
- Efetividade do aprendizado de parâmetros
- Precisão na coleta de feedback
- Tendências de melhoria

SUPERVISOR AGENT:
- Precisão na identificação de problemas
- Qualidade das correções sugeridas
- Taxa de aprovação apropriada
- Efetividade do fact-checking

META-AUDITOR AGENT:
- Qualidade das auditorias sistêmicas
- Relevância dos insights fornecidos
- Precisão na identificação de gargalos
- Utilidade das recomendações

RESEARCH AGENT:
- Qualidade das pesquisas
- Adequação da seleção de fontes
- Eficiência no processamento
- Satisfação do usuário com resultados

Retorne APENAS um JSON válido:
{{
    "agent_performance": {{
        "maestro": {{
            "overall_score": 0.8,
            "learning_effectiveness": 0.7,
            "feedback_quality": 0.8,
            "improvement_trend": "stable",
            "key_strengths": ["exemplo"],
            "areas_for_improvement": ["exemplo"]
        }},
        "supervisor": {{
            "overall_score": 0.8,
            "detection_accuracy": 0.8,
            "correction_quality": 0.7,
            "improvement_trend": "stable",
            "key_strengths": ["exemplo"],
            "areas_for_improvement": ["exemplo"]
        }},
        "meta_auditor": {{
            "overall_score": 0.7,
            "audit_depth": 0.8,
            "insight_relevance": 0.7,
            "improvement_trend": "stable",
            "key_strengths": ["exemplo"],
            "areas_for_improvement": ["exemplo"]
        }},
        "research": {{
            "overall_score": 0.8,
            "search_quality": 0.8,
            "result_relevance": 0.8,
            "improvement_trend": "stable",
            "key_strengths": ["exemplo"],
            "areas_for_improvement": ["exemplo"]
        }}
    }},
    "cross_agent_synergy": 0.8,
    "collaboration_effectiveness": ["exemplo"],
    "system_wide_recommendations": ["exemplo"]
}}"""

        try:
            performance_response = await self._call_gemini(performance_prompt, "agent_performance", "performance_audit")
            
            if not performance_response or performance_response.strip() == "":
                print("META-AUDITOR: Resposta vazia do Gemini para performance - usando fallback")
                return self._create_fallback_performance_analysis()
            
            # Limpa resposta
            cleaned_response = performance_response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response.replace('```json', '').replace('```', '').strip()
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response.replace('```', '').strip()
            
            analysis = json.loads(cleaned_response)
            
            # NOVO: Adiciona métricas quantitativas do histórico
            analysis["quantitative_metrics"] = self._calculate_agent_performance_metrics(system_history)
            
            return analysis
        except json.JSONDecodeError as e:
            print(f"META-AUDITOR: Erro no parsing JSON de performance - {e}")
            return self._create_fallback_performance_analysis()
        except Exception as e:
            print(f"META-AUDITOR: Erro na análise de performance - {e}")
            return self._create_fallback_performance_analysis()
    
    async def _analyze_comprehensive_system_health(self, context: str, system_history: Dict) -> Dict:
        """Análise abrangente da saúde sistêmica"""
        
        health_prompt = f"""Como Meta-Auditor sistêmico, avalie a saúde geral do sistema multi-agente:

{context}

INDICADORES DE SAÚDE A AVALIAR:

SAÚDE OPERACIONAL:
- Estabilidade dos componentes
- Taxa de erro vs sucesso
- Disponibilidade dos serviços
- Resiliência a falhas

SAÚDE DE DADOS:
- Integridade dos dados históricos
- Consistência entre componentes
- Qualidade dos metadados
- Completude dos registros

SAÚDE DE PERFORMANCE:
- Tendências de tempo de resposta
- Eficiência de recursos
- Escalabilidade atual
- Gargalos sistêmicos

SAÚDE DE EXPERIÊNCIA:
- Satisfação do usuário ao longo do tempo
- Qualidade das respostas
- Facilidade de uso
- Efetividade do sistema

SAÚDE ARQUITETURAL:
- Qualidade das integrações
- Modularidade dos componentes
- Manutenibilidade do código
- Extensibilidade futura

Baseado em {system_history.get("total_processes", 0)} processos analisados:

Retorne APENAS um JSON válido:
{{
    "overall_health_score": 0.8,
    "health_indicators": {{
        "operational": {{"score": 0.8, "status": "stable", "issues": []}},
        "data_integrity": {{"score": 0.7, "status": "stable", "issues": ["exemplo"]}},
        "performance": {{"score": 0.8, "status": "stable", "issues": []}},
        "user_experience": {{"score": 0.8, "status": "stable", "issues": []}},
        "architectural": {{"score": 0.8, "status": "stable", "issues": []}}
    }},
    "critical_health_issues": ["exemplo"],
    "health_trends": {{
        "short_term": "stable",
        "long_term": "stable"
    }},
    "system_resilience": 0.8,
    "maintenance_recommendations": ["exemplo"],
    "upgrade_priorities": ["exemplo"]
}}"""

        try:
            health_response = await self._call_gemini(health_prompt, "system_health", "health_audit")
            
            if not health_response or health_response.strip() == "":
                print("META-AUDITOR: Resposta vazia do Gemini para saúde - usando fallback")
                return self._create_fallback_health_analysis()
            
            # Limpa resposta
            cleaned_response = health_response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response.replace('```json', '').replace('```', '').strip()
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response.replace('```', '').strip()
            
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            print(f"META-AUDITOR: Erro no parsing JSON de saúde - {e}")
            return self._create_fallback_health_analysis()
        except Exception as e:
            print(f"META-AUDITOR: Erro na análise de saúde - {e}")
            return self._create_fallback_health_analysis()
    
    async def _generate_comprehensive_meta_insights(self, context: str, efficiency: Dict, 
                                                  integration: Dict, performance: Dict, 
                                                  health: Dict, system_history: Dict) -> str:
        """Gera insights meta-sistêmicos abrangentes"""
        
        insights_prompt = f"""Como Meta-Auditor com visão sistêmica completa, gere insights estratégicos:

CONTEXTO COMPLETO:
{context}

ANÁLISES REALIZADAS:
Eficiência: {json.dumps(efficiency, ensure_ascii=False, indent=2)}
Integração: {json.dumps(integration, ensure_ascii=False, indent=2)}
Performance: {json.dumps(performance, ensure_ascii=False, indent=2)}
Saúde: {json.dumps(health, ensure_ascii=False, indent=2)}

HISTÓRICO SISTÊMICO:
Total de processos: {system_history.get("total_processes", 0)}
Tendência de satisfação: {system_history.get("user_satisfaction_trends", {})}
Análise de custos: {system_history.get("cost_analysis", {})}

Gere insights meta-sistêmicos que incluam:

1. PADRÕES EMERGENTES no comportamento do sistema
2. OPORTUNIDADES ESTRATÉGICAS para melhorias sistêmicas
3. RISCOS SISTÊMICOS identificados
4. RECOMENDAÇÕES ARQUITETURAIS para evolução
5. INSIGHTS SOBRE O FUTURO do sistema

Forneça uma análise narrativa profunda e estratégica sobre o estado e futuro do sistema."""

        try:
            insights_response = await self._call_gemini(insights_prompt, "meta_insights", "strategic_analysis")
            return insights_response
        except Exception as e:
            print(f"META-AUDITOR: Erro na geração de insights - {e}")
            return f"Meta-insights indisponíveis devido a erro: {str(e)}"
    
    def _compile_comprehensive_audit_result(self, efficiency: Dict, integration: Dict, 
                                            performance: Dict, health: Dict, insights: str, system_history: Dict) -> SystemAuditResult:
        """Compila resultado final da auditoria"""
        
        # Calcula scores gerais
        overall_efficiency = (
            efficiency.get("efficiency_score", 0.7) * 0.3 +
            integration.get("integration_quality", 0.8) * 0.3 +
            health.get("system_health_score", 0.8) * 0.4
        )
        
        # Coleta todos os problemas e sugestões
        all_bottlenecks = (
            efficiency.get("bottlenecks", []) +
            integration.get("communication_issues", []) +
            health.get("critical_risks", [])
        )
        
        all_suggestions = (
            efficiency.get("optimization_suggestions", []) +
            integration.get("interface_improvements", []) +
            health.get("evolution_opportunities", [])
        )
        
        return SystemAuditResult(
            overall_efficiency=overall_efficiency,
            integration_quality=integration.get("integration_quality", 0.8),
            process_optimization_score=efficiency.get("efficiency_score", 0.7),
            bottlenecks_identified=all_bottlenecks,
            improvement_suggestions=all_suggestions,
            system_health_assessment=health.get("system_health_score", 0.8),
            agent_performance_analysis=performance,
            recommended_changes=health.get("maintenance_needs", []),
            meta_insights=insights
        )
    
    def _create_limited_audit(self, process_data: ProcessData, system_history: Dict) -> SystemAuditResult:
        """Cria auditoria limitada quando Gemini não está disponível"""
        
        # Análise baseada apenas em dados quantitativos do histórico
        performance_metrics = system_history.get("performance_metrics", {})
        
        return SystemAuditResult(
            overall_efficiency=performance_metrics.get("success_rate", 0.7),
            integration_quality=0.8,  # Assumido baseado em funcionalidade
            process_optimization_score=0.7,
            bottlenecks_identified=["Gemini indisponível para análise detalhada"],
            improvement_suggestions=[
                "Configure GEMINI_API_KEY para auditoria completa",
                "Baseado no histórico: manter padrão de qualidade atual"
            ],
            system_health_assessment="Limitado - configure Gemini para análise completa",
            agent_performance_analysis={"status": "Análise limitada"},
            recommended_changes=["Habilitar auditoria completa com Gemini"],
            meta_insights=f"Sistema processou {system_history.get('total_processes', 0)} processos com auditoria limitada"
        )
    
    def _create_fallback_audit_with_history(self, system_history: Dict) -> SystemAuditResult:
        """Cria auditoria de fallback usando dados históricos"""
        
        try:
            performance_metrics = system_history.get("performance_metrics", {})
            cost_analysis = system_history.get("cost_analysis", {})
            
            return SystemAuditResult(
                overall_efficiency=performance_metrics.get("success_rate", 0.6),
                integration_quality=0.7,
                process_optimization_score=0.6,
                bottlenecks_identified=["Erro na auditoria automática"],
                improvement_suggestions=[
                    "Verificar logs de sistema",
                    f"Sistema processou {system_history.get('total_processes', 0)} processos"
                ],
                system_health_assessment="Auditoria com erro - verificar sistema",
                agent_performance_analysis={"historical_data": performance_metrics},
                recommended_changes=["Investigar causas do erro de auditoria"],
                meta_insights="Auditoria de fallback baseada em dados históricos disponíveis"
            )
        except Exception:
            return self._create_fallback_audit()
    
    def _save_history(self):
        """Salva o histórico de auditorias em arquivo JSON"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.audit_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[META-AUDITOR] Erro ao salvar histórico: {e}")
    
    def _load_history(self):
        """Carrega o histórico de auditorias do arquivo JSON"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.audit_history = json.load(f)
                print(f"[META-AUDITOR] Histórico carregado: {len(self.audit_history)} auditorias")
            else:
                self.audit_history = []
        except Exception as e:
            print(f"[META-AUDITOR] Erro ao carregar histórico: {e}")
            self.audit_history = []
    
    def _record_comprehensive_audit(self, process_data: ProcessData, audit_result: SystemAuditResult, system_history: Dict):
        """Registra uma auditoria no histórico"""
        
        audit_record = {
            "timestamp": datetime.now().isoformat(),
            "query": process_data.query,
            "response_preview": process_data.final_response[:200] + "..." if len(process_data.final_response) > 200 else process_data.final_response,
            "overall_efficiency": audit_result.overall_efficiency,
            "meta_insights": {
                "primary_insight": audit_result.meta_insights[:100] + "..." if len(audit_result.meta_insights) > 100 else audit_result.meta_insights,
                "full_insights": audit_result.meta_insights
            },
            "recommendations": audit_result.improvement_suggestions,
            "efficiency_breakdown": {
                "timing_efficiency": audit_result.process_optimization_score,
                "quality_efficiency": audit_result.integration_quality,
                "integration_efficiency": audit_result.overall_efficiency
            },
            "system_health": audit_result.system_health_assessment,
            "agents_performance": {
                "research_agent": audit_result.agent_performance_analysis.get("research_agent", {}).get("quality_score", 0.5),
                "supervisor_performance": audit_result.agent_performance_analysis.get("supervisor_agent", {}).get("quality_score", 0.5),
                "maestro_performance": audit_result.agent_performance_analysis.get("maestro_agent", {}).get("learning_effectiveness", 0.5)
            },
            "bottlenecks": audit_result.bottlenecks_identified,
            "recommended_changes": audit_result.recommended_changes,
            "system_history": system_history
        }
        
        self.audit_history.append(audit_record)
        
        # Salvar automaticamente
        self._save_history()
        
        # Atualizar estatísticas
        self._update_statistics(audit_result.overall_efficiency)
        
        # Manter apenas os últimos 100 registros na memória
        if len(self.audit_history) > 100:
            self.audit_history = self.audit_history[-100:]
            self._save_history()  # Salvar após limpeza
    
    def _update_statistics(self, efficiency: float):
        """Atualiza estatísticas internas"""
        if not hasattr(self, 'system_metrics'):
            self.system_metrics = {
                "total_audits": 0,
                "avg_efficiency": 0.0,
                "critical_issues_found": 0,
                "improvements_suggested": 0
            }
        
        self.system_metrics["total_audits"] += 1
        
        # Calcula média móvel da eficiência
        if self.audit_history:
            total_efficiency = sum(audit.get("overall_efficiency", 0.0) for audit in self.audit_history)
            self.system_metrics["avg_efficiency"] = total_efficiency / len(self.audit_history)
        
        # Conta problemas críticos
        if efficiency < 0.6:
            self.system_metrics["critical_issues_found"] += 1
    
    def get_audit_statistics(self) -> Dict:
        """Retorna estatísticas das auditorias"""
        
        if self.system_metrics["total_audits"] == 0:
            return {"message": "Nenhuma auditoria realizada ainda"}
        
        recent_audits = self.audit_history[-10:] if self.audit_history else []
        recent_avg = sum(audit["overall_efficiency"] for audit in recent_audits) / len(recent_audits) if recent_audits else 0
        
        return {
            "total_audits": self.system_metrics["total_audits"],
            "avg_efficiency": f"{self.system_metrics['avg_efficiency']:.2f}",
            "recent_avg_efficiency": f"{recent_avg:.2f}",
            "critical_issues_found": self.system_metrics["critical_issues_found"],
            "improvements_suggested": self.system_metrics["improvements_suggested"],
            "gemini_status": "Ativo" if self.model else "Inativo"
        }
    
    def get_recent_audits(self, limit: int = 5) -> List[Dict]:
        """Retorna auditorias recentes"""
        return self.audit_history[-limit:] if self.audit_history else []
    
    async def _call_gemini(self, prompt: str, operation: str = "audit", query_context: str = "") -> str:
        """Chama Gemini com rastreamento de custos"""
        
        if not self.model or not self.gemini_available:
            raise Exception("Gemini não disponível")
        
        try:
            response = self.model.generate_content(prompt)
            
            # NOVO: Rastreamento de custos para Gemini
            # Gemini não fornece token count diretamente, então estimamos
            estimated_input = len(prompt.split()) * 1.3  # Aproximação tokens/palavras
            estimated_output = len(response.text.split()) * 1.3
            
            cost = track_gemini_call(
                model="gemini-1.5-pro",
                input_tokens=int(estimated_input),
                output_tokens=int(estimated_output),
                operation=operation,
                query_context=query_context or "meta_audit_analysis",
                response_preview=response.text[:100] if response.text else "empty_response"
            )
            
            print(f"META-AUDITOR (Gemini): ${cost:.6f} USD (~{int(estimated_input + estimated_output)} tokens)")
            
            return response.text
            
        except Exception as e:
            print(f"META-AUDITOR: Erro no Gemini - {e}")
            raise
    
    def _build_audit_context(self, process_data) -> str:
        """Constrói contexto básico para auditoria"""
        return f"""
DADOS DO PROCESSO PARA AUDITORIA:
{'='*50}

CONSULTA ORIGINAL: {process_data.query}

RESPOSTA DA PESQUISA: {process_data.research_response}

FEEDBACK DO SUPERVISOR: {json.dumps(process_data.supervisor_feedback, ensure_ascii=False, indent=2)}

FEEDBACK DO MAESTRO: {json.dumps(process_data.maestro_feedback, ensure_ascii=False, indent=2)}

FLUXO DE EXECUÇÃO: {json.dumps(process_data.execution_flow, ensure_ascii=False, indent=2)}

DADOS DE TIMING: {json.dumps(process_data.timing_data, ensure_ascii=False, indent=2)}

SATISFAÇÃO DO USUÁRIO: {process_data.user_satisfaction}/5

RESPOSTA FINAL: {process_data.final_response}
"""
    
    def _calculate_historical_efficiency_metrics(self, system_history: Dict) -> Dict:
        """Calcula métricas de eficiência baseadas no histórico"""
        try:
            performance_metrics = system_history.get("performance_metrics", {})
            cost_analysis = system_history.get("cost_analysis", {})
            process_patterns = system_history.get("process_patterns", {})
            
            return {
                "historical_success_rate": performance_metrics.get("success_rate", 0.7),
                "historical_avg_cost": cost_analysis.get("avg_cost_per_process", 0.001),
                "historical_avg_execution_time": process_patterns.get("avg_execution_time", 5.0),
                "trend_analysis": "stable",  # Seria calculado com mais dados
                "efficiency_score": performance_metrics.get("success_rate", 0.7)
            }
        except Exception:
            return {"efficiency_score": 0.7}
    
    def _calculate_agent_performance_metrics(self, system_history: Dict) -> Dict:
        """Calcula métricas quantitativas de performance dos agentes"""
        try:
            agent_conversations = system_history.get("agent_conversations", {})
            all_steps = system_history.get("all_process_steps", [])
            
            metrics = {}
            
            # Analisa performance por tipo de agent baseado nos steps
            agent_types = ["research_agent", "supervisor_agent", "meta_auditor_agent", "orchestrator"]
            
            for agent_type in agent_types:
                agent_steps = [step for step in all_steps if step.get('agent') == agent_type]
                
                if agent_steps:
                    avg_execution_time = sum(step.get('execution_time', 0) for step in agent_steps) / len(agent_steps)
                    success_rate = 0.8  # Baseado em heurísticas - seria melhor com dados reais
                else:
                    avg_execution_time = 0
                    success_rate = 0.7
                
                metrics[agent_type] = {
                    "avg_execution_time": avg_execution_time,
                    "success_rate": success_rate,
                    "total_steps": len(agent_steps),
                    "conversations_count": len(agent_conversations.get(agent_type.replace("_agent", ""), []))
                }
            
            return metrics
            
        except Exception as e:
            print(f"META-AUDITOR: Erro ao calcular métricas de agentes - {e}")
            return {}
    
    def _create_fallback_audit(self) -> SystemAuditResult:
        """Cria auditoria de fallback quando há problemas"""
        return SystemAuditResult(
            overall_efficiency=0.7,
            integration_quality=0.8,
            process_optimization_score=0.7,
            bottlenecks_identified=["Gemini indisponível para análise detalhada"],
            improvement_suggestions=[
                "Configure GEMINI_API_KEY para auditoria completa",
                "Sistema funcionando em modo básico"
            ],
            system_health_assessment="Auditoria limitada - configure Gemini",
            agent_performance_analysis={"status": "Análise limitada"},
            recommended_changes=["Habilitar auditoria completa"],
            meta_insights="Sistema operando sem auditoria completa do Gemini"
        )
    
    def _create_fallback_efficiency_analysis(self, system_history: Dict) -> Dict:
        """Cria análise de eficiência de fallback"""
        try:
            performance_metrics = system_history.get("performance_metrics", {})
            return {
                "current_efficiency": performance_metrics.get("success_rate", 0.7),
                "historical_comparison": {
                    "trend": "stable",
                    "efficiency_change": 0,
                    "historical_avg": performance_metrics.get("avg_satisfaction", 3.5)
                },
                "bottlenecks_identified": ["Análise completa indisponível"],
                "improvement_opportunities": ["Configure Gemini para análise detalhada"]
            }
        except Exception:
            return {"current_efficiency": 0.7, "bottlenecks_identified": ["Erro na análise"]}
    
    def _create_fallback_integration_analysis(self) -> Dict:
        """Cria análise de integração de fallback"""
        
        return {
            "integration_score": 0.8,
            "agent_communication": {
                "orchestrator_research": {"quality": 0.8, "issues": []},
                "research_maestro": {"quality": 0.8, "issues": []},
                "supervisor_meta": {"quality": 0.8, "issues": []}
            },
            "data_consistency": {
                "score": 0.7,
                "consistency_issues": ["Análise automática indisponível"],
                "sync_problems": []
            },
            "feature_integration": {
                "pipeline_integrity": 0.8,
                "mode_switching": 0.9,
                "conversation_system": 0.8
            },
            "integration_bottlenecks": ["Verificação automática falhou"],
            "recommended_improvements": ["Verificar configuração dos agentes"]
        }
    
    def _create_fallback_performance_analysis(self) -> Dict:
        """Cria análise de performance de fallback"""
        
        return {
            "agent_performance": {
                "maestro": {
                    "overall_score": 0.8,
                    "learning_effectiveness": 0.7,
                    "feedback_quality": 0.8,
                    "improvement_trend": "stable",
                    "key_strengths": ["Feedback collection"],
                    "areas_for_improvement": ["Analysis automation"]
                },
                "supervisor": {
                    "overall_score": 0.8,
                    "detection_accuracy": 0.8,
                    "correction_quality": 0.7,
                    "improvement_trend": "stable",
                    "key_strengths": ["Quality control"],
                    "areas_for_improvement": ["Fact checking"]
                },
                "meta_auditor": {
                    "overall_score": 0.7,
                    "audit_depth": 0.8,
                    "insight_relevance": 0.7,
                    "improvement_trend": "stable",
                    "key_strengths": ["System overview"],
                    "areas_for_improvement": ["Detailed analysis"]
                },
                "research": {
                    "overall_score": 0.8,
                    "search_quality": 0.8,
                    "result_relevance": 0.8,
                    "improvement_trend": "stable",
                    "key_strengths": ["Information gathering"],
                    "areas_for_improvement": ["Source verification"]
                }
            },
            "cross_agent_synergy": 0.8,
            "collaboration_effectiveness": ["Análise automática indisponível"],
            "system_wide_recommendations": ["Verificar configuração para análise completa"]
        }
    
    def _create_fallback_health_analysis(self) -> Dict:
        """Cria análise de saúde de fallback"""
        
        return {
            "overall_health_score": 0.8,
            "health_indicators": {
                "operational": {"score": 0.8, "status": "stable", "issues": []},
                "data_integrity": {"score": 0.7, "status": "stable", "issues": ["Análise automática limitada"]},
                "performance": {"score": 0.8, "status": "stable", "issues": []},
                "user_experience": {"score": 0.8, "status": "stable", "issues": []},
                "architectural": {"score": 0.8, "status": "stable", "issues": []}
            },
            "critical_health_issues": ["Análise automática indisponível"],
            "health_trends": {
                "short_term": "stable",
                "long_term": "stable"
            },
            "system_resilience": 0.8,
            "maintenance_recommendations": ["Verificar configuração dos agentes"],
            "upgrade_priorities": ["Habilitar análise automática completa"]
        } 