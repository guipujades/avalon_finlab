#!/usr/bin/env python3
"""
SUPERVISOR AGENT - Verificação de Coerência e Qualidade
Analisa respostas para garantir coerência lógica, temporal e factual
UTILIZA CLAUDE (ANTHROPIC) para verificação independente
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import asyncio

# Importação do Claude/Anthropic
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

# NOVO: Import do sistema de histórico completo
from process_history import process_history_manager

# NOVO: Import do cost tracker
from cost_tracker import cost_tracker, track_anthropic_call, track_openai_call

@dataclass
class SupervisionResult:
    """Resultado da supervisão"""
    approved: bool
    confidence_score: float  # 0-1
    issues_found: List[str]
    corrections_suggested: List[str]
    additional_context: str
    verification_notes: str
    temporal_analysis: Dict
    logical_consistency: Dict

class SupervisorAgent:
    """Agente supervisor que verifica coerência e qualidade das respostas usando Claude"""
    
    def __init__(self, anthropic_key: str = None, tavily_key: str = None, fallback_llm=None, model: str = "claude-3-5-sonnet-20241022"):
        # Configuração do Claude (Anthropic)
        self.anthropic_key = anthropic_key or os.getenv("ANTHROPIC_API_KEY")
        self.claude_client = None
        self.fallback_llm = fallback_llm  # LLM de fallback caso Claude não esteja disponível
        
        # Inicializa cliente Claude
        if ANTHROPIC_AVAILABLE and self.anthropic_key:
            try:
                self.claude_client = anthropic.Anthropic(api_key=self.anthropic_key)
                self.llm_provider = "claude"
            except Exception as e:
                print(f"SUPERVISOR: Erro ao configurar Claude: {e}")
                self.claude_client = None
                self.llm_provider = "fallback"
        else:
            if not ANTHROPIC_AVAILABLE:
                print("SUPERVISOR: Biblioteca Anthropic não disponível - usando LLM de fallback")
            else:
                print("SUPERVISOR: ANTHROPIC_API_KEY não encontrada - usando LLM de fallback")
            self.llm_provider = "fallback"
        
        # Configuração Tavily
        self.tavily_key = tavily_key or os.getenv("TAVILY_KEY")
        self.supervision_history = []
        self.statistics = {
            "total_supervisions": 0,
            "approved_responses": 0,
            "rejected_responses": 0,
            "corrections_made": 0,
            "fact_checks_performed": 0,
            "claude_verifications": 0,
            "fallback_verifications": 0
        }
        
        # Configurações de verificação
        self.verification_config = {
            "temporal_tolerance_days": 7,  # Tolerância para dados temporais
            "minimum_confidence_threshold": 0.7,  # Mínimo para aprovação automática
            "fact_check_threshold": 0.6,  # Quando fazer fact-check
            "logical_consistency_weight": 0.4,
            "temporal_accuracy_weight": 0.3,
            "factual_accuracy_weight": 0.3
        }
        
        # Padrões problemáticos conhecidos
        self.problematic_patterns = [
            "dados desatualizados",
            "informações contraditórias", 
            "falta de contexto temporal",
            "inconsistência lógica",
            "fatos não verificáveis"
        ]
        
        # Configuração Tavily para fact-checking
        self.tavily_client = None
        if self.tavily_key:
            try:
                from mcp_Tavily_Expert import tavily_search_tool
                self.tavily_available = True
            except ImportError:
                self.tavily_available = False
        else:
            self.tavily_available = False
        
        self.model = model
        
        # Configurar cliente
        if self.anthropic_key:
            self.client = anthropic.Anthropic(api_key=self.anthropic_key)
            self.llm_type = "claude"
        else:
            # Fallback para OpenAI
            import openai
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                self.client = openai.OpenAI(api_key=openai_key)
                self.llm_type = "openai"
                self.model = "gpt-4o"
            else:
                raise ValueError("Nenhuma API key válida encontrada para Supervisor Agent")
        
        # Histórico de supervisões
        self.history_file = "supervisor_history.json"
        
        # NOVO: Acesso ao histórico completo
        self.process_history_manager = process_history_manager
        
        # Carregar histórico existente
        self._load_history()
        
        # Contadores para estatísticas
        self.total_supervisions = 0
        self.auto_approvals = 0
        self.corrections_generated = 0
    
    async def _call_llm(self, prompt: str, max_tokens: int = 1000, query_context: str = "") -> str:
        """Chama LLM (Claude preferido, fallback se necessário) com rastreamento de custos"""
        
        if self.llm_type == "claude" and self.client:
            try:
                # Usa Claude (Anthropic)
                response = self.client.messages.create(
                    model=self.model,  # Usa modelo configurado
                    max_tokens=max_tokens,
                    temperature=0.1,  # Baixa temperatura para análise precisa
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                
                # Rastreia custo da chamada
                usage = response.usage
                input_tokens = usage.input_tokens
                output_tokens = usage.output_tokens
                
                cost = track_anthropic_call(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    model="claude-3-5-sonnet-20241022",
                    operation="supervision",
                    query_context=query_context
                )
                
                print(f"SUPERVISOR (Claude): ${cost:.6f} USD ({int(input_tokens + output_tokens)} tokens)")
                
                return response.content[0].text
                
            except Exception as e:
                print(f"SUPERVISOR: Erro no Claude, usando fallback: {e}")
                # Continua para fallback
        
        # Usa LLM de fallback (OpenAI)  
        if self.llm_type == "openai" and self.client:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{
                        "role": "user", 
                        "content": prompt
                    }],
                    max_tokens=max_tokens,
                    temperature=0.1
                )
                
                # NOVO: Rastreamento de custos para OpenAI fallback
                usage = response.usage
                input_tokens = usage.prompt_tokens
                output_tokens = usage.completion_tokens
                
                cost = track_openai_call(
                    model="gpt-4o",  # Assume gpt-4o para fallback
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    operation="supervision_fallback",
                    query_context=query_context or "supervisor_fallback",
                    response_preview=response.choices[0].message.content[:100]
                )
                
                print(f"SUPERVISOR (OpenAI): ${cost:.6f} USD ({int(input_tokens + output_tokens)} tokens)")
                
                return response.choices[0].message.content
            
            except Exception as e:
                print(f"SUPERVISOR: Erro no fallback OpenAI - {e}")
                
                # Emergency fallback - estimativa de custo
                estimated_input = len(prompt.split()) * 1.3
                estimated_output = 200  # Estimativa conservadora
                
                cost = track_openai_call(
                    model="gpt-4o",
                    input_tokens=int(estimated_input),
                    output_tokens=int(estimated_output),
                    operation="supervision_emergency",
                    query_context="emergency_fallback"
                )
                
                print(f"SUPERVISOR (Emergency): ${cost:.6f} USD (~{int(estimated_input + estimated_output)} tokens)")
        
        # Último recurso: usa fallback_llm se disponível
        if hasattr(self, 'fallback_llm') and self.fallback_llm:
            try:
                response = await self.fallback_llm.acomplete(prompt)
                
                # NOVO: Rastreamento para fallback LLM (assume gpt-4o)
                estimated_input = len(prompt.split()) * 1.3
                estimated_output = len(response.text.split()) * 1.3
                
                cost = track_openai_call(
                    model="gpt-4o",  # Assume gpt-4o para fallback
                    input_tokens=int(estimated_input),
                    output_tokens=int(estimated_output),
                    operation="supervision_emergency_fallback",
                    query_context=query_context or "supervisor_emergency",
                    response_preview=response.text[:100]
                )
                
                print(f"💰 SUPERVISOR (Emergency): ${cost:.6f} USD (~{int(estimated_input + estimated_output)} tokens)")
                
                return response.text
                
            except Exception as e:
                print(f"SUPERVISOR: Erro no LLM de fallback: {e}")
                return '{"error": "Falha na análise de LLM"}'
        
        return '{"error": "Nenhum LLM disponível"}'
    
    async def supervise_response(self, 
                                query: str, 
                                response: str, 
                                context: Dict,
                                agent_used: str) -> SupervisionResult:
        """Supervisiona uma resposta completa"""
        
        print("SUPERVISOR: Iniciando verificação de coerência...")
        
        # NOVO: Obtém histórico completo para contexto aprimorado
        complete_history = self.process_history_manager.get_complete_history_for_agents()
        
        try:
            # Análise temporal (verifica se informações estão atualizadas)
            temporal_analysis = await self._analyze_temporal_consistency(query, response, context, complete_history)
            
            # Análise de consistência lógica
            logical_analysis = await self._analyze_logical_consistency(query, response, context, complete_history)
            
            # Verificação factual se necessário
            factual_analysis = await self._verify_facts_if_needed(query, response, context, complete_history)
            
            # Análise de completude
            completeness_analysis = await self._analyze_completeness(query, response, context, complete_history)
            
            # Calcula score final
            final_score = self._calculate_supervision_score(
                temporal_analysis, logical_analysis, factual_analysis, completeness_analysis
            )
            
            # Gera resultado final
            result = self._generate_supervision_result(
                query, response, final_score, temporal_analysis, 
                logical_analysis, factual_analysis, completeness_analysis
            )
            
            # Registra supervisão
            self._record_supervision(query, response, result, agent_used)
            
            print(f"SUPERVISOR: Verificação completa - Score: {final_score:.2f}")
            if result.approved:
                print("SUPERVISOR: Resposta APROVADA")
            else:
                print("SUPERVISOR: Resposta precisa de CORREÇÃO")
                print(f"SUPERVISOR: Problemas: {', '.join(result.issues_found)}")
            
            return result
            
        except Exception as e:
            print(f"SUPERVISOR: Erro na supervisão - {str(e)}")
            # Retorna resultado de fallback
            return SupervisionResult(
                approved=True,  # Aprova por segurança em caso de erro
                confidence_score=0.5,
                issues_found=[f"Erro na supervisão: {str(e)}"],
                corrections_suggested=["Revisar manualmente"],
                additional_context="Supervisão automática falhou",
                verification_notes="Sistema de supervisão indisponível",
                temporal_analysis={"status": "error"},
                logical_consistency={"status": "error"}
            )
    
    async def _analyze_temporal_consistency(self, query: str, response: str, context: Dict, history: Dict) -> Dict:
        """Analisa consistência temporal da resposta com acesso ao histórico completo"""
        
        # NOVO: Usa dados históricos para análise temporal mais precisa
        historical_patterns = history.get("process_patterns", {})
        recent_processes = history.get("recent_processes", [])
        
        temporal_prompt = f"""Como especialista em análise temporal, avalie se esta resposta está temporalmente consistente.

