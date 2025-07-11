#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Histórico Completo de Processos
Captura e armazena todo o fluxo de execução do sistema multi-agente
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class ProcessStep:
    """Representa um passo no processo"""
    timestamp: str
    step_type: str  # "user_input", "intent_analysis", "research", "supervision", "meta_audit", "response"
    agent: str
    input_data: Dict
    output_data: Dict
    execution_time: float
    cost_data: Optional[Dict] = None
    metadata: Optional[Dict] = None

@dataclass
class CompleteProcess:
    """Processo completo do início ao fim"""
    process_id: str
    start_timestamp: str
    end_timestamp: str
    user_query: str
    final_response: str
    total_execution_time: float
    total_cost: float
    steps: List[ProcessStep]
    user_satisfaction: Optional[int] = None
    admin_mode: bool = True
    conversation_context: Optional[Dict] = None

class ProcessHistoryManager:
    """Gerencia o histórico completo de todos os processos"""
    
    def __init__(self):
        self.history_dir = "process_history"
        self.ensure_history_directory()
        
        # Arquivos de histórico
        self.main_history_file = f"{self.history_dir}/complete_processes.json"
        self.steps_archive_file = f"{self.history_dir}/detailed_steps.json"
        self.conversations_integration_file = f"{self.history_dir}/conversations_integration.json"
        
        # Cache em memória
        self.current_process: Optional[CompleteProcess] = None
        self.recent_processes: List[CompleteProcess] = []
        
        # Carrega histórico existente
        self.load_history()
    
    def ensure_history_directory(self):
        """Garante que o diretório de histórico existe"""
        if not os.path.exists(self.history_dir):
            os.makedirs(self.history_dir)
    
    def start_new_process(self, user_query: str, admin_mode: bool = True) -> str:
        """Inicia um novo processo"""
        process_id = f"proc_{datetime.now().timestamp()}"
        
        self.current_process = CompleteProcess(
            process_id=process_id,
            start_timestamp=datetime.now().isoformat(),
            end_timestamp="",
            user_query=user_query,
            final_response="",
            total_execution_time=0.0,
            total_cost=0.0,
            steps=[],
            admin_mode=admin_mode
        )
        
        return process_id
    
    def add_process_step(self, 
                        step_type: str,
                        agent: str,
                        input_data: Dict,
                        output_data: Dict,
                        execution_time: float,
                        cost_data: Optional[Dict] = None,
                        metadata: Optional[Dict] = None):
        """Adiciona um passo ao processo atual"""
        
        if not self.current_process:
            return
        
        step = ProcessStep(
            timestamp=datetime.now().isoformat(),
            step_type=step_type,
            agent=agent,
            input_data=input_data,
            output_data=output_data,
            execution_time=execution_time,
            cost_data=cost_data,
            metadata=metadata
        )
        
        self.current_process.steps.append(step)
    
    def complete_process(self, final_response: str, total_cost: float, user_satisfaction: Optional[int] = None):
        """Finaliza o processo atual"""
        
        if not self.current_process:
            return
        
        self.current_process.end_timestamp = datetime.now().isoformat()
        self.current_process.final_response = final_response
        self.current_process.total_cost = total_cost
        self.current_process.user_satisfaction = user_satisfaction
        
        # Calcula tempo total
        start_time = datetime.fromisoformat(self.current_process.start_timestamp)
        end_time = datetime.fromisoformat(self.current_process.end_timestamp)
        self.current_process.total_execution_time = (end_time - start_time).total_seconds()
        
        # Adiciona aos processos recentes
        self.recent_processes.append(self.current_process)
        
        # Mantém apenas últimos 50 processos em memória
        if len(self.recent_processes) > 50:
            self.recent_processes = self.recent_processes[-50:]
        
        # Salva no disco
        self.save_process_to_disk(self.current_process)
        
        # Limpa processo atual
        completed_process = self.current_process
        self.current_process = None
        
        return completed_process
    
    def save_process_to_disk(self, process: CompleteProcess):
        """Salva um processo completo no disco"""
        try:
            # Carrega histórico existente
            processes = []
            if os.path.exists(self.main_history_file):
                with open(self.main_history_file, 'r', encoding='utf-8') as f:
                    processes = json.load(f)
            
            # Adiciona novo processo
            processes.append(asdict(process))
            
            # Mantém apenas últimos 200 processos no arquivo principal
            if len(processes) > 200:
                processes = processes[-200:]
            
            # Salva arquivo principal
            with open(self.main_history_file, 'w', encoding='utf-8') as f:
                json.dump(processes, f, ensure_ascii=False, indent=2)
            
            # Salva detalhes dos steps em arquivo separado
            self.save_detailed_steps(process)
            
        except Exception as e:
            print(f"PROCESS_HISTORY: Erro ao salvar processo: {e}")
    
    def save_detailed_steps(self, process: CompleteProcess):
        """Salva detalhes completos dos steps"""
        try:
            # Carrega arquivo de steps
            all_steps = []
            if os.path.exists(self.steps_archive_file):
                with open(self.steps_archive_file, 'r', encoding='utf-8') as f:
                    all_steps = json.load(f)
            
            # Adiciona steps do processo atual
            for step in process.steps:
                step_with_process = asdict(step)
                step_with_process['process_id'] = process.process_id
                step_with_process['user_query'] = process.user_query
                all_steps.append(step_with_process)
            
            # Mantém apenas últimos 1000 steps
            if len(all_steps) > 1000:
                all_steps = all_steps[-1000:]
            
            with open(self.steps_archive_file, 'w', encoding='utf-8') as f:
                json.dump(all_steps, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"PROCESS_HISTORY: Erro ao salvar steps: {e}")
    
    def load_history(self):
        """Carrega histórico do disco"""
        try:
            if os.path.exists(self.main_history_file):
                with open(self.main_history_file, 'r', encoding='utf-8') as f:
                    processes_data = json.load(f)
                    
                # Carrega últimos 20 processos na memória
                for process_data in processes_data[-20:]:
                    process = CompleteProcess(**process_data)
                    # Reconstrói os steps
                    process.steps = [ProcessStep(**step) for step in process_data['steps']]
                    self.recent_processes.append(process)
                    
        except Exception as e:
            print(f"PROCESS_HISTORY: Erro ao carregar histórico: {e}")
    
    def get_complete_history_for_agents(self) -> Dict[str, Any]:
        """Retorna histórico completo formatado para uso pelos agentes"""
        
        # Carrega todos os processos do disco se necessário
        all_processes = []
        try:
            if os.path.exists(self.main_history_file):
                with open(self.main_history_file, 'r', encoding='utf-8') as f:
                    all_processes = json.load(f)
        except Exception:
            all_processes = []
        
        # Carrega todos os steps detalhados
        all_steps = []
        try:
            if os.path.exists(self.steps_archive_file):
                with open(self.steps_archive_file, 'r', encoding='utf-8') as f:
                    all_steps = json.load(f)
        except Exception:
            all_steps = []
        
        # Integra com conversas dos agentes
        agent_conversations = self.get_agent_conversations_integration()
        
        return {
            "total_processes": len(all_processes),
            "recent_processes": all_processes[-10:],  # Últimos 10 processos
            "all_process_steps": all_steps[-100:],  # Últimos 100 steps detalhados
            "agent_conversations": agent_conversations,
            "process_patterns": self.analyze_process_patterns(all_processes),
            "performance_metrics": self.calculate_performance_metrics(all_processes),
            "cost_analysis": self.analyze_costs(all_processes),
            "user_satisfaction_trends": self.analyze_satisfaction_trends(all_processes)
        }
    
    def get_agent_conversations_integration(self) -> Dict:
        """Integra com as conversas dos agentes"""
        try:
            # Tenta carregar conversas dos agentes
            conversations = {}
            
            agent_conv_dir = "agent_conversations"
            if os.path.exists(agent_conv_dir):
                for agent in ["maestro", "supervisor", "meta_auditor"]:
                    conv_file = f"{agent_conv_dir}/{agent}_conversations.json"
                    if os.path.exists(conv_file):
                        with open(conv_file, 'r', encoding='utf-8') as f:
                            conversations[agent] = json.load(f)[-10:]  # Últimas 10 conversas
            
            return conversations
        except Exception as e:
            print(f"PROCESS_HISTORY: Erro ao integrar conversas: {e}")
            return {}
    
    def analyze_process_patterns(self, processes: List[Dict]) -> Dict:
        """Analisa padrões nos processos"""
        if not processes:
            return {}
        
        patterns = {
            "avg_execution_time": 0.0,
            "avg_steps_per_process": 0.0,
            "most_common_failures": [],
            "efficiency_trends": [],
            "agent_usage_patterns": {}
        }
        
        try:
            # Tempo médio de execução
            execution_times = [p.get('total_execution_time', 0) for p in processes]
            patterns["avg_execution_time"] = sum(execution_times) / len(execution_times) if execution_times else 0
            
            # Número médio de steps
            step_counts = [len(p.get('steps', [])) for p in processes]
            patterns["avg_steps_per_process"] = sum(step_counts) / len(step_counts) if step_counts else 0
            
            # Padrões de uso dos agentes
            agent_usage = {}
            for process in processes:
                for step in process.get('steps', []):
                    agent = step.get('agent', 'unknown')
                    agent_usage[agent] = agent_usage.get(agent, 0) + 1
            patterns["agent_usage_patterns"] = agent_usage
            
        except Exception as e:
            print(f"PROCESS_HISTORY: Erro na análise de padrões: {e}")
        
        return patterns
    
    def calculate_performance_metrics(self, processes: List[Dict]) -> Dict:
        """Calcula métricas de performance"""
        if not processes:
            return {}
        
        try:
            total_processes = len(processes)
            successful_processes = len([p for p in processes if p.get('user_satisfaction', 3) >= 4])
            
            return {
                "success_rate": successful_processes / total_processes if total_processes > 0 else 0,
                "avg_satisfaction": sum(p.get('user_satisfaction', 3) for p in processes) / total_processes,
                "total_processes_analyzed": total_processes,
                "processes_with_feedback": len([p for p in processes if p.get('user_satisfaction') is not None])
            }
        except Exception:
            return {"success_rate": 0, "avg_satisfaction": 0}
    
    def analyze_costs(self, processes: List[Dict]) -> Dict:
        """Analisa custos dos processos"""
        if not processes:
            return {}
        
        try:
            costs = [p.get('total_cost', 0) for p in processes]
            return {
                "total_cost": sum(costs),
                "avg_cost_per_process": sum(costs) / len(costs) if costs else 0,
                "most_expensive_process": max(costs) if costs else 0,
                "cheapest_process": min(costs) if costs else 0
            }
        except Exception:
            return {"total_cost": 0, "avg_cost_per_process": 0}
    
    def analyze_satisfaction_trends(self, processes: List[Dict]) -> Dict:
        """Analisa tendências de satisfação do usuário"""
        if not processes:
            return {}
        
        try:
            # Últimos 10 processos com satisfação
            recent_with_satisfaction = [
                p for p in processes[-10:] 
                if p.get('user_satisfaction') is not None
            ]
            
            if len(recent_with_satisfaction) >= 2:
                recent_avg = sum(p['user_satisfaction'] for p in recent_with_satisfaction) / len(recent_with_satisfaction)
                
                # Compara com processos anteriores
                older_with_satisfaction = [
                    p for p in processes[:-10] 
                    if p.get('user_satisfaction') is not None
                ]
                
                if older_with_satisfaction:
                    older_avg = sum(p['user_satisfaction'] for p in older_with_satisfaction) / len(older_with_satisfaction)
                    trend = "melhorando" if recent_avg > older_avg else "estável" if recent_avg == older_avg else "piorando"
                else:
                    trend = "dados insuficientes"
                
                return {
                    "recent_avg_satisfaction": recent_avg,
                    "trend": trend,
                    "total_feedback_collected": len(recent_with_satisfaction) + len(older_with_satisfaction)
                }
        except Exception:
            pass
        
        return {"trend": "dados insuficientes"}
    
    def get_process_by_id(self, process_id: str) -> Optional[Dict]:
        """Busca um processo específico por ID"""
        # Busca primeiro na memória
        for process in self.recent_processes:
            if process.process_id == process_id:
                return asdict(process)
        
        # Busca no disco se não encontrou na memória
        try:
            if os.path.exists(self.main_history_file):
                with open(self.main_history_file, 'r', encoding='utf-8') as f:
                    processes = json.load(f)
                    for process in processes:
                        if process.get('process_id') == process_id:
                            return process
        except Exception:
            pass
        
        return None
    
    def get_recent_processes(self, limit: int = 10) -> List[Dict]:
        """Retorna processos recentes como dicionários"""
        try:
            # Converte objetos CompleteProcess para dicionários
            recent_dicts = []
            for process in self.recent_processes[-limit:]:
                if hasattr(process, '__dict__'):
                    # É um objeto CompleteProcess
                    recent_dicts.append(asdict(process))
                else:
                    # Já é um dicionário
                    recent_dicts.append(process)
            
            return recent_dicts
        except Exception as e:
            print(f"PROCESS_HISTORY: Erro ao obter processos recentes - {e}")
            return []

# Instância global do gerenciador de histórico
process_history_manager = ProcessHistoryManager() 