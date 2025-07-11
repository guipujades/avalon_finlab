#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Conversas Diretas com Agentes
Permite conversas individuais com Maestro, Supervisor e Meta-Auditor
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

class AgentConversationManager:
    """Gerencia conversas diretas com cada agente do sistema"""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.conversation_dir = "agent_conversations"
        self.ensure_conversation_directory()
        
        # Arquivos de histórico para cada agente
        self.conversation_files = {
            "maestro": f"{self.conversation_dir}/maestro_conversations.json",
            "supervisor": f"{self.conversation_dir}/supervisor_conversations.json", 
            "meta_auditor": f"{self.conversation_dir}/meta_auditor_conversations.json"
        }
        
        # NOVO: Memória curta para conversas ativas (contexto da sessão atual)
        self.session_memory = {
            "maestro": [],
            "supervisor": [],
            "meta_auditor": []
        }
        
        # Configuração da memória curta
        self.memory_config = {
            "max_context_messages": 5,  # Últimas 5 trocas de mensagens
            "context_enabled": True,    # Pode ser desabilitado se necessário
            "include_timestamps": False  # Para não poluir o contexto
        }
        
        # Carrega históricos existentes
        self.conversation_histories = {}
        for agent, file_path in self.conversation_files.items():
            self.conversation_histories[agent] = self.load_conversation_history(file_path)
    
    def ensure_conversation_directory(self):
        """Garante que o diretório de conversas existe"""
        if not os.path.exists(self.conversation_dir):
            os.makedirs(self.conversation_dir)
    
    def load_conversation_history(self, file_path: str) -> List[Dict]:
        """Carrega histórico de conversas de um arquivo"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"CONVERSATIONS: Erro ao carregar {file_path}: {e}")
        return []
    
    def save_conversation_history(self, agent: str):
        """Salva histórico de conversas de um agente"""
        try:
            file_path = self.conversation_files[agent]
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_histories[agent], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"CONVERSATIONS: Erro ao salvar {agent}: {e}")
    
    def record_conversation(self, agent: str, user_input: str, agent_response: str, context: Dict = None):
        """Registra uma conversa com um agente"""
        conversation_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "agent_response": agent_response,
            "context": context or {},
            "conversation_id": f"{agent}_{datetime.now().timestamp()}"
        }
        
        self.conversation_histories[agent].append(conversation_entry)
        
        # Mantém apenas últimas 100 conversas por agente
        if len(self.conversation_histories[agent]) > 100:
            self.conversation_histories[agent] = self.conversation_histories[agent][-100:]
        
        self.save_conversation_history(agent)
    
    async def start_maestro_conversation(self) -> bool:
        """Inicia conversa direta com o Maestro"""
        print("\n" + "="*60)
        print("CONVERSA DIRETA COM O MAESTRO")
        print("="*60)
        print("Você está agora conversando diretamente com o Maestro Agent.")
        print("O Maestro pode ajudar com:")
        print("- Análise de performance do sistema")
        print("- Ajustes de parâmetros")
        print("- Insights sobre otimizações")
        print("- Histórico de feedback e aprendizado")
        print()
        print("💡 MEMÓRIA ATIVA: O Maestro lembrará desta conversa!")
        print("Digite 'sair' para encerrar a conversa")
        print("Digite 'limpar' para resetar o contexto da conversa")
        print("="*60)
        
        # Limpa memória da sessão anterior do Maestro
        self.clear_session_memory("maestro")
        
        conversation_count = 0
        
        while True:
            try:
                user_input = input("\nVocê para Maestro: ").strip()
                
                if user_input.lower() in ['sair', 'exit', 'quit']:
                    print(f"\nConversa com Maestro encerrada. {conversation_count} interações registradas.")
                    self.clear_session_memory("maestro")  # Limpa ao sair
                    break
                
                if user_input.lower() in ['limpar', 'clear', 'reset']:
                    self.clear_session_memory("maestro")
                    print("🧹 Contexto da conversa limpo! Começando conversa fresca.")
                    continue
                
                if not user_input:
                    continue
                
                # NOVO: Inclui contexto da conversa
                conversation_context = self.get_conversation_context("maestro")
                
                # Conversa direta com o Maestro (com contexto)
                maestro_response = await self.orchestrator.maestro_agent.direct_conversation_with_context(
                    user_input, conversation_context
                )
                
                print(f"\nMaestro: {maestro_response}")
                
                # NOVO: Adiciona à memória de sessão
                self.add_to_session_memory("maestro", user_input, maestro_response)
                
                # Registra a conversa no histórico permanente
                self.record_conversation("maestro", user_input, maestro_response)
                conversation_count += 1
                
            except KeyboardInterrupt:
                print(f"\n\nConversa interrompida. {conversation_count} interações registradas.")
                self.clear_session_memory("maestro")
                break
            except Exception as e:
                print(f"Erro na conversa com Maestro: {e}")
        
        return True
    
    async def start_supervisor_conversation(self) -> bool:
        """Inicia conversa direta com o Supervisor"""
        print("\n" + "="*60)
        print("CONVERSA DIRETA COM O SUPERVISOR")
        print("="*60)
        print("Você está agora conversando diretamente com o Supervisor Agent.")
        print("O Supervisor pode ajudar com:")
        print("- Análise de coerência de respostas")
        print("- Verificação de consistência temporal")
        print("- Relatórios de supervisão")
        print("- Estatísticas de aprovação/reprovação")
        print()
        print("💡 MEMÓRIA ATIVA: O Supervisor lembrará desta conversa!")
        print("Digite 'sair' para encerrar a conversa")
        print("Digite 'limpar' para resetar o contexto da conversa")
        print("="*60)
        
        # Limpa memória da sessão anterior do Supervisor
        self.clear_session_memory("supervisor")
        
        conversation_count = 0
        
        while True:
            try:
                user_input = input("\nVocê para Supervisor: ").strip()
                
                if user_input.lower() in ['sair', 'exit', 'quit']:
                    print(f"\nConversa com Supervisor encerrada. {conversation_count} interações registradas.")
                    self.clear_session_memory("supervisor")  # Limpa ao sair
                    break
                
                if user_input.lower() in ['limpar', 'clear', 'reset']:
                    self.clear_session_memory("supervisor")
                    print("🧹 Contexto da conversa limpo! Começando conversa fresca.")
                    continue
                
                if not user_input:
                    continue
                
                # NOVO: Inclui contexto da conversa
                conversation_context = self.get_conversation_context("supervisor")
                
                # Monta prompt com contexto para o Supervisor
                prompt_with_context = f"""Você é o Supervisor Agent em conversa direta com o arquiteto do sistema.