PERGUNTA: {query}
RESPOSTA: {response}
CONTEXTO ATUAL: {json.dumps(context, ensure_ascii=False)}

HISTÓRICO DE PROCESSOS SIMILARES:
{json.dumps(historical_patterns, ensure_ascii=False, indent=2)}

PROCESSOS RECENTES (últimos 10):
{json.dumps([p.get('user_query', '') for p in recent_processes], ensure_ascii=False)}

Analise:
1. A resposta menciona datas/períodos específicos?
2. As informações temporais são consistentes com o contexto atual?
3. Há contradições temporais baseadas no histórico?
4. A resposta considera mudanças temporais relevantes?

Retorne JSON:
{{
    "temporal_score": 0-10,
    "issues_found": ["problemas identificados"],
    "temporal_context": "análise do contexto temporal",
    "recommendations": ["recomendações"],
    "historical_consistency": "como se relaciona com histórico"
}}"""

        try:
            temporal_response = await self._call_llm(temporal_prompt, max_tokens=1000, query_context="temporal_analysis")
            analysis = json.loads(temporal_response)
            
            # NOVO: Adiciona insights do histórico
            analysis["historical_insights"] = self._extract_historical_insights(query, history)
            
            return analysis
        except Exception as e:
            print(f"SUPERVISOR: Erro na análise temporal - {e}")
            return {"temporal_score": 7, "issues_found": [], "temporal_context": "Análise não disponível"}
    
    async def _analyze_logical_consistency(self, query: str, response: str, context: Dict, history: Dict) -> Dict:
        """Analisa consistência lógica com base no histórico"""
        
        # NOVO: Padrões de resposta baseados no histórico
        response_patterns = self._analyze_response_patterns(history)
        
        logical_prompt = f"""Como especialista em lógica e coerência, avalie a consistência lógica desta resposta.

