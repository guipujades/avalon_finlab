import os
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
from dotenv import load_dotenv
from llama_index.llms.openai import OpenAI
from collections import defaultdict

# Importa configurações
from config import get_config, SYSTEM_CONFIG, validate_and_fix_model_config

# NOVO: Import do cost tracker
from cost_tracker import cost_tracker

# NOVO: Import do sistema de histórico completo
from process_history import process_history_manager

# ===== ORCHESTRATOR - COORDENADOR INTELIGENTE =====
class IntelligentOrchestrator:
    """Orchestrator inteligente que coordena todos os agentes e interface"""
    
    def __init__(self, openai_key: str, tavily_key: str, maestro_enabled: bool = True, admin_mode: bool = True):
        self.openai_key = openai_key
        self.tavily_key = tavily_key
        self.llm = None
        self.document_agent = None
        self.research_agent = None
        self.maestro_agent = None  # Novo agente Maestro
        self.supervisor_agent = None  # Agente Supervisor
        self.meta_auditor_agent = None  # Meta-Auditor com Gemini
        self.data_science_agent = None  # NOVO: Agente de Data Science
        
        # NOVO: Sistema de modos
        self.admin_mode = admin_mode  # True = Modo Admin, False = Modo Usuário
        self.agent_conversation_manager = None  # Sistema de conversas com agentes
        
        # NOVO: Sistema de histórico completo
        self.process_history_manager = process_history_manager
        
        # Carrega configuração do sistema
        self.config = get_config()
        self.llm_config = SYSTEM_CONFIG["llm"]
        self.model_selection = SYSTEM_CONFIG["model_selection"]
        
        # Memória compartilhada
        self.shared_memory = {
            "recent_queries": [],
            "cached_responses": {},
            "user_preferences": {},
            "session_context": {}
        }
        
        # Configurações de decisão (serão controladas pelo Maestro)
        self.decision_thresholds = {
            "simple_query_confidence": 0.8,
            "cache_expiry_hours": 2,
            "context_relevance_threshold": 0.7
        }
        
        # Controle de modo Maestro
        self.maestro_enabled = maestro_enabled  # NOVO: Parâmetro configurável
        self.auto_maestro_mode = False  # Se True, Maestro roda em modo automático
        
        # NOVO: Controle do Supervisor
        self.supervisor_enabled = True  # Supervisor ativo por padrão
        
        # NOVO: Controle do Meta-Auditor
        self.meta_auditor_enabled = True  # Meta-Auditor ativo por padrão
        
        # NOVO: Estatísticas de uso do maestro
        self.maestro_stats = {
            "commands_skipped": 0,
            "research_queries": 0,
            "total_interactions": 0
        }
        
        # NOVO: Controle de primeira interação
        self.first_interaction = True
        self.skip_first_maestro = False  # Configurável para pular maestro no primeiro feedback
        
        # NOVO: Comandos que não precisam do maestro (operações simples)
        self.no_maestro_commands = {
            # Comandos de sistema diretos
            'scan', 'processar', 'processar_novos', 'docs', 'status',
            'stats', 'memoria', 'info_memoria', 'decisions',
            'limpar_curta', 'clear_short', 'limpar_longa', 'clear_long',
            'reset_total', 'clear_all', 'help', 'clear', 'stats_maestro',
            # NOVO: Comandos para controlar maestro
            'maestro_off', 'maestro_on', 'toggle_maestro', 'disable_maestro', 'enable_maestro',
            # NOVO: Comandos para controlar supervisor
            'supervisor_off', 'supervisor_on', 'toggle_supervisor', 'stats_supervisor',
            # NOVO: Comandos para controlar provedores de busca
            'provider_tavily', 'provider_perplexity', 'provider_status', 'providers',
            'tavily', 'perplexity', 'web_provider',
            # Variações comuns
            'statistics', 'memory', 'documento', 'documentos',
            'escanear', 'process', 'process_new'
        }
        
        # Comandos de sistema por categoria
        self.system_commands = {
            'document_management': {
                'scan', 'processar', 'processar_novos', 'docs', 'status',
                'escanear', 'process', 'process_new', 'documentos'
            },
            'system_stats': {
                'stats', 'memoria', 'info_memoria', 'memory_info', 'decisions',
                'statistics', 'memory'
            },
            'memory_management': {
                'limpar_curta', 'clear_short', 'limpar_longa', 'clear_long',
                'reset_total', 'clear_all'
            },
            'help_commands': {
                'help', 'clear'
            }
        }
        
        # Toggle de agentes
        self.maestro_enabled = maestro_enabled
        self.supervisor_enabled = True  # Supervisor sempre ativo
        # Meta-Auditor agora apenas observa e registra dados
        
        # Cached responses para evitar reconsultas
        self.response_cache = {}
        
    async def initialize(self):
        """Inicializa todos os componentes"""
        from document_agent import EnhancedDocumentAgent
        from research_agent import IntelligentResearchAgent
        from maestro_agent import MaestroAgent
        from supervisor_agent import SupervisorAgent  # Import do Supervisor
        from meta_auditor_agent import MetaAuditorAgent  # Import do Meta-Auditor
        from data_science_agent import DataScienceAgent  # NOVO: Import do Data Science Agent
        from agent_conversations import AgentConversationManager  # NOVO: Import do sistema de conversas
        from config import validate_and_fix_model_config
        
        print("ORCHESTRATOR: Inicializando sistema...")
        
        # NOVO: Valida e corrige configurações de modelo ANTES de criar LLMs
        try:
            # Aplicar validação na configuração LLM principal
            temp_config = {"system": {"llm": self.llm_config}}
            validated_config = validate_and_fix_model_config(temp_config)
            self.llm_config = validated_config["system"]["llm"]
            
            # Aplicar validação nas configurações especializadas
            validated_model_selection = {}
            for operation_type, config in self.model_selection.items():
                temp_config = {"system": {"model_selection": {operation_type: config}}}
                validated_config = validate_and_fix_model_config(temp_config)
                validated_model_selection[operation_type] = validated_config["system"]["model_selection"][operation_type]
            self.model_selection = validated_model_selection
            
        except Exception as e:
            print(f"ORCHESTRATOR: Erro na validação de modelos - {e}")
            print("ORCHESTRATOR: Usando configuração estável como fallback")
            from config import get_stable_config
            stable_config = get_stable_config()
            self.llm_config = stable_config["system"]["llm"]
            self.model_selection = stable_config["system"]["model_selection"]
        
        # LLM principal usando a melhor configuração
        self.llm = OpenAI(
            model=self.llm_config["model"],  # gpt-4o (melhor modelo)
            temperature=self.llm_config["temperature"],
            max_tokens=self.llm_config["max_tokens"],
            api_key=self.openai_key
        )
        
        # Cria LLMs especializados para diferentes operações
        self.llm_models = {
            "main": self.llm,
            "fast": OpenAI(
                model=self.llm_config["fast_model"],
                temperature=self.model_selection["simple_commands"]["temperature"],
                max_tokens=self.model_selection["simple_commands"]["max_tokens"],
                api_key=self.openai_key
            ),
            "analysis": OpenAI(
                model=self.model_selection["complex_analysis"]["model"],
                temperature=self.model_selection["complex_analysis"]["temperature"],
                max_tokens=self.model_selection["complex_analysis"]["max_tokens"],
                api_key=self.openai_key
            ),
            "research": OpenAI(
                model=self.model_selection["research_synthesis"]["model"],
                temperature=self.model_selection["research_synthesis"]["temperature"],
                max_tokens=self.model_selection["research_synthesis"]["max_tokens"],
                api_key=self.openai_key
            )
        }
        
        # Maestro Agent (primeiro para controlar os parâmetros)
        self.maestro_agent = MaestroAgent(self.llm)
        
        # NOVO: Supervisor Agent 
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.supervisor_agent = SupervisorAgent(
            anthropic_key=anthropic_key,
            tavily_key=self.tavily_key,
            fallback_llm=self.llm  # OpenAI como fallback
        )
        
        # NOVO: Meta-Auditor Agent with Gemini
        gemini_key = os.getenv("GEMINI_API_KEY")
        self.meta_auditor_agent = MetaAuditorAgent(gemini_key=gemini_key)
        
        # NOVO: Data Science Agent 
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.data_science_agent = DataScienceAgent(anthropic_key=anthropic_key)
        
        # Atualiza parâmetros dos outros agentes baseado no que o Maestro aprendeu
        maestro_params = self.maestro_agent.get_current_parameters()
        if "llm_settings" in maestro_params:
            llm_settings = maestro_params["llm_settings"]
            # Só aplica se o modelo suporta temperature diferente
            model_name = self.llm_config["model"]
            if not any(restricted_model in model_name for restricted_model in ["o1", "o3"]):
                self.llm.temperature = llm_settings.get("temperature", self.llm_config["temperature"])
        
        # Document Agent
        self.document_agent = EnhancedDocumentAgent(self.llm)
        
        # NOVO: Research Agent com suporte a múltiplos provedores
        # Detecta provedores de busca disponíveis
        perplexity_key = os.getenv("PERPLEXITY_API_KEY")
        
        self.research_agent = IntelligentResearchAgent(
            self.llm, 
            self.document_agent, 
            tavily_key=self.tavily_key,
            perplexity_key=perplexity_key
        )
        
        # NOVO: Conecta Maestro ao Research Agent
        self.research_agent.set_maestro_agent(self.maestro_agent)
        
        # NOVO: Conecta Data Science Agent ao Research Agent
        self.research_agent.set_data_science_agent(self.data_science_agent)
        
        self.load_shared_memory()
        
        # NOVO: Inicializa sistema de conversas com agentes (apenas em modo admin)
        if self.admin_mode:
            self.agent_conversation_manager = AgentConversationManager(self)
        
        print("ORCHESTRATOR: Sistema inicializado com sucesso!")
        
        # NOVO: Exibe modo de operação
        mode_description = "ADMIN (acesso completo)" if self.admin_mode else "USUÁRIO (consultas apenas)"
        print(f"MODO DE OPERAÇÃO: {mode_description}")
        print(f"PIPELINE ATIVO: Research → Data Science → Supervisor → Maestro")
        print(f"HISTÓRICO COMPLETO: Ativo para aprendizado dos agentes")
    
    def load_shared_memory(self):
        """Carrega memória compartilhada de arquivo"""
        memory_file = "shared_memory.json"
        if os.path.exists(memory_file):
            try:
                with open(memory_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        self.shared_memory.update(json.loads(content))
            except Exception:
                pass
    
    def save_shared_memory(self):
        """Salva memória compartilhada"""
        memory_file = "shared_memory.json"
        with open(memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.shared_memory, f, ensure_ascii=False, indent=2)
    
    def display_interaction_menu(self) -> str:
        """Exibe menu interativo baseado no modo (Admin/Usuário)"""
        
        # Estatísticas do sistema
        stats = self.get_system_statistics()
        
        print("="*70)
        if self.admin_mode:
            print("SISTEMA MULTI-AGENTE INTELIGENTE - MODO ADMINISTRADOR")
        else:
            print("SISTEMA MULTI-AGENTE INTELIGENTE - MODO USUÁRIO")
        print("="*70)
        
        print("STATUS DO SISTEMA:")
        print(f"   Documentos na base: {stats['documents_in_base']}")
        print(f"   Consultas na sessão: {stats['session_queries']}")
        print(f"   Respostas em cache: {stats['cached_responses']}")
        
        if self.admin_mode:
            # Menu completo para administrador
            print("\n" + "="*70)
            print("MENU DE INTERACAO - MODO ADMINISTRADOR")
            print("="*70)
            
            print("\n1. PERGUNTA/PESQUISA")
            print("   • Qualquer tipo de pergunta ou pesquisa")
            print("   • Sistema decide automaticamente a melhor estratégia")
            
            print("\n2. CONSULTA DOCUMENTOS")
            print("   • Busca específica na base de conhecimento local")
            
            print("\n3. GERENCIAR SISTEMA")
            print("   • Comandos de sistema (scan, status, stats, etc.)")
            
            print("\n4. CONVERSAS COM AGENTES")
            print("   • Conversar diretamente com Maestro, Supervisor ou Meta-Auditor")
            print("   • Acesso a insights técnicos e arquiteturais")
            
            print("\n5. CONFIGURAR MAESTRO")
            print("   • Ajustar modo de feedback")
            
            print("\n6. DESABILITAR/HABILITAR MAESTRO")
            print("   • Toggle rápido do maestro ON/OFF")
            
            maestro_status = "[ATIVO]" if self.maestro_enabled else "[INATIVO]"
            supervisor_status = "[ATIVO]" if self.supervisor_enabled else "[INATIVO]"
            meta_auditor_status = "[OBSERVAÇÃO]"  # Meta-Auditor sempre em modo observação
            print(f"\nSTATUS MAESTRO: {maestro_status}")
            print(f"STATUS SUPERVISOR: {supervisor_status}")
            print(f"STATUS META-AUDITOR: {meta_auditor_status}")
            print("="*70)
        
            while True:
                try:
                    choice = input("Escolha uma opção (1-6): ").strip()
                    if choice in ['1', '2', '3', '4', '5', '6']:
                        return choice
                    else:
                        print("Por favor, digite um número de 1 a 6")
                except KeyboardInterrupt:
                    print("\n\nSistema interrompido pelo usuário.")
                    return "exit"
                except:
                    print("Por favor, digite um número de 1 a 6")
        
        else:
            # Menu simplificado para usuário
            print("\n" + "="*70)
            print("MENU DE INTERACAO - MODO USUÁRIO")
            print("="*70)
            
            print("\n1. FAZER PERGUNTA")
            print("   • Digite sua pergunta sobre qualquer assunto")
            print("   • Sistema busca informações e fornece resposta completa")
            
            print("\n2. CONSULTAR DOCUMENTOS")
            print("   • Busca específica na base de conhecimento")
            
            print("\n" + "="*70)
            print("MODO USUÁRIO: Interface simplificada para consultas")
            print("="*70)
            
            while True:
                try:
                    choice = input("Escolha uma opção (1-2): ").strip()
                    if choice in ['1', '2']:
                        return choice
                    else:
                        print("Por favor, digite um número de 1 a 2")
                except KeyboardInterrupt:
                    print("\n\nSistema interrompido pelo usuário.")
                    return "exit"
                except:
                    print("Por favor, digite um número de 1 a 2")
    
    async def handle_user_choice(self, choice: str) -> Optional[Tuple[str, str, Dict]]:
        """Processa a escolha do usuário e retorna (query, response, context)"""
        
        if choice == "1":
            # Pergunta/Pesquisa - sistema decide automaticamente
            query = input("\nDigite sua pergunta/pesquisa: ").strip()
            if not query:
                return None
            
            # NOVO: Inicia rastreamento do processo completo
            process_id = self.process_history_manager.start_new_process(query, self.admin_mode)
            
            print(f"\nProcessando: '{query}'")
            
            # Registra início da análise de intenção
            step_start = datetime.now()
            intent = await self.analyze_user_intent(query)
            step_end = datetime.now()
            
            self.process_history_manager.add_process_step(
                step_type="intent_analysis",
                agent="orchestrator",
                input_data={"query": query},
                output_data={"intent": intent},
                execution_time=(step_end - step_start).total_seconds(),
                metadata={"admin_mode": self.admin_mode}
            )
            
            # Usa pipeline completo com Meta-Auditor
            supervised_response, full_context = await self.process_with_full_pipeline(
                query, {"intent_analysis": intent}, "auto_system"
            )
            
            # Combina contextos
            final_context = {
                "intent_analysis": intent, 
                "interaction_type": "auto_query",
                "pipeline": full_context,
                "process_id": process_id
            }
            
            return query, supervised_response, final_context
        
        elif choice == "2":
            # Consulta documentos
            query = input("\nDigite sua consulta sobre documentos: ").strip()
            if not query:
                return None
            
            # NOVO: Inicia rastreamento do processo
            process_id = self.process_history_manager.start_new_process(query, self.admin_mode)
            
            print(f"\nConsultando base de documentos: '{query}'")
            
            forced_intent = {
                "intent_type": "question",
                "action_required": "document_management",
                "complexity": "moderate",
                "requires_web": False,
                "requires_documents": True,
                "can_answer_from_memory": False,
                "confidence": 0.9,
                "suggested_response_type": "direct",
                "key_entities": [],
                "reasoning": "Consulta documentos forçada pelo usuário"
            }
            
            # Registra intent forçado
            self.process_history_manager.add_process_step(
                step_type="intent_analysis",
                agent="orchestrator",
                input_data={"query": query},
                output_data={"intent": forced_intent},
                execution_time=0.0,
                metadata={"forced_intent": True}
            )
            
            # Registra processamento da consulta
            step_start = datetime.now()
            response = await self.delegate_to_document_agent(query, forced_intent)
            step_end = datetime.now()
            
            self.process_history_manager.add_process_step(
                step_type="document_query",
                agent="document_agent",
                input_data={"query": query, "intent": forced_intent},
                output_data={"response": response},
                execution_time=(step_end - step_start).total_seconds()
            )
            
            context = {
                "intent_analysis": forced_intent, 
                "interaction_type": "document_query", 
                "agent_used": "document_agent",
                "process_id": process_id
            }
            
            return query, response, context
        
        # Opções apenas disponíveis no modo Admin
        elif self.admin_mode and choice == "3":
            # Gerenciar sistema
            print("\nCOMANDOS DE SISTEMA DISPONIVEIS:")
            print()
            print("DOCUMENTOS:")
            print("'scan' - Escanear novos documentos")
            print("'processar' - Reprocessar TODOS os documentos")
            print("'processar_novos' - Processar apenas novos/modificados")
            print("'docs' - Listar documentos disponíveis")
            print()
            print("ESTATISTICAS:")
            print("'stats' - Estatisticas detalhadas do sistema")
            print("'memoria' - Status basico da memoria")
            print("'info_memoria' - Informacoes detalhadas das memorias")
            print("'decisions' - Historico de decisoes do Research Agent")
            print()
            print("CUSTOS:")
            print("'costs' - Custos da sessão atual")
            print("'cost_report' - Relatório detalhado de custos")
            print("'pricing' - Tabela de preços das APIs")
            print()
            print("GERENCIAR MEMORIA:")
            print("'limpar_curta' - Limpar memoria de curto prazo (sessao)")
            print("'limpar_longa' - Limpar memoria de longo prazo (historico)")
            print("'reset_total' - RESET TOTAL do sistema (CUIDADO!)")
            print()
            print("'help' - Mostrar todos os comandos")
            
            command = input("\nDigite o comando: ").strip()
            if not command:
                return None
            
            response = await self.handle_system_command(command)
            
            return command, response, {"interaction_type": "system_command", "agent_used": "orchestrator"}
        
        elif self.admin_mode and choice == "4":
            # NOVO: Conversas com agentes
            if not self.agent_conversation_manager:
                return "error", "Sistema de conversas não inicializado", {"error": True}
            
            conversation_choice = self.agent_conversation_manager.display_agent_conversation_menu()
            
            if conversation_choice and conversation_choice != "0":
                await self.agent_conversation_manager.handle_agent_conversation_choice(conversation_choice)
            
            return "conversations", "Conversas com agentes concluídas", {"interaction_type": "agent_conversations"}
        
        elif self.admin_mode and choice == "5":
            # Configurar Maestro (era opção 4)
            return await self.handle_maestro_configuration()
        
        elif self.admin_mode and choice == "6":
            # Desabilitar/Habilitar Maestro (era opção 5)
            self.maestro_enabled = not self.maestro_enabled
            status = "ATIVADO" if self.maestro_enabled else "DESATIVADO"
            response = f"Modo automático do Maestro: {status}"
            
            return f"maestro_config_{choice}", response, {"interaction_type": "maestro_config", "agent_used": "maestro"}
        
        # Se não é modo admin e tentou acessar opção restrita
        elif not self.admin_mode and choice in ["3", "4", "5", "6"]:
            return "error", "Esta opção está disponível apenas no Modo Administrador", {"error": True}
        
        return None
    
    async def handle_maestro_configuration(self) -> Optional[Tuple[str, str, Dict]]:
        """Configurações do Maestro"""
        print("\nCONFIGURACOES DO MAESTRO")
        print("="*40)
        print("1. Alternar modo automatico")
        print("2. Ver performance do sistema")
        print("3. Ver parametros atuais")
        print("4. Resetar dados de aprendizado")
        print("5. Voltar")
        
        choice = input("\nEscolha (1-5): ").strip()
        
        if choice == "1":
            self.auto_maestro_mode = not self.auto_maestro_mode
            status = "ATIVADO" if self.auto_maestro_mode else "DESATIVADO"
            response = f"Modo automatico do Maestro: {status}"
            
        elif choice == "2":
            performance = self.maestro_agent.get_performance_summary()
            response = f"""PERFORMANCE DO SISTEMA:
   Total de interacoes: {performance.get('total_interactions', 0)}
   Score medio de qualidade: {performance.get('average_quality_score', 0):.2f}/10
   Score recente: {performance.get('recent_average', 0):.2f}/10
   Tendencia: {performance.get('improvement_trend', 'N/A')}
   Melhor agente: {performance.get('best_performing_agent', 'N/A')}
   Ajustes realizados: {performance.get('total_parameter_adjustments', 0)}"""
            
        elif choice == "3":
            params = self.maestro_agent.get_current_parameters()
            response = f"PARAMETROS ATUAIS:\n{json.dumps(params, ensure_ascii=False, indent=2)}"
            
        elif choice == "4":
            self.maestro_agent.reset_learning_data()
            response = "Dados de aprendizado do Maestro foram resetados."
            
        else:
            return None
        
        return f"maestro_config_{choice}", response, {"interaction_type": "maestro_config", "agent_used": "maestro"}
    
    async def process_user_input_internal(self, user_input: str, intent: Dict) -> str:
        """Versão interna do processamento sem Maestro"""
        
        # CORRIGIDO: Validação robusta do intent
        if not intent or not isinstance(intent, dict):
            print("INTERNAL: Intent inválido, usando fallback")
            intent = self._fallback_intent_analysis(user_input)
        
        # Garante que todas as chaves necessárias existem
        required_keys = ["action_required", "requires_web", "requires_documents", "can_answer_from_memory"]
        for key in required_keys:
            if key not in intent:
                print(f"INTERNAL: Chave '{key}' ausente no intent, regenerando...")
                intent = self._fallback_intent_analysis(user_input)
                break
        
        try:
            # Verifica cache
            memory_response = await self.check_memory_for_answer(user_input, intent)
            if memory_response:
                print("Respondendo da memória...")
                return memory_response
            
            # Processa baseado na intenção
            action_required = intent.get("action_required", "research")
            
            if action_required == "system_info":
                response = await self.handle_system_command(user_input)
            elif action_required == "document_management":
                response = await self.delegate_to_document_agent(user_input, intent)
            elif action_required == "research":
                response = await self.delegate_to_research(user_input, intent)
            elif action_required == "hybrid":
                doc_response = await self.delegate_to_document_agent(user_input, intent)
                if "não foi possível" in doc_response.lower() or len(doc_response) < 50:
                    print("Complementando com pesquisa web...")
                    web_response = await self.delegate_to_research(user_input, intent)
                    response = f"{doc_response}\n\nInformações adicionais da web:\n{web_response}"
                else:
                    response = doc_response
            else:
                # Fallback para research
                print(f"INTERNAL: Action '{action_required}' desconhecida, usando research")
                response = await self.delegate_to_research(user_input, intent)
            
            return response
                
        except Exception as e:
            print(f"INTERNAL: Erro no processamento - {e}")
            # Fallback: tenta pesquisa simples
            try:
                return await self.delegate_to_research(user_input, intent)
            except Exception as e2:
                return f"Erro no processamento da consulta: {str(e)}\nFallback também falhou: {str(e2)}"
    
    async def analyze_user_intent(self, user_input: str) -> Dict:
        """Analisa a intenção do usuário usando LLM"""
        try:
            # NOVO: Verifica primeiro se é comando simples
            if self.is_simple_command(user_input):
                return {
                    "intent_type": "command",
                    "action_required": "system_info",
                    "complexity": "simple",
                    "requires_web": False,
                    "requires_documents": False,
                    "can_answer_from_memory": True,
                    "confidence": 0.95,
                    "suggested_response_type": "direct",
                    "key_entities": [],
                    "reasoning": "Comando simples identificado - não requer maestro",
                    "skip_maestro": True
                }
            
            prompt = f"""Analise esta consulta do usuário e retorne um JSON com a análise da intenção:

Consulta: "{user_input}"

Retorne um JSON com:
- intent_type: "question" | "command" | "conversation"
- action_required: "research" | "document_management" | "system_info" | "hybrid"
- complexity: "simple" | "moderate" | "complex"
- requires_web: boolean (precisa de informações da web?)
- requires_documents: boolean (precisa consultar documentos locais?)
- can_answer_from_memory: boolean (pode ser respondido da memória?)
- confidence: number (0-1, confiança na análise)
- suggested_response_type: "direct" | "delegated" | "hybrid"
- key_entities: array (empresas, índices, conceitos mencionados)
- reasoning: string (explicação da análise)
- skip_maestro: boolean (se é comando simples que não precisa de avaliação)

Comandos simples que devem ter skip_maestro=true: scan, docs, stats, memoria, help, clear, decisions, etc."""

            # Usa modelo rápido para análise de intenção
            fast_llm = self.get_optimal_llm("intent_analysis")
            response = await fast_llm.acomplete(prompt)
            
            # CORRIGIDO: Melhor tratamento de JSON
            response_text = response.text.strip()
            
            # Verifica se é JSON válido
            if not response_text:
                print("INTENT: Resposta vazia do LLM")
                return self._fallback_intent_analysis(user_input)
            
            # Tenta extrair JSON se estiver em bloco de código
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                if json_end > json_start:
                    response_text = response_text[json_start:json_end].strip()
            
            # Tenta fazer parse do JSON
            try:
                result = json.loads(response_text)
            except json.JSONDecodeError as e:
                print(f"INTENT: Erro de JSON - {e}")
                print(f"INTENT: Texto recebido: {response_text[:200]}...")
                return self._fallback_intent_analysis(user_input)
            
            # Valida se tem todas as chaves necessárias
            required_keys = ["intent_type", "action_required", "complexity", "requires_web", 
                           "requires_documents", "confidence", "reasoning"]
            
            for key in required_keys:
                if key not in result:
                    print(f"INTENT: Chave '{key}' ausente, usando fallback")
                    return self._fallback_intent_analysis(user_input)
            
            # Garante que comandos simples tenham skip_maestro=true
            if result.get("intent_type") == "command" and result.get("complexity") == "simple":
                result["skip_maestro"] = True
            else:
                result["skip_maestro"] = False
            
            return result
            
        except Exception as e:
            print(f"Erro na análise de intenção: {e}")
            return self._fallback_intent_analysis(user_input)
    
    def _fallback_intent_analysis(self, user_input: str) -> Dict:
        """Análise de fallback quando LLM falha"""
        user_lower = user_input.lower()
        
        # Comandos explícitos que não precisam do maestro
        if any(cmd in user_lower for cmd in self.no_maestro_commands):
            return {
                "intent_type": "command",
                "action_required": "system_info",
                "complexity": "simple",
                "requires_web": False,
                "requires_documents": False,
                "can_answer_from_memory": True,
                "confidence": 0.9,
                "suggested_response_type": "direct",
                "key_entities": [],
                "reasoning": "Comando de sistema identificado",
                "skip_maestro": True
            }
        
        # Perguntas sobre empresas específicas
        companies = ["petrobras", "vale", "itaú", "bradesco", "ambev", "mercado", "ibovespa", "bovespa"]
        mentions_company = any(company in user_lower for company in companies)
        
        # Detecta se menciona termos financeiros
        financial_terms = ["mercado", "cotação", "preço", "ação", "índice", "bolsa", "investimento"]
        mentions_finance = any(term in user_lower for term in financial_terms)
        
        # Decide action_required baseado no conteúdo
        if mentions_company and mentions_finance:
            action_required = "hybrid"  # Busca local + web
        elif mentions_finance:
            action_required = "research"  # Principalmente web
        else:
            action_required = "research"  # Default
        
        return {
            "intent_type": "question",
            "action_required": action_required,
            "complexity": "moderate",
            "requires_web": True,
            "requires_documents": mentions_company,
            "can_answer_from_memory": False,
            "confidence": 0.6,
            "suggested_response_type": "delegated",
            "key_entities": [comp for comp in companies if comp in user_lower],
            "reasoning": "Análise de fallback - pergunta identificada",
            "skip_maestro": False
        }
    
    def is_simple_command(self, user_input: str) -> bool:
        """Verifica se é um comando simples que não precisa do maestro"""
        user_lower = user_input.lower().strip()
        
        # Comandos exatos
        if user_lower in self.no_maestro_commands:
            return True
        
        # Comandos que começam com palavras-chave
        simple_prefixes = ['scan', 'processar', 'docs', 'stats', 'memoria', 'help', 'limpar', 'clear', 'reset']
        if any(user_lower.startswith(prefix) for prefix in simple_prefixes):
            return True
        
        return False
    
    async def check_memory_for_answer(self, user_input: str, intent: Dict) -> Optional[str]:
        """Verifica se pode responder da memória"""
        if not intent.get("can_answer_from_memory"):
            return None
        
        # Verifica cache de respostas recentes
        query_hash = hash(user_input.lower().strip())
        if query_hash in self.shared_memory["cached_responses"]:
            cached = self.shared_memory["cached_responses"][query_hash]
            
            # Verifica se não expirou
            cached_time = datetime.fromisoformat(cached["timestamp"])
            if datetime.now() - cached_time < timedelta(hours=self.decision_thresholds["cache_expiry_hours"]):
                return cached["response"]
        
        return None
    
    async def _generate_simple_response(self, user_input: str, intent: Dict) -> Optional[str]:
        """Gera resposta simples para perguntas básicas"""
        
        simple_prompt = f"""Você é um assistente financeiro. Responda de forma concisa se esta for uma pergunta simples que você pode responder com conhecimento geral. Se a pergunta requer dados específicos ou atuais, retorne 'REQUIRES_RESEARCH'.

PERGUNTA: {user_input}

CONTEXTO: {intent.get('reasoning', '')}

Se puder responder, forneça uma resposta concisa. Se não, retorne exatamente 'REQUIRES_RESEARCH'."""
        
        try:
            # Usa modelo rápido para respostas simples
            fast_llm = self.get_optimal_llm("simple_command")
            response = await fast_llm.acomplete(simple_prompt)
            answer = response.text.strip()
            
            if answer == "REQUIRES_RESEARCH":
                return None
            
            return answer
        except Exception:
            return None
    
    async def handle_system_command(self, command: str) -> str:
        """Processa comandos do sistema"""
        command = command.lower().strip()
        
        if command == 'scan':
            print("ORCHESTRATOR: Executando scan de documentos...")
            scan_result = await self.document_agent.scan_documents()
            return f"""Scan completo:
   Total: {scan_result['total_documents']} documentos
   Processados: {scan_result['processed_this_scan']} novos
   Tipos: {scan_result['types']}"""
        
        elif command == 'docs':
            snapshot = await self.document_agent.get_knowledge_base_snapshot()
            result = f"""BASE DE CONHECIMENTO:
   Total: {snapshot['summary']['total_documents']} documentos
   Categorias: {list(snapshot['summary']['categories'].keys())}"""
            
            if snapshot['catalog']:
                result += "\n\nDOCUMENTOS RECENTES:"
                for doc in snapshot['catalog'][:5]:
                    result += f"\n   {doc['filename']} ({doc['type']}) - {doc['categories']}"
            
            return result
        
        elif command == 'status':
            snapshot = await self.document_agent.get_knowledge_base_snapshot()
            result = f"""STATUS DA BASE:
   Documentos: {snapshot['summary']['total_documents']}
   Categorias: {len(snapshot['summary']['categories'])}
   Entidades: {len(snapshot['entities_coverage'])}
   LlamaParse: {'Ativo' if snapshot['summary']['llama_parse_available'] else 'Inativo'}"""
            
            if snapshot['recommendations']:
                result += "\n\nRECOMENDAÇÕES:"
                for rec in snapshot['recommendations']:
                    result += f"\n   • {rec}"
            
            return result
        
        elif command == 'stats':
            stats = self.get_system_statistics()
            result = f"""ESTATÍSTICAS DETALHADAS:
   Consultas na sessão: {len(self.shared_memory['recent_queries'])}
   Respostas em cache: {len(self.shared_memory['cached_responses'])}
   Documentos na base: {stats['documents_in_base']}
   Decisões do research: {stats.get('research_decisions', 0)}"""
            
            return result
        
        elif command == 'memoria':
            memory_stats = self.get_memory_statistics()
            return f"""MEMÓRIA DO SISTEMA:
   Consultas recentes: {memory_stats['recent_queries']}
   Cache de respostas: {memory_stats['cached_responses']}
   Contexto da sessão: {memory_stats['session_items']}"""
        
        elif command in ['info_memoria', 'memory_info']:
            return self.get_memory_info()
        
        elif command in ['limpar_curta', 'clear_short']:
            return self.clear_short_term_memory()
        
        elif command in ['limpar_longa', 'clear_long']:
            return self.clear_long_term_memory()
        
        elif command in ['reset_total', 'clear_all']:
            return self.clear_all_memories()
        
        elif command == 'decisions':
            if hasattr(self.research_agent, 'decision_history') and self.research_agent.decision_history:
                result = f"HISTÓRICO DE DECISÕES ({len(self.research_agent.decision_history)} total):"
                for i, decision in enumerate(self.research_agent.decision_history[-5:], 1):
                    timestamp = decision['timestamp'][:19].replace('T', ' ')
                    strategy = decision['decision']['strategy']
                    confidence = decision['decision']['confidence']
                    result += f"\n   {i}. [{timestamp}] {strategy} (conf: {confidence:.2f})"
                return result
            else:
                return "Nenhuma decisão registrada ainda"
        
        elif command == 'stats_supervisor':
            stats = self.supervisor_agent.get_supervision_statistics()
            if "message" in stats:
                return stats["message"]
            
            return f"""ESTATÍSTICAS DO SUPERVISOR:
   Total de supervisões: {stats['total_supervisions']}
   Respostas aprovadas: {stats['approved_responses']}
   Respostas reprovadas: {stats['rejected_responses']}
   Taxa de aprovação: {stats['approval_rate']}
   Correções aplicadas: {stats['corrections_made']}
   Taxa de correção: {stats['correction_rate']}
   Verificações factuais: {stats['fact_checks_performed']}"""
        
        elif command == 'stats_meta_auditor':
            stats = self.meta_auditor_agent.get_audit_statistics()
            if "message" in stats:
                return stats["message"]
            
            return f"""ESTATÍSTICAS DO META-AUDITOR:
   Total de auditorias: {stats['total_audits']}
   Eficiência média geral: {stats['avg_efficiency']}
   Eficiência recente: {stats['recent_avg_efficiency']}
   Problemas críticos: {stats['critical_issues_found']}
   Melhorias sugeridas: {stats['improvements_suggested']}
   Status Gemini: {stats['gemini_status']}"""
        
        elif command == 'stats_data_science':
            stats = self.data_science_agent.get_usage_statistics()
            
            return f"""ESTATÍSTICAS DO DATA SCIENCE AGENT:
   Total de requisições: {stats['total_requests']}
   Requisições bem-sucedidas: {stats['successful_requests']}
   Requisições falharam: {stats['failed_requests']}
   Taxa de sucesso: {stats['success_rate']}
   APIs disponíveis: {', '.join(stats['available_apis'])}
   Claude disponível: {'✅ Sim' if stats['claude_available'] else '❌ Não'}
   Por fonte de dados: {json.dumps(stats['by_api_source'], ensure_ascii=False)}"""
        
        elif command == 'operations_data_science':
            operations = self.data_science_agent.get_available_operations()
            result = "OPERAÇÕES DISPONÍVEIS NO DATA SCIENCE AGENT:\n"
            for api_name, ops in operations.items():
                result += f"\n{api_name.upper()}:\n"
                for op in ops:
                    result += f"   • {op}\n"
            return result
        
        # NOVO: Comandos de custos
        elif command in ['costs', 'custos']:
            summary = cost_tracker.get_session_summary()
            if summary['total_cost'] == 0:
                return "Nenhum custo registrado nesta sessão."
            
            result = f"""CUSTOS DA SESSÃO ATUAL:
   Total gasto: ${summary['total_cost']:.6f} USD
   Total de chamadas: {summary['total_calls']}
   Custo médio/chamada: ${summary['total_cost']/summary['total_calls']:.6f} USD

POR PROVEDOR:"""
            
            for provider, data in summary['by_provider'].items():
                avg_cost = data['cost'] / data['calls'] if data['calls'] > 0 else 0
                result += f"""
   {provider.upper()}: ${data['cost']:.6f} ({data['calls']} calls, ~{avg_cost:.6f}/call)"""
            
            # Chamada mais cara
            if summary.get('most_expensive_call'):
                expensive = summary['most_expensive_call']
                result += f"""

CHAMADA MAIS CARA:
   {expensive.api_provider}/{expensive.model}: ${expensive.cost_usd:.6f}
   {expensive.total_tokens} | {expensive.operation}"""
            
            return result
        
        elif command in ['cost_report', 'relatorio_custos']:
            return cost_tracker.get_detailed_report()
        
        elif command in ['pricing', 'precos']:
            return cost_tracker.get_pricing_table()
        
        elif command in ['estimate_cost', 'estimar_custo']:
            sample_query = "Como está o mercado hoje?"
            estimates = cost_tracker.estimate_query_cost(len(sample_query), "medium")
            
            result = f"""ESTIMATIVA DE CUSTOS (consulta média ~{len(sample_query)} chars):

OPENAI:
   gpt-4o: ${estimates.get('openai_gpt-4o', 0):.6f} USD
   gpt-4o-mini: ${estimates.get('openai_gpt-4o-mini', 0):.6f} USD [ECONÔMICO]
   gpt-4-turbo: ${estimates.get('openai_gpt-4-turbo', 0):.6f} USD

ANTHROPIC:
   sonnet: ${estimates.get('anthropic_sonnet', 0):.6f} USD
   haiku: ${estimates.get('anthropic_haiku', 0):.6f} USD [ECONÔMICO]

GOOGLE:
   gemini-1.5-pro: ${estimates.get('google_gemini-1.5-pro', 0):.6f} USD
   gemini-1.5-flash: ${estimates.get('google_gemini-1.5-flash', 0):.6f} USD [ECONÔMICO]

BUSCA WEB:
   Tavily: ${estimates.get('tavily_search', 0):.6f} USD
   Perplexity: ${estimates.get('perplexity_search', 0):.6f} USD

ECONOMIA: Use modelos [ECONÔMICO] para reduzir custos em ~70-90%"""
            
            return result
        
        else:
            return f"Comando '{command}' não reconhecido. Digite 'help' para ver comandos disponíveis."
    
    async def delegate_to_research(self, user_input: str, intent: Dict) -> str:
        """Delega pergunta para o Research Agent"""
        print("ORCHESTRATOR → RESEARCH AGENT: Delegando consulta")
        
        # Cria contexto para o research agent
        context = {
            "user_query": user_input,
            "intent_analysis": intent,
            "session_context": self.shared_memory.get("session_context", {}),
            "recent_queries": [q['query'] for q in self.shared_memory['recent_queries'][-3:]]
        }
        
        # Chama o research agent (versão simplificada)
        result = await self.research_agent.process_query_simple(user_input, context)
        
        return result
    
    async def delegate_to_document_agent(self, user_input: str, intent: Dict) -> str:
        """Delega ação para o Document Agent"""
        print("ORCHESTRATOR → DOCUMENT AGENT: Consultando base de documentos")
        
        request = {
            "query": user_input,
            "request_id": f"orchestrator_{datetime.now().timestamp()}",
            "context": {
                "intent_analysis": intent,
                "source": "orchestr"
            }
        }
        
        try:
            response = await self.document_agent.process_intelligent_request(request)
        
            # CORRIGIDO: Verifica se response não é None
            if response is None:
                print("DOCUMENT AGENT → ORCHESTRATOR: Resposta vazia")
                return "Não foi possível processar a consulta nos documentos locais (resposta vazia)."
            
            if response.get("status") == "success":
                data = response.get("data", {})
                print("DOCUMENT AGENT → ORCHESTRATOR: Informações encontradas")
                
                # Verifica se há informação extraída
                extracted_info = data.get("extracted_information")
                if extracted_info and extracted_info.get("combined_insights"):
                    return extracted_info.get("combined_insights", "Informação processada com sucesso.")
                
                # Se não há informação extraída, tenta usar documentos encontrados
                documents = data.get("documents_found", {})
                perfect_matches = documents.get("perfect_matches", [])
                good_matches = documents.get("good_matches", [])
                
                if perfect_matches or good_matches:
                    matches = perfect_matches + good_matches
                    doc_list = []
                    for match in matches[:3]:  # Máximo 3 documentos
                        doc_list.append(f"• {match.get('filename', 'Documento')} (Score: {match.get('relevance_score', 0):.1f})")
                    
                    result = f"Documentos relevantes encontrados na base local:\n" + "\n".join(doc_list)
                    result += f"\n\nRecomendação: {data.get('recommendations', {}).get('suggested_approach', 'Buscar informações adicionais na web')}"
                    return result
                else:
                    return "Nenhum documento relevante encontrado na base local."
            
            elif response.get("status") == "error":
                error_msg = response.get("error", "Erro desconhecido")
                print(f"DOCUMENT AGENT → ORCHESTRATOR: Erro - {error_msg}")
                return f"Erro ao consultar documentos locais: {error_msg}"
            
            else:
                print("DOCUMENT AGENT → ORCHESTRATOR: Status desconhecido")
                return "Status de resposta desconhecido dos documentos locais."
                
        except Exception as e:
            print(f"DOCUMENT AGENT → ORCHESTRATOR: Exceção - {str(e)}")
            return f"Erro inesperado ao consultar documentos locais: {str(e)}"
    
    async def process_with_supervision(self, query: str, response: str, context: Dict, agent_used: str) -> Tuple[str, Dict]:
        """Processa resposta com verificação do supervisor"""
        
        if not self.supervisor_enabled:
            print("SUPERVISOR: Desabilitado - resposta aprovada sem verificação")
            return response, {"supervised": False, "approved": True}
        
        # Executa supervisão
        supervision_result = await self.supervisor_agent.supervise_response(
            query, response, context, agent_used
        )
        
        if supervision_result.approved:
            # Resposta aprovada
            return response, {
                "supervised": True, 
                "approved": True,
                "supervision_score": supervision_result.confidence_score,
                "supervision_notes": supervision_result.verification_notes
            }
        
        else:
            # Resposta reprovada - precisa de correção
            print("SUPERVISOR: Resposta reprovada - gerando correção...")
            
            # Gera sugestões de correção
            correction_suggestions = await self.supervisor_agent.generate_correction_suggestions(
                query, response, supervision_result
            )
            
            # Tenta gerar resposta corrigida
            corrected_response = await self._generate_corrected_response(
                query, response, supervision_result, correction_suggestions, context, agent_used
            )
            
            # Verifica se a correção foi bem-sucedida
            if corrected_response != response:
                print("SUPERVISOR: Resposta corrigida gerada")
                return corrected_response, {
                    "supervised": True,
                    "approved": False,
                    "corrected": True,
                    "original_issues": supervision_result.issues_found,
                    "corrections_applied": supervision_result.corrections_suggested,
                    "supervision_score": supervision_result.confidence_score
                }
            else:
                print("SUPERVISOR: Não foi possível corrigir - entregando resposta original com aviso")
                warning = f"\n\n⚠️ AVISO DO SUPERVISOR: Esta resposta pode ter problemas de coerência.\nProblemas identificados: {', '.join(supervision_result.issues_found)}"
                
                return response + warning, {
                    "supervised": True,
                    "approved": False,
                    "corrected": False,
                    "issues_found": supervision_result.issues_found,
                    "supervision_score": supervision_result.confidence_score
                }
    
    async def _generate_corrected_response(self, query: str, original_response: str, 
                                         supervision_result, correction_suggestions: str,
                                         context: Dict, agent_used: str) -> str:
        """Gera resposta corrigida baseada nas sugestões do supervisor"""
        
        correction_prompt = f"""Corrija esta resposta baseado nas sugestões do supervisor:

PERGUNTA ORIGINAL: {query}
RESPOSTA ORIGINAL: {original_response}

PROBLEMAS IDENTIFICADOS:
{chr(10).join(f"- {issue}" for issue in supervision_result.issues_found)}

SUGESTÕES DE CORREÇÃO:
{correction_suggestions}

ANÁLISE TEMPORAL: {supervision_result.temporal_analysis}
ANÁLISE LÓGICA: {supervision_result.logical_consistency}

Gere uma resposta corrigida que:
1. Mantenha o conteúdo útil da resposta original
2. Corrija os problemas identificados
3. Adicione contexto temporal específico se necessário
4. Melhore a coerência lógica
5. Seja factualmente precisa

RESPOSTA CORRIGIDA:"""
        
        try:
            # NOVO: Usa Claude através do supervisor para correção
            corrected_response = await self.supervisor_agent._call_llm(correction_prompt, max_tokens=2000)
            
            # Verifica se houve mudança significativa
            if len(corrected_response) < len(original_response) * 0.5:
                print("SUPERVISOR: Correção muito curta - mantendo original")
                return original_response
            
            return corrected_response
            
        except Exception as e:
            print(f"SUPERVISOR: Erro na correção - {str(e)}")
            return original_response

    async def execute_system_audit(self, query: str, final_response: str, 
                                supervision_context: Dict, maestro_context: Dict,
                                execution_log: List[Dict], timing_data: Dict,
                                user_satisfaction: Optional[int] = None) -> Dict:
        """Meta-Auditor agora apenas observa - dados ficam registrados no histórico para conversas futuras"""
        
        # Meta-Auditor não executa mais no fluxo, apenas registra observação
        return {
            "audit_enabled": False, 
            "message": "Meta-Auditor em modo observação - dados disponíveis para conversas individuais",
            "data_logged": True,
            "available_for_individual_analysis": True
        }
    
    async def process_with_full_pipeline(self, query: str, context: Dict, agent_used: str) -> Tuple[str, Dict]:
        """Processa consulta com pipeline completo (Research → Supervisor → Maestro)"""
        
        start_time = datetime.now()
        execution_log = []
        
        try:
            # 1. Gera resposta inicial
            execution_log.append({"step": "research_start", "timestamp": datetime.now().isoformat()})
            
            # CORRIGIDO: Verifica se o contexto tem intent_analysis válido
            intent = context.get("intent_analysis", {})
            if not intent or "action_required" not in intent:
                print("PIPELINE: Intent analysis inválido, regenerando...")
                intent = await self.analyze_user_intent(query)
                context["intent_analysis"] = intent
            
            # Registra início da pesquisa
            research_start = datetime.now()
            initial_response = await self.process_user_input_internal(query, intent)
            research_end = datetime.now()
            
            # NOVO: Registra step de pesquisa no histórico
            self.process_history_manager.add_process_step(
                step_type="research",
                agent="research_agent",
                input_data={"query": query, "intent": intent},
                output_data={"response": initial_response},
                execution_time=(research_end - research_start).total_seconds(),
                cost_data={"estimated_cost": 0.001}  # Será refinado com dados reais de custo
            )
            
            execution_log.append({"step": "research_complete", "timestamp": datetime.now().isoformat()})
            
            # 2. Supervisão com Claude
            execution_log.append({"step": "supervision_start", "timestamp": datetime.now().isoformat()})
            
            supervision_start = datetime.now()
            supervised_response, supervision_context = await self.process_with_supervision(
                query, initial_response, context, agent_used
            )
            supervision_end = datetime.now()
            
            # NOVO: Registra step de supervisão no histórico
            self.process_history_manager.add_process_step(
                step_type="supervision",
                agent="supervisor_agent",
                input_data={"query": query, "response": initial_response, "context": context},
                output_data={"supervised_response": supervised_response, "supervision_result": supervision_context},
                execution_time=(supervision_end - supervision_start).total_seconds()
            )
            
            execution_log.append({"step": "supervision_complete", "timestamp": datetime.now().isoformat()})
            
            # 3. Dados de timing para observação (Meta-Auditor registra apenas)
            end_time = datetime.now()
            timing_data = {
                "total_duration": (end_time - start_time).total_seconds(),
                "process_start": start_time.isoformat(),
                "process_end": end_time.isoformat()
            }
            
            # NOVO: Meta-Auditor apenas registra dados para análises futuras (não executa no fluxo)
            # Os dados ficam disponíveis no histórico completo para conversas individuais
            execution_log.append({"step": "meta_audit_data_logged", "timestamp": datetime.now().isoformat()})
            
            # NOVO: Registra resposta final no histórico
            final_step_start = datetime.now()
            self.process_history_manager.add_process_step(
                step_type="response",
                agent="orchestrator",
                input_data={"query": query, "pipeline_context": context},
                output_data={"response": supervised_response, "full_context": execution_log},
                execution_time=(datetime.now() - final_step_start).total_seconds(),
                metadata={"pipeline_complete": True}
            )
            
            # Retorna resposta supervisionada com dados completos
            final_context = {
                "supervision": supervision_context,
                "execution_log": execution_log,
                "timing_data": timing_data,
                "meta_audit_available": True,  # Indica que dados estão disponíveis para o Meta-Auditor
                "pipeline_simplified": True
            }
            
            return supervised_response, final_context
            
        except Exception as e:
            print(f"PIPELINE: Erro no processamento - {e}")
            # Fallback simples
            try:
                simple_response = await self.process_user_input_internal(query, context.get("intent_analysis", {}))
                return simple_response, {"error": str(e), "fallback_used": True}
            except Exception as e2:
                return f"Erro no processamento: {str(e)}\nFallback também falhou: {str(e2)}", {"error": str(e), "fallback_error": str(e2)}
    
    def get_system_statistics(self) -> Dict:
        """Retorna estatísticas do sistema"""
        stats = {
            "session_queries": len(self.shared_memory["recent_queries"]),
            "cached_responses": len(self.shared_memory["cached_responses"]),
            "documents_in_base": 0,
            "research_decisions": 0
        }
        
        if self.document_agent:
            stats["documents_in_base"] = len(self.document_agent.registry.get("documents", {}))
        
        if hasattr(self.research_agent, 'decision_history'):
            stats["research_decisions"] = len(self.research_agent.decision_history)
        
        return stats
    
    def get_memory_statistics(self) -> Dict:
        """Retorna estatísticas da memória"""
        return {
            "recent_queries": len(self.shared_memory["recent_queries"]),
            "cached_responses": len(self.shared_memory["cached_responses"]),
            "session_items": len(self.shared_memory.get("session_context", {}))
        }
    
    def clear_short_term_memory(self) -> str:
        """Limpa memória de curto prazo (sessão atual)"""
        confirmation = input("ATENCAO: Isso apagara a memoria da sessao atual. Confirma? (s/n): ").strip().lower()
        if confirmation in ['s', 'sim', 'y', 'yes']:
            # Limpa memória compartilhada
            self.shared_memory = {
                "recent_queries": [],
                "cached_responses": {},
                "user_preferences": {},
                "session_context": {}
            }
            self.save_shared_memory()
            return "Memoria de curto prazo limpa com sucesso."
        else:
            return "Operacao cancelada."
    
    def clear_long_term_memory(self) -> str:
        """Limpa memória de longo prazo (dados persistentes)"""
        print("ATENCAO: Esta operacao apagara TODOS os dados de longo prazo:")
        print("   • Historico de decisoes do Research Agent")
        print("   • Padroes de memoria aprendidos")
        print("   • Dados de aprendizado do sistema")
        print("   • Configuracoes aprendidas")
        print()
        
        confirmation = input("Digite 'CONFIRMAR RESET' para prosseguir: ").strip()
        if confirmation == "CONFIRMAR RESET":
            try:
                # Limpa arquivo de memória de longo prazo
                if os.path.exists("long_term_memory.json"):
                    os.remove("long_term_memory.json")
                
                # Limpa padrões de memória
                if os.path.exists("memory_patterns.json"):
                    os.remove("memory_patterns.json")
                
                # Reset do histórico de decisões do research agent
                if hasattr(self.research_agent, 'decision_history'):
                    self.research_agent.decision_history = []
                
                # Reset da memória interna do research agent se existir
                if hasattr(self.research_agent, 'memory_manager'):
                    self.research_agent.memory_manager.long_term_storage = {
                        "successful_queries": [],
                        "failed_queries": [],
                        "optimization_insights": [],
                        "user_patterns": []
                    }
                    if hasattr(self.research_agent.memory_manager, 'save_to_disk'):
                        self.research_agent.memory_manager.save_to_disk()
                
                return "Memoria de longo prazo limpa com sucesso."
                
            except Exception as e:
                return f"Erro ao limpar memoria de longo prazo: {e}"
        else:
            return "Operacao cancelada."
    
    def clear_all_memories(self) -> str:
        """Limpa TODAS as memórias do sistema"""
        print("ATENCAO EXTREMA: Esta operacao apagara TUDO:")
        print("   • Memoria de curto prazo (sessao)")
        print("   • Memoria de longo prazo (historico)")
        print("   • Dados do Maestro (feedback, parametros)")
        print("   • Registros de documentos processados")
        print("   • Todas as configuracoes aprendidas")
        print()
        print("Esta operacao e IRREVERSIVEL!")
        print()
        
        confirmation = input("Digite 'RESET TOTAL CONFIRMADO' para prosseguir: ").strip()
        if confirmation == "RESET TOTAL CONFIRMADO":
            try:
                # Limpa memória de curto prazo
                self.shared_memory = {
                    "recent_queries": [],
                    "cached_responses": {},
                    "user_preferences": {},
                    "session_context": {}
                }
                self.save_shared_memory()
                
                # Limpa memória de longo prazo
                files_to_remove = [
                    "long_term_memory.json",
                    "memory_patterns.json",
                    "maestro_parameters.json",
                    "maestro_feedback.json", 
                    "maestro_learning.json"
                ]
                
                for file in files_to_remove:
                    if os.path.exists(file):
                        os.remove(file)
                
                # Reset do Maestro
                if self.maestro_agent:
                    self.maestro_agent.feedback_history = []
                    self.maestro_agent.learning_metrics = {
                        "response_quality_scores": [],
                        "parameter_adjustments": [],
                        "user_satisfaction_trends": [],
                        "agent_performance": {
                            "orchestrator": {"avg_response_time": 0, "success_rate": 1.0},
                            "research_agent": {"avg_response_time": 0, "success_rate": 1.0},
                            "document_agent": {"avg_response_time": 0, "success_rate": 1.0}
                        }
                    }
                    # Reset parâmetros para valores padrão
                    self.maestro_agent.__init__(self.llm)
                
                # Reset do research agent
                if hasattr(self.research_agent, 'decision_history'):
                    self.research_agent.decision_history = []
                
                return "RESET TOTAL realizado. Sistema reiniciado com configuracoes padrao."
                
            except Exception as e:
                return f"Erro durante reset total: {e}"
        else:
            return "Operacao cancelada."
    
    def get_memory_info(self) -> str:
        """Retorna informações detalhadas sobre as memórias do sistema"""
        info = []
        
        # Memória de curto prazo
        info.append("MEMORIA DE CURTO PRAZO:")
        info.append(f"   Consultas recentes: {len(self.shared_memory['recent_queries'])}")
        info.append(f"   Respostas em cache: {len(self.shared_memory['cached_responses'])}")
        info.append(f"   Contexto da sessao: {len(self.shared_memory.get('session_context', {}))}")
        
        # Memória de longo prazo
        info.append("\nMEMORIA DE LONGO PRAZO:")
        
        # Verifica arquivos existentes
        long_term_files = {
            "long_term_memory.json": "Memoria persistente principal",
            "memory_patterns.json": "Padroes de uso aprendidos",
            "maestro_parameters.json": "Parametros otimizados",
            "maestro_feedback.json": "Historico de feedback",
            "maestro_learning.json": "Metricas de aprendizado"
        }
        
        for file, description in long_term_files.items():
            if os.path.exists(file):
                try:
                    size = os.path.getsize(file)
                    info.append(f"   OK {description}: {size} bytes")
                except:
                    info.append(f"   ERRO {description}: arquivo corrompido")
            else:
                info.append(f"   NAO EXISTE {description}: nao existe")
        
        # Dados do Maestro
        if self.maestro_agent:
            info.append(f"\nDADOS DO MAESTRO:")
            info.append(f"   Feedback historico: {len(self.maestro_agent.feedback_history)}")
            info.append(f"   Scores de qualidade: {len(self.maestro_agent.learning_metrics.get('response_quality_scores', []))}")
            info.append(f"   Ajustes de parametros: {len(self.maestro_agent.learning_metrics.get('parameter_adjustments', []))}")
        
        # Dados do Research Agent
        if hasattr(self.research_agent, 'decision_history'):
            info.append(f"\nDADOS DO RESEARCH AGENT:")
            info.append(f"   Historico de decisoes: {len(self.research_agent.decision_history)}")
        
        return "\n".join(info)
    
    def display_welcome(self):
        """Exibe mensagem de boas-vindas"""
        stats = self.get_system_statistics()
        
        print("=" * 70)
        print("SISTEMA MULTI-AGENTE INTELIGENTE")
        print("=" * 70)
        print("Pesquisa Avançada + Base de Conhecimento Local + Web Search")
        print()
        
        print("STATUS DO SISTEMA:")
        print(f"   Documentos na base: {stats['documents_in_base']}")
        print(f"   Consultas na sessão: {stats['session_queries']}")
        print(f"   Respostas em cache: {stats['cached_responses']}")
        print()
        
        print("=" * 70)
        print("COMANDOS DISPONÍVEIS:")
        print("=" * 70)
        print()
        
        print("PESQUISA:")
        print("   • Digite sua pergunta diretamente")
        print("   • Exemplo: 'Qual a situação da Petrobras?'")
        print("   • Exemplo: 'Como está o mercado hoje?'")
        print()
        
        print("GERENCIAR DOCUMENTOS:")
        print("   • 'scan' - Escanear novos documentos")
        print("   • 'docs' - Listar documentos disponíveis")
        print("   • 'status' - Ver status da base de conhecimento")
        print()
        
        print("ESTATÍSTICAS:")
        print("   • 'stats' - Estatísticas detalhadas do sistema")
        print("   • 'memoria' - Status da memória de longo prazo")
        print("   • 'decisions' - Histórico de decisões do sistema")
        if self.admin_mode:
            print("   • 'stats_supervisor' - Estatísticas do Supervisor")
            print("   • 'stats_meta_auditor' - Estatísticas do Meta-Auditor")
            print("   • 'stats_data_science' - Estatísticas do Data Science Agent")
            print("   • 'operations_data_science' - Operações disponíveis do Data Science")
        print()
        
        print("CUSTOS E ECONOMIA:")
        print("   • 'costs' - Custos da sessão atual")
        print("   • 'cost_report' - Relatório detalhado de custos")
        print("   • 'pricing' - Tabela de preços das APIs")
        print("   • 'estimate_cost' - Estimativa de custos por consulta")
        print()
        
        print("SISTEMA:")
        print("   • 'help' - Mostrar esta ajuda novamente")
        print("   • 'clear' - Limpar tela")
        print("   • 'exit', 'quit', 'sair' - Encerrar sistema")
        print()
        
        print("=" * 70)
        print("DICAS:")
        print("   • O sistema decide automaticamente entre base local e web")
        print("   • Perguntas similares são respondidas da memória")
        print("   • Para documentos específicos, mencione o nome da empresa")
        print("   • Coloque novos documentos em: knowledge_base/novos_docs/")
        print("=" * 70)
        print()
    
    def get_maestro_usage_stats(self) -> str:
        """Retorna estatísticas de uso do maestro na sessão"""
        stats = self.maestro_stats
        total = stats["total_interactions"]
        
        if total == 0:
            return "Nenhuma interação registrada nesta sessão."
        
        skipped_pct = (stats["commands_skipped"] / total) * 100
        research_pct = (stats["research_queries"] / total) * 100
        
        return f"""ESTATÍSTICAS DE USO DO MAESTRO (SESSÃO):
    Total de interações: {total}
    Comandos simples (sem maestro): {stats["commands_skipped"]} ({skipped_pct:.1f}%)
    Consultas pesquisa (com maestro): {stats["research_queries"]} ({research_pct:.1f}%)
    
    EFICIÊNCIA: {skipped_pct:.1f}% das operações não precisaram do maestro"""
    
    def get_optimal_llm(self, operation_type: str = "main") -> OpenAI:
        """Seleciona o modelo LLM ideal baseado no tipo de operação"""
        model_mapping = {
            "main": "main",
            "fast": "fast",
            "simple_command": "fast",
            "complex_analysis": "analysis", 
            "research_synthesis": "research",
            "document_analysis": "analysis",
            "intent_analysis": "fast",
            "maestro_evaluation": "main"
        }
        
        selected_model = model_mapping.get(operation_type, "main")
        return self.llm_models.get(selected_model, self.llm)

# ===== FUNÇÃO PRINCIPAL DO ORCHESTRATOR =====
async def main(maestro_enabled: bool = True, admin_mode: bool = True):
    """Função principal do orchestrator
    
    Args:
        maestro_enabled: Se o Maestro está ativo
        admin_mode: True = Modo Admin (completo), False = Modo Usuário (simplificado)
    """
    load_dotenv()
    
    openai_key = os.getenv("OPENAI_API_KEY")
    tavily_key = os.getenv("TAVILY_KEY")
    
    if not openai_key:
        print("ERRO: OPENAI_API_KEY não encontrada no arquivo .env")
        print("Adicione sua chave OpenAI no arquivo .env")
        return
        
    if not tavily_key:
        print("ERRO: TAVILY_KEY não encontrada no arquivo .env")
        print("Adicione sua chave Tavily no arquivo .env")
        return
    
    try:
        # Inicializa orchestrator
        orchestrator = IntelligentOrchestrator(openai_key, tavily_key, maestro_enabled=maestro_enabled, admin_mode=admin_mode)
        await orchestrator.initialize()
        
        # Exibe interface
        orchestrator.display_welcome()
        
        # Loop principal
        while True:
            try:
                choice = orchestrator.display_interaction_menu()
                result = await orchestrator.handle_user_choice(choice)
                
                if result:
                    query, response, context = result
                    
                    print("\n" + "="*50)
                    print("RESPOSTA:")
                    print("="*50)
                    print(response)
                    print("="*50)
                    
                    # Verifica se deve pular o maestro para comandos simples ou se não é modo admin
                    skip_maestro = (
                        not admin_mode or  # NOVO: Modo usuário pula maestro sempre
                        orchestrator.is_simple_command(query) or 
                        context.get("skip_maestro", False) or
                        context.get("interaction_type") == "system_command" or
                        context.get("interaction_type") == "agent_conversations" or  # NOVO: Conversas com agentes
                        (orchestrator.first_interaction and orchestrator.skip_first_maestro)
                    )
                    
                    # NOVO: Se é primeira interação e modo admin, pergunta se quer pular maestro
                    if admin_mode and orchestrator.first_interaction and not skip_maestro and orchestrator.maestro_enabled:
                        print("\n" + "="*50)
                        print("PRIMEIRA INTERAÇÃO - MAESTRO")
                        print("="*50)
                        print("O Maestro vai avaliar a qualidade da resposta e coletar feedback.")
                        print("Você pode:")
                        print("1. Continuar com avaliação (padrão)")
                        print("2. Pular avaliação desta vez")
                        print("3. Desabilitar maestro permanentemente")
                        
                        choice = input("\nEscolha (1/2/3) ou Enter para continuar: ").strip()
                        
                        if choice == "2":
                            skip_maestro = True
                            print("Pulando avaliação do maestro desta vez")
                        elif choice == "3":
                            orchestrator.maestro_enabled = False
                            skip_maestro = True
                            print("Maestro desabilitado permanentemente (use 'maestro_on' para reativar)")
                        else:
                            print("Continuando com avaliação do maestro")
                    
                    # Marca que não é mais primeira interação
                    orchestrator.first_interaction = False
                    
                    # Interação com Maestro (apenas no modo admin e se habilitado)
                    if admin_mode and orchestrator.maestro_enabled and context.get("interaction_type") != "maestro_config" and not skip_maestro:
                        agent_used = context.get("agent_used", "unknown")
                        
                        try:
                            # NOVO: Maestro coleta feedback sobre a resposta
                            print("\n" + "="*50)
                            print("AVALIAÇÃO DO MAESTRO")
                            print("="*50)
                            print("Avalie a qualidade da resposta para melhorar futuras consultas:")
                            print("1 = Muito ruim | 2 = Ruim | 3 = Regular | 4 = Bom | 5 = Muito bom")
                            
                            while True:
                                try:
                                    satisfaction = int(input("\nNota (1-5): ").strip())
                                    if 1 <= satisfaction <= 5:
                                        break
                                    else:
                                        print("Por favor, digite um número de 1 a 5")
                                except ValueError:
                                    print("Por favor, digite um número de 1 a 5")
                            
                            user_comments = input("Comentários (opcional): ").strip()
                            
                            # Coleta feedback usando novo método
                            feedback_data = await orchestrator.maestro_agent.collect_response_feedback(
                                query=query,
                                response=response,
                                agent_type=agent_used,
                                user_satisfaction=satisfaction,
                                user_comments=user_comments
                            )
                            
                            # NOVO: Finaliza processo no histórico com dados de satisfação
                            process_id = context.get("process_id")
                            if process_id:
                                session_cost_summary = cost_tracker.get_session_summary()
                                total_cost = session_cost_summary.get("total_cost", 0.0)
                                
                                completed_process = orchestrator.process_history_manager.complete_process(
                                    final_response=response,
                                    total_cost=total_cost,
                                    user_satisfaction=satisfaction
                                )
                                
                                print(f"HISTÓRICO: Processo {process_id} finalizado com satisfação {satisfaction}/5")
                            
                            # Exibe resumo do aprendizado
                            if satisfaction >= 4:
                                print("Obrigado! Esta resposta foi marcada como sucesso para futuras orientações.")
                            else:
                                print("Obrigado! Este feedback ajudará a melhorar futuras respostas.")
                            
                            # Exibe estatísticas de aprendizado
                            learning_summary = orchestrator.maestro_agent.get_learning_summary()
                            print(f"Base de conhecimento: {learning_summary['successful_responses']} sucessos, {learning_summary['failed_responses']} falhas")
                                
                        except Exception as e:
                            print(f"Erro na coleta de feedback do Maestro: {e}")
                            
                            # NOVO: Finaliza processo mesmo com erro no feedback
                            process_id = context.get("process_id")
                            if process_id:
                                session_cost_summary = cost_tracker.get_session_summary()
                                total_cost = session_cost_summary.get("total_cost", 0.0)
                                
                                orchestrator.process_history_manager.complete_process(
                                    final_response=response,
                                    total_cost=total_cost,
                                    user_satisfaction=None  # Sem avaliação devido ao erro
                                )
                    
                    elif skip_maestro:
                        # Comando simples ou modo usuário - informa que o maestro foi pulado
                        if not admin_mode:
                            print(f"[MODO USUÁRIO] Resposta entregue sem avaliação do Maestro")
                        else:
                            print(f"[SISTEMA] Comando '{query}' executado diretamente (maestro não utilizado)")
                        orchestrator.maestro_stats["commands_skipped"] += 1
                        
                        # NOVO: Finaliza processo sem avaliação do Maestro
                        process_id = context.get("process_id")
                        if process_id:
                            session_cost_summary = cost_tracker.get_session_summary()
                            total_cost = session_cost_summary.get("total_cost", 0.0)
                            
                            # Em modo usuário, assume satisfação neutra
                            default_satisfaction = 4 if not admin_mode else None
                            
                            orchestrator.process_history_manager.complete_process(
                                final_response=response,
                                total_cost=total_cost,
                                user_satisfaction=default_satisfaction
                            )
                    else:
                        orchestrator.maestro_stats["research_queries"] += 1
                        
                        # NOVO: Finaliza processo sem feedback específico
                        process_id = context.get("process_id")
                        if process_id:
                            session_cost_summary = cost_tracker.get_session_summary()
                            total_cost = session_cost_summary.get("total_cost", 0.0)
                            
                            orchestrator.process_history_manager.complete_process(
                                final_response=response,
                                total_cost=total_cost,
                                user_satisfaction=None
                            )
                    
                    orchestrator.maestro_stats["total_interactions"] += 1
                    
                    # Adiciona à memória para próximas consultas
                    orchestrator.shared_memory["recent_queries"].append({
                        "query": query,
                        "timestamp": datetime.now().isoformat(),
                        "interaction_type": context.get("interaction_type", "unknown")
                    })
                    
                    # Mantém apenas últimas 20 consultas
                    if len(orchestrator.shared_memory["recent_queries"]) > 20:
                        orchestrator.shared_memory["recent_queries"] = orchestrator.shared_memory["recent_queries"][-20:]
                    
                    # Salva memória
                    orchestrator.save_shared_memory()
                    
                else:
                    print("Voltando ao menu principal...")
                
                # Pergunta se quer continuar
                continue_session = input("\nDeseja fazer outra consulta? (s/n): ").strip().lower()
                if continue_session not in ['s', 'sim', 'y', 'yes', '']:
                    # Exibe estatísticas antes de sair (apenas modo admin)
                    if admin_mode:
                        print("\n" + "="*70)
                        print(orchestrator.get_maestro_usage_stats())
                        print("="*70)
                    print("\nEncerrando sistema. Até logo!")
                    break
                
            except KeyboardInterrupt:
                print("\n\nInterrompido pelo usuário.")
                print("Encerrando sistema...")
                break
            except Exception as e:
                print(f"\nErro: {e}")
                print("Retornando ao menu principal...")
                
    except Exception as e:
        print(f"Erro na inicialização: {e}")
        return

if __name__ == "__main__":
    import sys
    
    # Verifica argumentos de linha de comando
    admin_mode = True  # Padrão é modo admin
    
    if len(sys.argv) > 1:
        if sys.argv[1].lower() in ['user', 'usuario', 'u']:
            admin_mode = False
            print("Iniciando em MODO USUÁRIO")
        elif sys.argv[1].lower() in ['admin', 'administrador', 'a']:
            admin_mode = True
            print("Iniciando em MODO ADMINISTRADOR")
    
    asyncio.run(main(admin_mode=admin_mode))