Seu papel como SUPERVISOR:
- Verificação de coerência e qualidade
- Análise de consistência temporal e lógica
- Fact-checking e validação
- Relatórios de supervisão

{conversation_context}

NOVA PERGUNTA DO ARQUITETO: {user_input}

Responda de forma técnica mantendo o contexto da conversa."""
                
                # Conversa direta com o Supervisor (usando Claude)
                supervisor_response = await self.orchestrator.supervisor_agent._call_llm(
                    prompt_with_context,
                    max_tokens=1500,
                    query_context="direct_conversation_supervisor_with_memory"
                )
                
                print(f"\nSupervisor: {supervisor_response}")
                
                # NOVO: Adiciona à memória de sessão
                self.add_to_session_memory("supervisor", user_input, supervisor_response)
                
                # Registra a conversa no histórico permanente
                self.record_conversation("supervisor", user_input, supervisor_response)
                conversation_count += 1
                
            except KeyboardInterrupt:
                print(f"\n\nConversa interrompida. {conversation_count} interações registradas.")
                self.clear_session_memory("supervisor")
                break
            except Exception as e:
                print(f"Erro na conversa com Supervisor: {e}")
        
        return True
    
    async def start_meta_auditor_conversation(self) -> bool:
        """Inicia conversa direta com o Meta-Auditor"""
        print("\n" + "="*60)
        print("CONVERSA DIRETA COM O META-AUDITOR")
        print("="*60)
        print("Você está agora conversando diretamente com o Meta-Auditor Agent.")
        print("O Meta-Auditor pode ajudar com:")
        print("- Auditoria sistêmica completa")
        print("- Análise de eficiência do pipeline")
        print("- Identificação de gargalos")
        print("- Sugestões de otimização arquitetural")
        print()
        print("💡 MEMÓRIA ATIVA: O Meta-Auditor lembrará desta conversa!")
        print("Digite 'sair' para encerrar a conversa")
        print("Digite 'limpar' para resetar o contexto da conversa")
        print("="*60)
        
        # Limpa memória da sessão anterior do Meta-Auditor
        self.clear_session_memory("meta_auditor")
        
        conversation_count = 0
        
        while True:
            try:
                user_input = input("\nVocê para Meta-Auditor: ").strip()
                
                if user_input.lower() in ['sair', 'exit', 'quit']:
                    print(f"\nConversa com Meta-Auditor encerrada. {conversation_count} interações registradas.")
                    self.clear_session_memory("meta_auditor")  # Limpa ao sair
                    break
                
                if user_input.lower() in ['limpar', 'clear', 'reset']:
                    self.clear_session_memory("meta_auditor")
                    print("🧹 Contexto da conversa limpo! Começando conversa fresca.")
                    continue
                
                if not user_input:
                    continue
                
                # NOVO: Inclui contexto da conversa
                conversation_context = self.get_conversation_context("meta_auditor")
                
                # Monta prompt com contexto para o Meta-Auditor
                prompt_with_context = f"""Você é o Meta-Auditor Agent em conversa direta com o arquiteto do sistema.