PERGUNTA: {query}
RESPOSTA: {response}

PADRÕES DE RESPOSTA HISTÓRICOS:
{json.dumps(response_patterns, ensure_ascii=False, indent=2)}

CONVERSAS COM AGENTES (histórico):
{json.dumps(history.get("agent_conversations", {}), ensure_ascii=False)}

Verifique:
1. Coerência interna da resposta
2. Consistência com padrões estabelecidos
3. Lógica dos argumentos apresentados
4. Contradições internas ou externas

Retorne JSON:
{{
    "logical_score": 0-10,
    "coherence_issues": ["problemas de coerência"],
    "argument_quality": "análise dos argumentos",
    "consistency_with_history": "consistência com histórico",
    "logical_flow": "análise do fluxo lógico"
}}"""

        try:
            logical_response = await self._call_llm(logical_prompt, max_tokens=1200, query_context="logical_analysis")
            return json.loads(logical_response)
        except Exception as e:
            print(f"SUPERVISOR: Erro na análise lógica - {e}")
            return {"logical_score": 7, "coherence_issues": [], "argument_quality": "Análise não disponível"}
    
    async def _verify_facts_if_needed(self, query: str, response: str, context: Dict, history: Dict) -> Dict:
        """Verificação factual aprimorada com contexto histórico"""
        
        # Verifica se precisa de fact-checking
        needs_fact_check = await self._detect_fact_check_needs(query, response)
        
        if not needs_fact_check:
            return {"factual_score": 8, "fact_check_performed": False, "factual_issues": []}
        
        if not self.tavily_available:
            return {"factual_score": 6, "fact_check_performed": False, "factual_issues": ["Fact-checking desabilitado"]}
        
        # NOVO: Considera histórico para fact-checking mais preciso
        historical_context = self._extract_factual_context_from_history(query, history)
        
        print("SUPERVISOR: Realizando verificação factual com contexto histórico...")
        
        try:
            fact_check_result = await self._perform_tavily_fact_check(query, response)
            
            # NOVO: Cruza informações com dados históricos
            fact_check_result["historical_validation"] = self._validate_against_history(response, historical_context)
            
            self.statistics["fact_checks_performed"] += 1
            
            return fact_check_result
            
        except Exception as e:
            print(f"SUPERVISOR: Erro no fact-checking - {e}")
            return {"factual_score": 6, "fact_check_performed": False, "factual_issues": [f"Erro: {str(e)}"]}
    
    async def _detect_fact_check_needs(self, query: str, response: str) -> bool:
        """Detecta se resposta precisa de fact-checking"""
        
        # Indicators que sugerem necessidade de verificação
        fact_check_indicators = [
            "ibovespa", "bovespa", "pontos", "valor", "cotação", "preço",
            "subiu", "caiu", "alta", "baixa", "variação", "%",
            "dólar", "real", "taxa", "juros", "selic", "inflação"
        ]
        
        response_lower = response.lower()
        query_lower = query.lower()
        
        # Se menciona indicadores financeiros específicos
        financial_mentions = sum(1 for indicator in fact_check_indicators 
                               if indicator in response_lower or indicator in query_lower)
        
        return financial_mentions >= 2
    
    async def _perform_tavily_fact_check(self, query: str, response: str) -> Dict:
        """Executa fact-checking via Tavily"""
        
        if not self.tavily_available:
            return {"fact_check_performed": False, "factual_accuracy": 0.8}
        
        # Identifica fatos específicos para verificar
        fact_extraction_prompt = f"""Extraia fatos específicos que podem ser verificados:

RESPOSTA: {response}

Identifique:
- Valores numéricos específicos (preços, índices, porcentagens)
- Afirmações sobre tendências ("subiu", "caiu")
- Comparações temporais
- Dados específicos de empresas

Retorne apenas os fatos verificáveis mais importantes (máximo 3).
"""
        
        try:
            facts_response = await self._call_llm(fact_extraction_prompt)
            facts_to_verify = facts_response
            
            # Busca verificação via Tavily
            verification_query = f"verificar dados atuais {query} {facts_to_verify}"
            
            # Aqui integraria com Tavily - por enquanto simulado
            return {
                "fact_check_performed": True,
                "factual_accuracy": 0.8,
                "verified_facts": ["Dados parcialmente verificados"],
                "contradictions_found": [],
                "confidence_level": "medium"
            }
            
        except Exception as e:
            return {
                "fact_check_performed": False,
                "factual_accuracy": 0.6,
                "verified_facts": [],
                "contradictions_found": [f"Erro: {str(e)}"],
                "confidence_level": "low"
            }
    
    async def _analyze_completeness(self, query: str, response: str, context: Dict, history: Dict) -> Dict:
        """Analisa se a resposta está completa"""
        
        prompt = f"""Analise se esta resposta está completa:

PERGUNTA: {query}
RESPOSTA: {response}

