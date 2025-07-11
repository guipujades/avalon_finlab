import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from llama_index.llms.openai import OpenAI
import statistics
from dataclasses import dataclass

@dataclass
class ResponseGuidance:
    """Orientações do Maestro para melhorar a resposta"""
    focus_points: List[str]      # O que focar na resposta
    avoid_points: List[str]      # O que evitar
    include_elements: List[str]  # Elementos que devem ser incluídos
    tone_suggestion: str         # Tom sugerido
    confidence_level: float = 0.8  # Confiança nas orientações (0-1) - com valor padrão
    reasoning: str = ""         # Por que essas orientações - com valor padrão

class MaestroAgent:
    """
    Maestro Agent - Controlador de Qualidade e Parametros Dinamicos
    
    Responsabilidades:
    1. Controle de qualidade das respostas
    2. Coleta e analise de feedback do usuario
    3. Ajuste dinamico de parametros do sistema
    4. Aprendizado continuo para melhorar performance
    5. Coordenacao entre agentes para otimizacao
    """
    
    def __init__(self, llm: OpenAI):
        self.llm = llm
        self.parameters_file = "maestro_parameters.json"
        self.feedback_file = "maestro_feedback.json"
        self.learning_file = "maestro_learning.json"
        
        # Parametros do sistema (valores iniciais)
        self.system_parameters = {
            "orchestrator": {
                "cache_expiry_hours": 2,
                "simple_query_confidence": 0.8,
                "context_relevance_threshold": 0.7,
                "memory_priority_threshold": 0.75
            },
            "research_agent": {
                "web_search_depth": "basic",
                "max_results": 5,
                "relevance_threshold": 0.5,
                "confidence_threshold": 0.6,
                "synthesis_detail_level": "moderate"
            },
            "document_agent": {
                "similarity_threshold": 0.7,
                "max_documents_analyzed": 5,
                "content_extraction_depth": "moderate",
                "entity_recognition_sensitivity": 0.6
            },
            "llm_settings": {
                "temperature": 0.7,
                "model_preference": "gpt-4o-mini",
                "max_tokens": 2000,
                "response_style": "informative"
            }
        }
        
        # Historico de feedback e aprendizado
        self.feedback_history = []
        self.learning_metrics = {
            "response_quality_scores": [],
            "parameter_adjustments": [],
            "user_satisfaction_trends": [],
            "agent_performance": {
                "orchestrator": {"avg_response_time": 0, "success_rate": 1.0},
                "research_agent": {"avg_response_time": 0, "success_rate": 1.0},
                "document_agent": {"avg_response_time": 0, "success_rate": 1.0}
            }
        }
        
        # Base de conhecimento do Maestro
        self.feedback_database = {
            "successful_responses": [],      # Respostas que funcionaram bem
            "failed_responses": [],          # Respostas que não funcionaram
            "user_preferences": {},          # Padrões de preferência do usuário
            "query_patterns": {},            # Padrões de tipos de pergunta
            "improvement_insights": []       # Insights de melhoria aprendidos
        }
        
        # Estatísticas de aprendizado
        self.learning_stats = {
            "total_consultations": 0,
            "guidance_applied": 0,
            "improvement_trend": 0.0,
            "last_updated": datetime.now().isoformat()
        }
        
        self.load_saved_data()
        self.load_feedback_database()
    
    def load_saved_data(self):
        """Carrega dados salvos de parametros, feedback e aprendizado"""
        # Carrega parametros
        if os.path.exists(self.parameters_file):
            try:
                with open(self.parameters_file, 'r', encoding='utf-8') as f:
                    saved_params = json.load(f)
                    self.system_parameters.update(saved_params)
            except Exception as e:
                print(f"Erro ao carregar parametros: {e}")
        
        # Carrega feedback
        if os.path.exists(self.feedback_file):
            try:
                with open(self.feedback_file, 'r', encoding='utf-8') as f:
                    self.feedback_history = json.load(f)
            except Exception as e:
                print(f"Erro ao carregar feedback: {e}")
        
        # Carrega metricas de aprendizado
        if os.path.exists(self.learning_file):
            try:
                with open(self.learning_file, 'r', encoding='utf-8') as f:
                    saved_learning = json.load(f)
                    self.learning_metrics.update(saved_learning)
            except Exception as e:
                print(f"Erro ao carregar metricas: {e}")
    
    def save_data(self):
        """Salva todos os dados do Maestro"""
        try:
            with open(self.parameters_file, 'w', encoding='utf-8') as f:
                json.dump(self.system_parameters, f, ensure_ascii=False, indent=2)
            
            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                json.dump(self.feedback_history, f, ensure_ascii=False, indent=2)
            
            with open(self.learning_file, 'w', encoding='utf-8') as f:
                json.dump(self.learning_metrics, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erro ao salvar dados do Maestro: {e}")
    
    async def evaluate_response_quality(self, 
                                      query: str, 
                                      response: str, 
                                      agent_used: str, 
                                      context: Dict) -> Dict:
        """Avalia a qualidade da resposta usando IA"""
        
        evaluation_prompt = f"""Avalie a qualidade desta resposta como um especialista em sistemas de informacao.

PERGUNTA ORIGINAL: {query}

RESPOSTA FORNECIDA: {response}

AGENTE UTILIZADO: {agent_used}
CONTEXTO: {json.dumps(context, ensure_ascii=False)}

Avalie nos seguintes criterios (0-10):
1. RELEVANCIA: A resposta atende diretamente a pergunta?
2. COMPLETUDE: A resposta e suficientemente detalhada?
3. PRECISAO: As informacoes parecem corretas e confiaveis?
4. CLAREZA: A resposta e facil de entender?
5. UTILIDADE: A resposta e acionavel/util para o usuario?

Retorne um JSON com:
{{
    "scores": {{
        "relevancia": 0-10,
        "completude": 0-10,
        "precisao": 0-10,
        "clareza": 0-10,
        "utilidade": 0-10
    }},
    "score_geral": 0-10,
    "pontos_fortes": ["aspectos positivos"],
    "pontos_fracos": ["aspectos a melhorar"],
    "sugestoes_melhoria": ["sugestoes especificas"],
    "parametros_recomendados": {{
        "temperature": 0.1-1.0,
        "search_depth": "basic/advanced",
        "max_results": 3-15,
        "outros": "sugestoes de parametros"
    }}
}}"""
        
        try:
            response_eval = await self.llm.acomplete(evaluation_prompt)
            evaluation = json.loads(response_eval.text)
            
            # Adiciona timestamp e contexto
            evaluation["timestamp"] = datetime.now().isoformat()
            evaluation["agent_used"] = agent_used
            evaluation["query_type"] = context.get("intent_analysis", {}).get("action_required", "unknown")
            
            return evaluation
        except Exception as e:
            print(f"Erro na avaliacao automatica: {e}")
            return {
                "scores": {"relevancia": 5, "completude": 5, "precisao": 5, "clareza": 5, "utilidade": 5},
                "score_geral": 5,
                "pontos_fortes": ["Resposta fornecida"],
                "pontos_fracos": ["Avaliacao automatica falhou"],
                "sugestoes_melhoria": ["Verificar sistema de avaliacao"],
                "parametros_recomendados": {}
            }
    
    async def collect_response_feedback(self, query: str, response: str, agent_type: str, 
                                      user_satisfaction: int, user_comments: str = "") -> Dict:
        """Coleta feedback simplificado para aprendizado de prioridades"""
        
        feedback_data = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response": response,
            "agent_type": agent_type,
            "user_satisfaction": user_satisfaction,
            "user_comments": user_comments
        }
        
        # Adiciona ao histórico para análise de padrões
        self.feedback_history.append(feedback_data)
        
        # Mantém apenas últimos 20 feedbacks para performance
        if len(self.feedback_history) > 20:
            self.feedback_history = self.feedback_history[-20:]
        
        # NOVO: Analisa padrões automaticamente a cada 3 feedbacks
        if len(self.feedback_history) >= 3 and len(self.feedback_history) % 3 == 0:
            print("MAESTRO: Analisando padrões de feedback para atualizar prioridades...")
            try:
                await self.analyze_feedback_patterns_and_priorities()
            except Exception as e:
                print(f"MAESTRO: Erro na análise automática: {e}")
                print(f"MAESTRO: Continuando operação normalmente...")
        
        # Salva dados
        try:
            self.save_feedback_database()
        except Exception as e:
            print(f"MAESTRO: Erro ao salvar dados: {e}")
        
        print(f"MAESTRO: Feedback coletado para {agent_type} - {user_satisfaction}/5 - '{user_comments[:50]}...'")
        
        return feedback_data
    
    async def suggest_parameter_adjustments(self, feedback: Dict) -> Dict:
        """Sugere ajustes de parametros baseado no feedback"""
        
        adjustments = {}
        combined_score = feedback['combined_score']
        auto_eval = feedback['automatic_evaluation']
        user_feedback = feedback['user_feedback']
        agent_used = auto_eval.get('agent_used', 'unknown')
        
        # Analise baseada no score
        if combined_score < 6:  # Resposta ruim
            adjustments = {
                "reason": "Baixa qualidade detectada",
                "changes": {}
            }
            
            # Ajustes especificos por agente
            if agent_used == "research_agent":
                if auto_eval['scores']['completude'] < 6:
                    adjustments["changes"]["max_results"] = min(15, self.system_parameters["research_agent"]["max_results"] + 2)
                    adjustments["changes"]["web_search_depth"] = "advanced"
                
                if auto_eval['scores']['precisao'] < 6:
                    adjustments["changes"]["relevance_threshold"] = max(0.3, self.system_parameters["research_agent"]["relevance_threshold"] - 0.1)
            
            elif agent_used == "document_agent":
                if auto_eval['scores']['completude'] < 6:
                    adjustments["changes"]["max_documents_analyzed"] = min(10, self.system_parameters["document_agent"]["max_documents_analyzed"] + 1)
                
                if auto_eval['scores']['precisao'] < 6:
                    adjustments["changes"]["similarity_threshold"] = max(0.5, self.system_parameters["document_agent"]["similarity_threshold"] - 0.1)
            
            # Ajustes de LLM
            if auto_eval['scores']['clareza'] < 6:
                adjustments["changes"]["temperature"] = max(0.3, self.system_parameters["llm_settings"]["temperature"] - 0.1)
        
        elif combined_score > 8:  # Resposta muito boa
            adjustments = {
                "reason": "Alta qualidade - otimizando eficiencia",
                "changes": {}
            }
            
            # Pode reduzir alguns parametros para eficiencia
            if agent_used == "research_agent" and auto_eval['scores']['completude'] > 8:
                current_results = self.system_parameters["research_agent"]["max_results"]
                if current_results > 3:
                    adjustments["changes"]["max_results"] = current_results - 1
        
        return adjustments
    
    def apply_parameter_adjustments(self, adjustments: Dict):
        """Aplica os ajustes de parametros sugeridos"""
        if not adjustments.get("changes"):
            return
        
        changes_applied = []
        
        for param_name, new_value in adjustments["changes"].items():
            # Encontra onde aplicar o parametro
            applied = False
            
            for section_name, section_params in self.system_parameters.items():
                if param_name in section_params:
                    old_value = section_params[param_name]
                    section_params[param_name] = new_value
                    changes_applied.append(f"{section_name}.{param_name}: {old_value} → {new_value}")
                    applied = True
                    break
            
            if not applied:
                print(f"Parametro nao encontrado: {param_name}")
        
        if changes_applied:
            print(f"\nAJUSTES APLICADOS:")
            for change in changes_applied:
                print(f"   • {change}")
            
            # Registra os ajustes
            self.learning_metrics["parameter_adjustments"].append({
                "timestamp": datetime.now().isoformat(),
                "reason": adjustments.get("reason", "Ajuste manual"),
                "changes": adjustments["changes"]
            })
        
        self.save_data()
    
    async def maestro_interaction(self, 
                                query: str, 
                                response: str, 
                                agent_used: str, 
                                context: Dict,
                                auto_mode: bool = False) -> Dict:
        """Interacao principal do Maestro apos uma resposta"""
        
        # Avaliacao automatica
        evaluation = await self.evaluate_response_quality(query, response, agent_used, context)
        
        if auto_mode:
            # Modo automatico - apenas registra dados
            feedback = {
                "timestamp": datetime.now().isoformat(),
                "automatic_evaluation": evaluation,
                "user_feedback": {"satisfaction": 4, "usefulness": 4, "comments": "Auto mode"},
                "combined_score": evaluation['score_geral']
            }
            self.feedback_history.append(feedback)
        else:
            # Modo interativo - coleta feedback do usuario
            feedback = await self.collect_response_feedback(query, response, agent_used, evaluation['score_geral'], evaluation['suggestions'])
        
        # Sugere ajustes de parametros
        adjustments = await self.suggest_parameter_adjustments(feedback)
        
        if not auto_mode and adjustments.get("changes"):
            print(f"\nSUGESTOES DE AJUSTES:")
            print(f"   Motivo: {adjustments['reason']}")
            for param, value in adjustments["changes"].items():
                print(f"   • {param} → {value}")
            
            apply_changes = input("\n   Aplicar ajustes? (s/n): ").strip().lower()
            if apply_changes in ['s', 'sim', 'y', 'yes']:
                self.apply_parameter_adjustments(adjustments)
            else:
                print("   Ajustes nao aplicados.")
        elif adjustments.get("changes"):
            # Modo automatico - aplica automaticamente ajustes pequenos
            if feedback['combined_score'] < 5:  # So ajusta se muito ruim
                self.apply_parameter_adjustments(adjustments)
        
        # Atualiza metricas de aprendizado
        self.learning_metrics["response_quality_scores"].append({
            "timestamp": datetime.now().isoformat(),
            "score": feedback['combined_score'],
            "agent_used": agent_used
        })
        
        # Salva dados
        self.save_data()
        
        return feedback
    
    def get_current_parameters(self, agent_name: str = None) -> Dict:
        """Retorna parametros atuais do sistema"""
        if agent_name:
            return self.system_parameters.get(agent_name, {})
        return self.system_parameters
    
    def get_performance_summary(self) -> Dict:
        """Retorna resumo de performance do sistema"""
        if not self.learning_metrics["response_quality_scores"]:
            return {
                "total_interactions": 0,
                "average_quality_score": 0,
                "recent_average": 0,
                "improvement_trend": "N/A",
                "best_performing_agent": "N/A",
                "total_parameter_adjustments": 0
            }
        
        scores = [s["score"] for s in self.learning_metrics["response_quality_scores"]]
        recent_scores = scores[-10:] if len(scores) >= 10 else scores
        
        return {
            "total_interactions": len(scores),
            "average_quality_score": statistics.mean(scores),
            "recent_average": statistics.mean(recent_scores),
            "improvement_trend": "Melhorando" if len(scores) > 5 and statistics.mean(recent_scores) > statistics.mean(scores[:-5]) else "Estavel",
            "best_performing_agent": self._get_best_agent(),
            "total_parameter_adjustments": len(self.learning_metrics["parameter_adjustments"])
        }
    
    def _get_best_agent(self) -> str:
        """Identifica o agente com melhor performance"""
        agent_scores = {}
        
        for score_data in self.learning_metrics["response_quality_scores"]:
            agent = score_data["agent_used"]
            if agent not in agent_scores:
                agent_scores[agent] = []
            agent_scores[agent].append(score_data["score"])
        
        if not agent_scores:
            return "N/A"
        
        best_agent = max(agent_scores.keys(), key=lambda x: statistics.mean(agent_scores[x]))
        return best_agent
    
    def reset_learning_data(self):
        """Reseta todos os dados de aprendizado"""
        confirmation = input("ATENCAO: Isso apagara todo o historico de aprendizado. Confirma? (digite 'RESET'): ")
        
        if confirmation == "RESET":
            self.feedback_history = []
            self.learning_metrics = {
                "response_quality_scores": [],
                "parameter_adjustments": [],
                "user_satisfaction_trends": [],
                "agent_performance": {
                    "orchestrator": {"avg_response_time": 0, "success_rate": 1.0},
                    "research_agent": {"avg_response_time": 0, "success_rate": 1.0},
                    "document_agent": {"avg_response_time": 0, "success_rate": 1.0}
                }
            }
            
            # Remove arquivos salvos
            for file in [self.feedback_file, self.learning_file]:
                if os.path.exists(file):
                    os.remove(file)
            
            print("Dados de aprendizado resetados.")
        else:
            print("Reset cancelado.") 
    
    async def get_response_guidance(self, query: str, agent_type: str, context: Dict = None) -> ResponseGuidance:
        """Gera orientações inteligentes baseadas em prioridades aprendidas"""
        
        # NOVO: Atualiza prioridades se há feedback suficiente
        if len(self.feedback_history) >= 3:
            try:
                await self.analyze_feedback_patterns_and_priorities()
            except Exception as e:
                print(f"MAESTRO: Erro ao atualizar prioridades: {e}")
        
        # Obtém prioridades atuais e preferências do usuário
        current_priorities = self.get_current_priorities()
        user_preferences = self.get_user_preferences()
        
        guidance_prompt = f"""Gere orientações inteligentes para responder esta consulta usando as prioridades aprendidas.

CONSULTA: {query}
AGENTE: {agent_type}
CONTEXTO: {json.dumps(context, ensure_ascii=False) if context else "Nenhum"}

PRIORIDADES APRENDIDAS:
{json.dumps(current_priorities, ensure_ascii=False, indent=2)}

PREFERÊNCIAS DO USUÁRIO:
{json.dumps(user_preferences, ensure_ascii=False, indent=2)}

Baseado no aprendizado, retorne um JSON com:
{{
    "focus_points": [
        "pontos principais com base nas prioridades aprendidas"
    ],
    "avoid_points": [
        "o que evitar baseado no feedback anterior"
    ],
    "include_elements": [
        "elementos que o usuário valoriza"
    ],
    "tone_suggestion": "formal/informal/technical",
    "reasoning": "por que estas orientações foram escolhidas"
}}

APLIQUE AS PRIORIDADES DE FORMA INTELIGENTE para esta consulta específica."""

        try:
            response = await self.llm.acomplete(guidance_prompt)
            guidance_data = json.loads(response.text)
            
            # NOVO: Aplica prioridades automaticamente baseadas nas preferências
            if user_preferences.get("prefers_brazilian_content") and "mercado" in query.lower():
                if not any("brasil" in focus.lower() for focus in guidance_data.get("focus_points", [])):
                    guidance_data["focus_points"].append("Incluir informações específicas do mercado brasileiro (Ibovespa, B3)")
                    print("MAESTRO: Prioridade brasileira aplicada automaticamente")
            
            if user_preferences.get("prefers_quantitative_data"):
                if not any("dados" in focus.lower() for focus in guidance_data.get("focus_points", [])):
                    guidance_data["focus_points"].append("Incluir dados numéricos e quantitativos específicos")
                    print("MAESTRO: Prioridade de dados quantitativos aplicada")
            
            guidance = ResponseGuidance(
                focus_points=guidance_data.get("focus_points", []),
                avoid_points=guidance_data.get("avoid_points", []),
                include_elements=guidance_data.get("include_elements", []),
                tone_suggestion=guidance_data.get("tone_suggestion", "informativo"),
                confidence_level=0.8,
                reasoning=guidance_data.get("reasoning", "Orientações baseadas em prioridades aprendidas")
            )
            
            print(f"MAESTRO → {agent_type.upper()}: Orientações com prioridades inteligentes geradas")
            if current_priorities:
                print(f"  Aplicando {len(current_priorities)} prioridades aprendidas")
            
            return guidance
            
        except Exception as e:
            print(f"MAESTRO: Erro ao gerar orientações: {e}")
            # Fallback com prioridades mínimas
            return ResponseGuidance(
                focus_points=["Responder de forma clara e informativa"],
                avoid_points=["Respostas vagas ou genéricas"],
                include_elements=["Informações relevantes e atuais"],
                tone_suggestion="informativo",
                confidence_level=0.5,
                reasoning=f"Fallback devido a erro: {e}"
            )
    
    def get_learning_summary(self) -> Dict:
        """Retorna resumo do aprendizado do Maestro"""
        total_feedback = len(self.feedback_database["successful_responses"]) + len(self.feedback_database["failed_responses"])
        success_rate = len(self.feedback_database["successful_responses"]) / max(total_feedback, 1)
        
        return {
            "total_consultations": self.learning_stats["total_consultations"],
            "total_feedback_collected": total_feedback,
            "success_rate": success_rate,
            "successful_responses": len(self.feedback_database["successful_responses"]),
            "failed_responses": len(self.feedback_database["failed_responses"]),
            "improvement_insights": len(self.feedback_database["improvement_insights"]),
            "user_preferences_learned": len(self.feedback_database["user_preferences"]),
            "last_updated": self.learning_stats["last_updated"]
        }
    
    def load_feedback_database(self):
        """Carrega base de feedback do disco"""
        try:
            if os.path.exists("maestro_feedback_database.json"):
                with open("maestro_feedback_database.json", 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
                    self.feedback_database.update(saved_data)
                print("MAESTRO: Base de feedback carregada do disco")
        except Exception as e:
            print(f"MAESTRO: Erro ao carregar base de feedback ({e})")
    
    def save_feedback_database(self):
        """Salva base de feedback no disco"""
        try:
            self.learning_stats["last_updated"] = datetime.now().isoformat()
            
            # Salva base de feedback
            with open("maestro_feedback_database.json", 'w', encoding='utf-8') as f:
                json.dump(self.feedback_database, f, ensure_ascii=False, indent=2)
            
            # Salva estatísticas de aprendizado
            with open("maestro_learning_stats.json", 'w', encoding='utf-8') as f:
                json.dump(self.learning_stats, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"MAESTRO: Erro ao salvar base de feedback ({e})")
    
    def reset_learning_data(self):
        """Reset completo dos dados de aprendizado"""
        self.feedback_database = {
            "successful_responses": [],
            "failed_responses": [],
            "user_preferences": {},
            "query_patterns": {},
            "improvement_insights": []
        }
        
        self.learning_stats = {
            "total_consultations": 0,
            "guidance_applied": 0,
            "improvement_trend": 0.0,
            "last_updated": datetime.now().isoformat()
        }
        
        self.save_feedback_database()
        print("MAESTRO: Dados de aprendizado resetados")
    
    async def analyze_feedback_patterns_and_priorities(self) -> Dict:
        """Analisa padrões de feedback e estabelece prioridades inteligentes para respostas"""
        
        if len(self.feedback_history) < 2:
            return {"priorities": [], "reasoning": "Feedback insuficiente para análise de padrões"}
        
        # Analisa comentários dos últimos feedbacks
        recent_feedback = self.feedback_history[-10:]  # Últimos 10 feedbacks
        
        # CORRIGIDO: Garante que todos os campos existam
        safe_feedback = []
        for f in recent_feedback:
            safe_entry = {
                "query": f.get("query", "")[:50],
                "score": f.get("user_satisfaction", 3),
                "comments": f.get("user_comments", "")
            }
            safe_feedback.append(safe_entry)
        
        feedback_analysis_prompt = f"""Analise estes feedbacks do usuário e identifique prioridades inteligentes para melhorar futuras respostas.

HISTÓRICO DE FEEDBACK:
{json.dumps(safe_feedback, ensure_ascii=False, indent=2)}

Baseado nos padrões de feedback, retorne um JSON com:
{{
    "identified_patterns": [
        "padrões identificados nos comentários"
    ],
    "response_priorities": [
        {{
            "priority": "nome da prioridade",
            "description": "descrição clara",
            "trigger_conditions": ["quando aplicar"],
            "implementation": "como implementar na prática",
            "confidence": 0.0-1.0
        }}
    ],
    "user_preferences": {{
        "prefers_brazilian_content": true/false,
        "prefers_quantitative_data": true/false,
        "prefers_multiple_sources": true/false,
        "prefers_detailed_context": true/false
    }},
    "improvement_suggestions": [
        "sugestões gerais para melhorar respostas"
    ]
}}

FOQUE EM PADRÕES GERAIS, não em correções específicas pontuais."""

        try:
            response = await self.llm.acomplete(feedback_analysis_prompt)
            analysis = json.loads(response.text)
            
            # Salva as prioridades identificadas
            self.response_priorities = analysis.get("response_priorities", [])
            self.user_preferences = analysis.get("user_preferences", {})
            
            print(f"MAESTRO: Padrões identificados e prioridades atualizadas")
            print(f"  {len(self.response_priorities)} prioridades de resposta estabelecidas")
            
            return analysis
            
        except Exception as e:
            print(f"MAESTRO: Erro na análise de padrões: {e}")
            return {"priorities": [], "reasoning": f"Erro na análise: {e}"}
    
    def get_current_priorities(self) -> List[Dict]:
        """Retorna as prioridades atuais baseadas no aprendizado"""
        if not hasattr(self, 'response_priorities'):
            self.response_priorities = []
        return self.response_priorities
    
    def get_user_preferences(self) -> Dict:
        """Retorna as preferências do usuário identificadas"""
        if not hasattr(self, 'user_preferences'):
            self.user_preferences = {}
        return self.user_preferences
    
    async def direct_conversation(self, user_input: str) -> str:
        """Conversa direta com o usuário (modo de conversa)"""
        try:
            response = await self._call_llm(
                f"Responda como Maestro Agent em conversa direta com o arquiteto do sistema. Pergunta: {user_input}",
                max_tokens=1500,
                query_context="direct_conversation"
            )
            return response
        except Exception as e:
            return f"Erro na conversa com Maestro: {e}"
    
    async def direct_conversation_with_context(self, user_input: str, conversation_context: str = "") -> str:
        """Conversa direta com o usuário incluindo contexto de memória curta"""
        try:
            # Monta prompt com contexto se disponível
            if conversation_context:
                full_prompt = f"""Você é o Maestro Agent em conversa direta com o arquiteto do sistema.

Seu papel como MAESTRO:
- Análise de performance e otimização
- Gerenciamento de parâmetros de sistema
- Coleta e análise de feedback
- Sugestões de melhorias

{conversation_context}

NOVA PERGUNTA DO ARQUITETO: {user_input}

Responda mantendo consistência com o contexto da conversa anterior."""
            else:
                full_prompt = f"Responda como Maestro Agent em conversa direta com o arquiteto do sistema. Pergunta: {user_input}"
            
            response = await self._call_llm(
                full_prompt,
                max_tokens=1500,
                query_context="direct_conversation_with_memory"
            )
            return response
        except Exception as e:
            return f"Erro na conversa com Maestro: {e}"
    
    def _calculate_average_quality(self) -> float:
        """Calcula qualidade média baseada no feedback"""
        if not self.feedback_history:
            return 7.5  # Valor padrão
        
        scores = [feedback.get('combined_score', 5) for feedback in self.feedback_history]
        return sum(scores) / len(scores)
    
    def _analyze_improvement_trend(self) -> str:
        """Analisa tendência de melhoria do sistema"""
        if len(self.feedback_history) < 5:
            return "Dados insuficientes"
        
        recent_scores = [feedback.get('combined_score', 5) for feedback in self.feedback_history[-5:]]
        older_scores = [feedback.get('combined_score', 5) for feedback in self.feedback_history[-10:-5]]
        
        if not older_scores:
            return "Em avaliação"
        
        recent_avg = sum(recent_scores) / len(recent_scores)
        older_avg = sum(older_scores) / len(older_scores)
        
        if recent_avg > older_avg + 0.5:
            return "Melhorando significativamente"
        elif recent_avg > older_avg:
            return "Melhorando gradualmente"
        elif recent_avg < older_avg - 0.5:
            return "Degradando"
        else:
            return "Estável" 