Seu papel como META-AUDITOR:
- Auditoria sistêmica e análise holística
- Identificação de gargalos e ineficiências
- Sugestões de otimização arquitetural
- Insights sobre saúde do sistema

{conversation_context}

NOVA PERGUNTA DO ARQUITETO: {user_input}

Forneça insights sistêmicos mantendo o contexto da conversa."""
                
                # Conversa direta com o Meta-Auditor (usando Gemini)
                meta_auditor_response = await self.orchestrator.meta_auditor_agent._call_gemini(
                    prompt_with_context,
                    operation="direct_conversation_with_memory",
                    query_context="architect_discussion_contextual"
                )
                
                print(f"\nMeta-Auditor: {meta_auditor_response}")
                
                # NOVO: Adiciona à memória de sessão
                self.add_to_session_memory("meta_auditor", user_input, meta_auditor_response)
                
                # Registra a conversa no histórico permanente
                self.record_conversation("meta_auditor", user_input, meta_auditor_response)
                conversation_count += 1
                
            except KeyboardInterrupt:
                print(f"\n\nConversa interrompida. {conversation_count} interações registradas.")
                self.clear_session_memory("meta_auditor")
                break
            except Exception as e:
                print(f"Erro na conversa com Meta-Auditor: {e}")
        
        return True
    
    def display_agent_conversation_menu(self) -> Optional[str]:
        """Exibe menu de conversas com agentes"""
        print("\n" + "="*60)
        print("CONVERSAS DIRETAS COM AGENTES")
        print("="*60)
        
        # Mostra estatísticas de conversas
        for agent, history in self.conversation_histories.items():
            count = len(history)
            last_conversation = history[-1]['timestamp'][:10] if history else "Nunca"
            memory_count = len(self.session_memory[agent])
            print(f"{agent.upper()}: {count} conversas registradas (última: {last_conversation}) | Memória: {memory_count} interações")
        
        print("\n1. Conversar com MAESTRO")
        print("2. Conversar com SUPERVISOR") 
        print("3. Conversar com META-AUDITOR")
        print("4. Ver histórico de conversas")
        print("5. Exportar conversas")
        print("6. Status da memória de sessão")
        print("7. Limpar toda memória de sessão")
        print("0. Voltar ao menu principal")
        print("="*60)
        
        while True:
            try:
                choice = input("Escolha uma opção (0-7): ").strip()
                if choice in ['0', '1', '2', '3', '4', '5', '6', '7']:
                    return choice
                else:
                    print("Por favor, digite um número de 0 a 7")
            except KeyboardInterrupt:
                return "0"
            except:
                print("Por favor, digite um número de 0 a 7")
    
    async def handle_agent_conversation_choice(self, choice: str) -> bool:
        """Processa escolha do menu de conversas"""
        if choice == "1":
            return await self.start_maestro_conversation()
        elif choice == "2":
            return await self.start_supervisor_conversation()
        elif choice == "3":
            return await self.start_meta_auditor_conversation()
        elif choice == "4":
            self.display_conversation_history()
            return True
        elif choice == "5":
            self.export_conversations()
            return True
        elif choice == "6":
            # NOVO: Status da memória de sessão
            self.display_memory_status()
            return True
        elif choice == "7":
            # NOVO: Limpar toda memória de sessão
            self.clear_all_session_memory()
            input("\nPressione Enter para continuar...")
            return True
        elif choice == "0":
            return False
        else:
            print("Opção inválida")
            return True
    
    def display_conversation_history(self):
        """Exibe histórico resumido de conversas"""
        print("\n" + "="*60)
        print("HISTÓRICO DE CONVERSAS COM AGENTES")
        print("="*60)
        
        for agent, history in self.conversation_histories.items():
            print(f"\n{agent.upper()} ({len(history)} conversas):")
            
            if not history:
                print("   Nenhuma conversa registrada")
                continue
            
            # Mostra últimas 5 conversas
            recent_conversations = history[-5:]
            for conv in recent_conversations:
                timestamp = conv['timestamp'][:19].replace('T', ' ')
                user_preview = conv['user_input'][:50] + "..." if len(conv['user_input']) > 50 else conv['user_input']
                print(f"   [{timestamp}] {user_preview}")
        
        input("\nPressione Enter para continuar...")
    
    def export_conversations(self):
        """Exporta conversas para arquivo de texto"""
        try:
            export_file = f"exported_conversations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            with open(export_file, 'w', encoding='utf-8') as f:
                f.write("CONVERSAS COM AGENTES DO SISTEMA\n")
                f.write("="*60 + "\n")
                f.write(f"Exportado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                for agent, history in self.conversation_histories.items():
                    f.write(f"\n{agent.upper()} - {len(history)} conversas\n")
                    f.write("-" * 40 + "\n")
                    
                    for conv in history:
                        timestamp = conv['timestamp'][:19].replace('T', ' ')
                        f.write(f"\n[{timestamp}]\n")
                        f.write(f"VOCÊ: {conv['user_input']}\n")
                        f.write(f"{agent.upper()}: {conv['agent_response']}\n")
                        f.write("-" * 20 + "\n")
            
            print(f"\nConversas exportadas para: {export_file}")
            
        except Exception as e:
            print(f"Erro ao exportar conversas: {e}")
        
        input("Pressione Enter para continuar...")
    
    def get_conversation_summary_for_agents(self) -> Dict[str, Any]:
        """Retorna resumo das conversas para uso pelos agentes"""
        summary = {}
        
        for agent, history in self.conversation_histories.items():
            if not history:
                summary[agent] = {"total_conversations": 0, "recent_topics": []}
                continue
            
            recent_conversations = history[-10:]  # Últimas 10
            recent_topics = [conv['user_input'][:100] for conv in recent_conversations]
            
            summary[agent] = {
                "total_conversations": len(history),
                "recent_topics": recent_topics,
                "last_conversation": history[-1]['timestamp'] if history else None
            }
        
        return summary
    
    # NOVOS MÉTODOS PARA MEMÓRIA CURTA
    def add_to_session_memory(self, agent: str, user_input: str, agent_response: str):
        """Adiciona interação à memória de sessão"""
        if not self.memory_config["context_enabled"]:
            return
        
        interaction = {
            "user": user_input,
            "agent": agent_response
        }
        
        self.session_memory[agent].append(interaction)
        
        # Mantém apenas as últimas N interações
        max_messages = self.memory_config["max_context_messages"]
        if len(self.session_memory[agent]) > max_messages:
            self.session_memory[agent] = self.session_memory[agent][-max_messages:]
    
    def get_conversation_context(self, agent: str) -> str:
        """Constrói contexto da conversa atual para incluir no prompt"""
        if not self.memory_config["context_enabled"] or not self.session_memory[agent]:
            return ""
        
        context_parts = ["CONTEXTO DA CONVERSA ATUAL:"]
        
        for i, interaction in enumerate(self.session_memory[agent], 1):
            context_parts.append(f"Interação {i}:")
            context_parts.append(f"ARQUITETO: {interaction['user']}")
            context_parts.append(f"VOCÊ: {interaction['agent']}")
            context_parts.append("")  # Linha em branco
        
        context_parts.append("---")
        context_parts.append("Continue a conversa mantendo consistência com o contexto acima.")
        context_parts.append("")
        
        return "\n".join(context_parts)
    
    def clear_session_memory(self, agent: str):
        """Limpa memória de sessão de um agente específico"""
        self.session_memory[agent] = []
        print(f"MEMORY: Contexto de sessão do {agent.upper()} limpo")
    
    def clear_all_session_memory(self):
        """Limpa memória de sessão de todos os agentes"""
        for agent in self.session_memory:
            self.session_memory[agent] = []
        print("MEMORY: Contexto de sessão de todos os agentes limpo")
    
    def get_memory_status(self) -> Dict:
        """Retorna status da memória de sessão"""
        status = {}
        for agent in self.session_memory:
            status[agent] = {
                "interactions_in_memory": len(self.session_memory[agent]),
                "memory_enabled": self.memory_config["context_enabled"],
                "max_context": self.memory_config["max_context_messages"]
            }
        return status
    
    def display_memory_status(self):
        """Exibe status detalhado da memória de sessão"""
        print("\n" + "="*60)
        print("STATUS DA MEMÓRIA DE SESSÃO")
        print("="*60)
        
        status = self.get_memory_status()
        
        for agent, info in status.items():
            print(f"\n{agent.upper()}:")
            print(f"  Interações na memória: {info['interactions_in_memory']}")
            print(f"  Memória habilitada: {'✅ Sim' if info['memory_enabled'] else '❌ Não'}")
            print(f"  Máximo de contexto: {info['max_context']} interações")
            
            if info['interactions_in_memory'] > 0:
                print(f"  Estado: 🧠 Contexto ativo")
            else:
                print(f"  Estado: 🆕 Conversa limpa")
        
        print(f"\nConfiguração Geral:")
        print(f"  Sistema de memória: {'✅ Ativo' if self.memory_config['context_enabled'] else '❌ Desativo'}")
        print(f"  Máximo por agente: {self.memory_config['max_context_messages']} interações")
        print(f"  Timestamps no contexto: {'✅ Sim' if self.memory_config['include_timestamps'] else '❌ Não'}")
        
        print("="*60)
        input("\nPressione Enter para continuar...") 