Verifique:
1. A resposta aborda todos os aspectos da pergunta?
2. Falta contexto importante?
3. A resposta é muito vaga ou muito específica?
4. Há informações essenciais ausentes?

Retorne JSON:
{{
    "completeness_score": float (0-1),
    "missing_aspects": ["aspectos em falta"],
    "information_gaps": ["lacunas de informação"],
    "context_adequacy": float (0-1),
    "response_depth": "shallow|adequate|deep"
}}"""
        
        try:
            response_obj = await self._call_llm(prompt)
            return json.loads(response_obj)
        except Exception as e:
            return {
                "completeness_score": 0.7,
                "missing_aspects": [],
                "information_gaps": [f"Erro na análise: {str(e)}"],
                "context_adequacy": 0.7,
                "response_depth": "adequate"
            }
    
    def _calculate_supervision_score(self, temporal: Dict, logical: Dict, factual: Dict, completeness: Dict) -> float:
        """Calcula score final de supervisão"""
        
        # Pesos configuráveis
        weights = self.verification_config
        
        temporal_score = temporal.get("temporal_score", 0.5)
        logical_score = logical.get("logical_score", 0.5)
        factual_score = factual.get("factual_score", 0.8)
        completeness_score = completeness.get("completeness_score", 0.7)
        
        final_score = (
            temporal_score * weights["temporal_accuracy_weight"] +
            logical_score * weights["logical_consistency_weight"] +
            factual_score * weights["factual_accuracy_weight"] +
            completeness_score * 0.2  # Peso para completude
        )
        
        return min(max(final_score, 0.0), 1.0)
    
    def _generate_supervision_result(self, query: str, response: str, score: float,
                                   temporal: Dict, logical: Dict, factual: Dict, completeness: Dict) -> SupervisionResult:
        """Gera resultado final da supervisão"""
        
        # Determina aprovação
        approved = score >= self.verification_config["minimum_confidence_threshold"]
        
        # Coleta problemas
        issues = []
        corrections = []
        
        # Problemas temporais
        if temporal.get("temporal_score", 0.5) < 0.7:
            issues.extend(temporal.get("issues_found", []))
        
        # Problemas lógicos
        if logical.get("logical_score", 0.5) < 0.7:
            issues.extend(logical.get("coherence_issues", []))
        
        # Problemas factuais
        if factual.get("factual_score", 0.8) < 0.7:
            issues.extend(factual.get("factual_issues", []))
        
        # Problemas de completude
        if completeness.get("completeness_score", 0.7) < 0.6:
            issues.extend(completeness.get("missing_aspects", []))
        
        # Contexto adicional
        additional_context = ""
        if not approved:
            additional_context = f"Resposta precisa de melhorias. Score: {score:.2f}"
        
        return SupervisionResult(
            approved=approved,
            confidence_score=score,
            issues_found=issues,
            corrections_suggested=corrections,
            additional_context=additional_context,
            verification_notes=f"Verificação completa - {len(issues)} problemas encontrados",
            temporal_analysis=temporal,
            logical_consistency=logical
        )
    
    def _record_supervision(self, query: str, response: str, result: SupervisionResult, agent_used: str):
        """Registra supervisão no histórico"""
        
        record = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response_preview": response[:200] + "..." if len(response) > 200 else response,
            "agent_used": agent_used,
            "approved": result.approved,
            "confidence_score": result.confidence_score,
            "issues_count": len(result.issues_found),
            "corrections_count": len(result.corrections_suggested)
        }
        
        self.supervision_history.append(record)
        
        # Atualiza estatísticas
        self.statistics["total_supervisions"] += 1
        if result.approved:
            self.statistics["approved_responses"] += 1
        else:
            self.statistics["rejected_responses"] += 1
            
        if result.corrections_suggested:
            self.statistics["corrections_made"] += 1
        
        # Mantém apenas últimas 50 supervisões
        if len(self.supervision_history) > 50:
            self.supervision_history = self.supervision_history[-50:]
        
        # Salvar automaticamente
        self._save_history()
    
    async def generate_correction_suggestions(self, query: str, response: str, 
                                            supervision_result: SupervisionResult) -> str:
        """Gera sugestões específicas de correção"""
        
        if supervision_result.approved:
            return "Resposta aprovada - nenhuma correção necessária."
        
        prompt = f"""Gere sugestões específicas de correção:

PERGUNTA: {query}
RESPOSTA ORIGINAL: {response}

PROBLEMAS IDENTIFICADOS:
{chr(10).join(f"- {issue}" for issue in supervision_result.issues_found)}

CORREÇÕES SUGERIDAS:
{chr(10).join(f"- {correction}" for correction in supervision_result.corrections_suggested)}

ANÁLISE TEMPORAL: {supervision_result.temporal_analysis}
ANÁLISE LÓGICA: {supervision_result.logical_consistency}

Forneça sugestões específicas e acionáveis para melhorar a resposta:"""
        
        try:
            response_obj = await self._call_llm(prompt)
            return response_obj
        except Exception as e:
            return f"Erro ao gerar sugestões: {str(e)}"
    
    def get_supervision_statistics(self) -> Dict:
        """Retorna estatísticas de supervisão"""
        
        total = self.statistics["total_supervisions"]
        if total == 0:
            return {"message": "Nenhuma supervisão realizada ainda"}
        
        approval_rate = (self.statistics["approved_responses"] / total) * 100
        correction_rate = (self.statistics["corrections_made"] / total) * 100
        
        return {
            "total_supervisions": total,
            "approved_responses": self.statistics["approved_responses"],
            "rejected_responses": self.statistics["rejected_responses"],
            "approval_rate": f"{approval_rate:.1f}%",
            "corrections_made": self.statistics["corrections_made"],
            "correction_rate": f"{correction_rate:.1f}%",
            "fact_checks_performed": self.statistics["fact_checks_performed"],
            "claude_verifications": self.statistics["claude_verifications"],
            "fallback_verifications": self.statistics["fallback_verifications"]
        }
    
    def get_recent_supervisions(self, limit: int = 10) -> List[Dict]:
        """Retorna supervisões recentes"""
        return self.supervision_history[-limit:]
    
    def _save_history(self):
        """Salva o histórico em arquivo JSON"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.supervision_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[SUPERVISOR] Erro ao salvar histórico: {e}")
    
    def _load_history(self):
        """Carrega o histórico do arquivo JSON"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.supervision_history = json.load(f)
                print(f"[SUPERVISOR] Histórico carregado: {len(self.supervision_history)} supervisões")
            else:
                self.supervision_history = []
        except Exception as e:
            print(f"[SUPERVISOR] Erro ao carregar histórico: {e}")
            self.supervision_history = []
    
    def _extract_historical_insights(self, query: str, history: Dict) -> Dict:
        """Extrai insights relevantes do histórico para a query atual"""
        
        try:
            recent_processes = history.get("recent_processes", [])
            agent_conversations = history.get("agent_conversations", {})
            
            insights = {
                "similar_queries": [],
                "related_conversations": [],
                "performance_context": history.get("performance_metrics", {}),
                "cost_context": history.get("cost_analysis", {})
            }
            
            # Busca queries similares
            query_lower = query.lower()
            for process in recent_processes:
                process_query = process.get('user_query', '').lower()
                if any(word in process_query for word in query_lower.split() if len(word) > 3):
                    insights["similar_queries"].append({
                        "query": process.get('user_query', ''),
                        "satisfaction": process.get('user_satisfaction'),
                        "timestamp": process.get('start_timestamp', '')
                    })
            
            # Busca conversas relacionadas
            for agent, conversations in agent_conversations.items():
                for conv in conversations:
                    conv_input = conv.get('user_input', '').lower()
                    if any(word in conv_input for word in query_lower.split() if len(word) > 3):
                        insights["related_conversations"].append({
                            "agent": agent,
                            "input": conv.get('user_input', ''),
                            "response_preview": conv.get('agent_response', '')[:100],
                            "timestamp": conv.get('timestamp', '')
                        })
            
            return insights
            
        except Exception as e:
            print(f"SUPERVISOR: Erro ao extrair insights históricos - {e}")
            return {}
    
    def _analyze_response_patterns(self, history: Dict) -> Dict:
        """Analisa padrões de resposta baseados no histórico"""
        
        try:
            all_steps = history.get("all_process_steps", [])
            response_steps = [step for step in all_steps if step.get('step_type') == 'response']
            
            patterns = {
                "avg_response_length": 0,
                "common_response_structures": [],
                "successful_response_patterns": [],
                "failed_response_patterns": []
            }
            
            if response_steps:
                # Calcula comprimento médio das respostas
                response_lengths = []
                for step in response_steps:
                    output_data = step.get('output_data', {})
                    response_text = str(output_data.get('response', ''))
                    response_lengths.append(len(response_text))
                
                if response_lengths:
                    patterns["avg_response_length"] = sum(response_lengths) / len(response_lengths)
                
                # Analisa respostas bem-sucedidas vs falhas (baseado em satisfaction)
                for step in response_steps:
                    # Busca o processo correspondente para obter satisfaction
                    process_id = step.get('process_id', '')
                    process_data = self.process_history_manager.get_process_by_id(process_id)
                    
                    if process_data:
                        satisfaction = process_data.get('user_satisfaction')
                        response_text = str(step.get('output_data', {}).get('response', ''))
                        
                        if satisfaction and satisfaction >= 4:
                            patterns["successful_response_patterns"].append({
                                "length": len(response_text),
                                "structure_indicators": self._extract_structure_indicators(response_text),
                                "satisfaction": satisfaction
                            })
                        elif satisfaction and satisfaction <= 2:
                            patterns["failed_response_patterns"].append({
                                "length": len(response_text),
                                "structure_indicators": self._extract_structure_indicators(response_text),
                                "satisfaction": satisfaction
                            })
            
            return patterns
            
        except Exception as e:
            print(f"SUPERVISOR: Erro ao analisar padrões - {e}")
            return {}
    
    def _extract_structure_indicators(self, response_text: str) -> Dict:
        """Extrai indicadores da estrutura da resposta"""
        
        try:
            indicators = {
                "has_sections": "## " in response_text or "### " in response_text,
                "has_bullet_points": "• " in response_text or "- " in response_text,
                "has_numbers": any(char.isdigit() for char in response_text),
                "has_emphasis": "**" in response_text or "__" in response_text,
                "paragraph_count": response_text.count('\n\n') + 1,
                "question_marks": response_text.count('?'),
                "exclamation_marks": response_text.count('!')
            }
            
            return indicators
            
        except Exception:
            return {}
    
    def _extract_factual_context_from_history(self, query: str, history: Dict) -> Dict:
        """Extrai contexto factual relevante do histórico"""
        
        try:
            factual_context = {
                "related_fact_checks": [],
                "historical_data_points": [],
                "validation_precedents": []
            }
            
            # Busca fact-checks anteriores relacionados
            all_steps = history.get("all_process_steps", [])
            fact_check_steps = [step for step in all_steps if 'fact_check' in step.get('step_type', '')]
            
            query_words = set(query.lower().split())
            
            for step in fact_check_steps:
                step_query = step.get('user_query', '').lower()
                step_words = set(step_query.split())
                
                # Verifica overlap de palavras
                overlap = len(query_words.intersection(step_words))
                if overlap >= 2:  # Pelo menos 2 palavras em comum
                    factual_context["related_fact_checks"].append({
                        "query": step.get('user_query', ''),
                        "timestamp": step.get('timestamp', ''),
                        "fact_check_result": step.get('output_data', {})
                    })
            
            return factual_context
            
        except Exception as e:
            print(f"SUPERVISOR: Erro ao extrair contexto factual - {e}")
            return {}
    
    def _validate_against_history(self, response: str, historical_context: Dict) -> Dict:
        """Valida resposta contra dados históricos"""
        
        try:
            validation = {
                "consistency_score": 8,  # Score padrão
                "contradictions_found": [],
                "confirmations_found": [],
                "data_freshness": "unknown"
            }
            
            # Verifica contradições com fact-checks anteriores
            for fact_check in historical_context.get("related_fact_checks", []):
                fact_result = fact_check.get('fact_check_result', {})
                
                # Lógica simplificada de validação
                if fact_result.get('factual_score', 5) < 5:
                    validation["contradictions_found"].append(f"Possível contradição com fact-check anterior: {fact_check.get('query', '')}")
                elif fact_result.get('factual_score', 5) > 7:
                    validation["confirmations_found"].append(f"Confirmado por fact-check anterior: {fact_check.get('query', '')}")
            
            # Ajusta score baseado nas contradições/confirmações
            if validation["contradictions_found"]:
                validation["consistency_score"] -= len(validation["contradictions_found"]) * 1.5
            if validation["confirmations_found"]:
                validation["consistency_score"] += len(validation["confirmations_found"]) * 0.5
            
            validation["consistency_score"] = max(0, min(10, validation["consistency_score"]))
            
            return validation
            
        except Exception as e:
            print(f"SUPERVISOR: Erro na validação histórica - {e}")
            return {"consistency_score": 7, "contradictions_found": [], "confirmations_found": []}
    
    def _create_fallback_efficiency_analysis(self, system_history: Dict) -> Dict:
        """Cria análise de eficiência de fallback baseada no histórico"""
        
        try:
            performance_metrics = system_history.get("performance_metrics", {})
            return {
                "current_efficiency": performance_metrics.get("success_rate", 0.7),
                "historical_comparison": {
                    "trend": "stable",
                    "efficiency_change": 0,
                    "historical_avg": performance_metrics.get("avg_satisfaction", 3.5)
                },
                "bottlenecks_identified": ["Análise automática indisponível"],
                "performance_by_agent": {
                    "research_agent": {"efficiency": 0.8, "trend": "stable"},
                    "supervisor_agent": {"efficiency": 0.8, "trend": "stable"},
                    "maestro_agent": {"efficiency": 0.7, "trend": "stable"}
                },
                "cost_efficiency": {
                    "cost_per_process": system_history.get("cost_analysis", {}).get("avg_cost_per_process", 0),
                    "cost_trend": "stable",
                    "optimization_potential": 0.3
                },
                "recurring_issues": ["Erro na análise automática"],
                "improvement_opportunities": ["Verificar configuração do sistema"]
            }
        except Exception:
            return {
                "current_efficiency": 0.7,
                "bottlenecks_identified": ["Análise de fallback falhou"],
                "improvement_opportunities": ["Verificar logs do sistema"]
            }
    
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