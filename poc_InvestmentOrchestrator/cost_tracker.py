#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Monitoramento de Custos para APIs
Rastreia gastos em tempo real de OpenAI, Anthropic, Gemini, Tavily e Perplexity
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict

@dataclass
class ApiCall:
    """Representa uma chamada de API com custos"""
    timestamp: str
    api_provider: str
    model: str
    operation: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    query_context: str
    response_preview: str

@dataclass
class QueryCostSummary:
    """Resumo de custos de uma consulta completa"""
    query: str
    timestamp: str
    total_cost_usd: float
    api_calls: List[ApiCall]
    pipeline_steps: List[str]

class CostTracker:
    """Sistema central de monitoramento de custos"""
    
    def __init__(self):
        self.cost_file = "cost_history.json"
        self.current_session_costs = []
        self.total_costs = defaultdict(float)
        self.api_calls_count = defaultdict(int)
        
        # Tabela de preços atualizada (USD por 1K tokens)
        self.pricing_table = {
            "openai": {
                "gpt-4o": {"input": 0.005, "output": 0.015},  # $5/$15 per 1M tokens
                "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},  # $0.15/$0.60 per 1M tokens
                "gpt-4-turbo": {"input": 0.01, "output": 0.03},
                "gpt-4": {"input": 0.03, "output": 0.06},
                "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
                "o1-preview": {"input": 0.015, "output": 0.06},  # $15/$60 per 1M tokens
                "o1-mini": {"input": 0.003, "output": 0.012}  # $3/$12 per 1M tokens
            },
            "anthropic": {
                "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},  # $3/$15 per 1M tokens
                "claude-3-5-haiku-20241022": {"input": 0.001, "output": 0.005},   # $1/$5 per 1M tokens
                "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},      # $15/$75 per 1M tokens
                "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
                "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125}
            },
            "google": {
                "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},  # $1.25/$5 per 1M tokens
                "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},  # $0.075/$0.30 per 1M tokens
                "gemini-1.0-pro": {"input": 0.0005, "output": 0.0015}
            },
            "tavily": {
                "search": {"per_request": 0.005},  # $0.005 per search
                "extract": {"per_url": 0.001}     # $0.001 per URL
            },
            "perplexity": {
                "online": {"per_request": 0.005},  # Estimativa baseada em uso típico
                "search": {"per_request": 0.005}
            }
        }
        
        # Limites de alerta (USD)
        self.alert_thresholds = {
            "session": 1.00,    # $1.00 por sessão
            "daily": 5.00,      # $5.00 por dia
            "monthly": 50.00    # $50.00 por mês
        }
        
        self.load_cost_history()
    
    def load_cost_history(self):
        """Carrega histórico de custos"""
        if os.path.exists(self.cost_file):
            try:
                with open(self.cost_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.total_costs = defaultdict(float, data.get('total_costs', {}))
                    self.api_calls_count = defaultdict(int, data.get('api_calls_count', {}))
            except Exception as e:
                print(f"COST_TRACKER: Erro ao carregar histórico - {e}")
    
    def save_cost_history(self):
        """Salva histórico de custos"""
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "total_costs": dict(self.total_costs),
                "api_calls_count": dict(self.api_calls_count),
                "current_session": [asdict(call) for call in self.current_session_costs[-50:]]  # Últimas 50
            }
            
            with open(self.cost_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"COST_TRACKER: Erro ao salvar histórico - {e}")
    
    def calculate_openai_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calcula custo OpenAI baseado em tokens"""
        if model not in self.pricing_table["openai"]:
            # Usa preço do gpt-4o como padrão se modelo não encontrado
            pricing = self.pricing_table["openai"]["gpt-4o"]
        else:
            pricing = self.pricing_table["openai"][model]
        
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        
        return input_cost + output_cost
    
    def calculate_anthropic_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calcula custo Anthropic baseado em tokens"""
        if model not in self.pricing_table["anthropic"]:
            # Usa preço do claude-3-5-sonnet como padrão
            pricing = self.pricing_table["anthropic"]["claude-3-5-sonnet-20241022"]
        else:
            pricing = self.pricing_table["anthropic"][model]
        
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        
        return input_cost + output_cost
    
    def calculate_gemini_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calcula custo Google Gemini baseado em tokens"""
        if model not in self.pricing_table["google"]:
            # Usa preço do gemini-1.5-pro como padrão
            pricing = self.pricing_table["google"]["gemini-1.5-pro"]
        else:
            pricing = self.pricing_table["google"][model]
        
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        
        return input_cost + output_cost
    
    def calculate_tavily_cost(self, operation: str, count: int = 1) -> float:
        """Calcula custo Tavily baseado em operações"""
        if operation == "search":
            return count * self.pricing_table["tavily"]["search"]["per_request"]
        elif operation == "extract":
            return count * self.pricing_table["tavily"]["extract"]["per_url"]
        else:
            return count * 0.005  # Padrão
    
    def calculate_perplexity_cost(self, operation: str, count: int = 1) -> float:
        """Calcula custo Perplexity baseado em requisições"""
        return count * self.pricing_table["perplexity"][operation]["per_request"]
    
    def track_api_call(self, 
                      api_provider: str,
                      model: str,
                      operation: str,
                      input_tokens: int = 0,
                      output_tokens: int = 0,
                      request_count: int = 1,
                      query_context: str = "",
                      response_preview: str = "") -> float:
        """Registra uma chamada de API e calcula custos"""
        
        # Calcula custo baseado no provider
        if api_provider.lower() == "openai":
            cost = self.calculate_openai_cost(model, input_tokens, output_tokens)
        elif api_provider.lower() == "anthropic":
            cost = self.calculate_anthropic_cost(model, input_tokens, output_tokens)
        elif api_provider.lower() == "google" or api_provider.lower() == "gemini":
            cost = self.calculate_gemini_cost(model, input_tokens, output_tokens)
        elif api_provider.lower() == "tavily":
            cost = self.calculate_tavily_cost(operation, request_count)
        elif api_provider.lower() == "perplexity":
            cost = self.calculate_perplexity_cost(operation, request_count)
        else:
            cost = 0.0
            print(f"COST_TRACKER: Provedor desconhecido - {api_provider}")
        
        # Cria registro da chamada
        api_call = ApiCall(
            timestamp=datetime.now().isoformat(),
            api_provider=api_provider,
            model=model,
            operation=operation,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost_usd=cost,
            query_context=query_context[:100] + "..." if len(query_context) > 100 else query_context,
            response_preview=response_preview[:100] + "..." if len(response_preview) > 100 else response_preview
        )
        
        # Adiciona aos registros
        self.current_session_costs.append(api_call)
        self.total_costs[api_provider] += cost
        self.api_calls_count[api_provider] += 1
        
        # Verifica alertas
        self._check_cost_alerts()
        
        # Salva histórico a cada 5 chamadas
        if len(self.current_session_costs) % 5 == 0:
            self.save_cost_history()
        
        return cost
    
    def _check_cost_alerts(self):
        """Verifica se atingiu limites de alerta"""
        session_cost = sum(call.cost_usd for call in self.current_session_costs)
        
        # Alerta de sessão
        if session_cost > self.alert_thresholds["session"]:
            print(f"⚠️ ALERTA DE CUSTO: Sessão atual: ${session_cost:.4f} (limite: ${self.alert_thresholds['session']:.2f})")
        
        # Alerta diário (últimas 24h)
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        daily_calls = [call for call in self.current_session_costs 
                      if datetime.fromisoformat(call.timestamp) > yesterday]
        daily_cost = sum(call.cost_usd for call in daily_calls)
        
        if daily_cost > self.alert_thresholds["daily"]:
            print(f"⚠️ ALERTA DE CUSTO DIÁRIO: ${daily_cost:.4f} (limite: ${self.alert_thresholds['daily']:.2f})")
    
    def get_session_summary(self) -> Dict:
        """Retorna resumo de custos da sessão atual"""
        if not self.current_session_costs:
            return {"total_cost": 0, "calls": 0, "by_provider": {}}
        
        total_cost = sum(call.cost_usd for call in self.current_session_costs)
        by_provider = defaultdict(lambda: {"cost": 0, "calls": 0, "tokens": 0})
        
        for call in self.current_session_costs:
            by_provider[call.api_provider]["cost"] += call.cost_usd
            by_provider[call.api_provider]["calls"] += 1
            by_provider[call.api_provider]["tokens"] += call.total_tokens
        
        return {
            "total_cost": total_cost,
            "total_calls": len(self.current_session_costs),
            "by_provider": dict(by_provider),
            "most_expensive_call": max(self.current_session_costs, key=lambda x: x.cost_usd) if self.current_session_costs else None
        }
    
    def get_detailed_report(self, last_n_calls: int = 10) -> str:
        """Gera relatório detalhado de custos"""
        if not self.current_session_costs:
            return "Nenhuma chamada de API registrada nesta sessão."
        
        summary = self.get_session_summary()
        
        report = f"""
RELATÓRIO DE CUSTOS - SESSÃO ATUAL
{'='*50}

RESUMO GERAL:
   Total gasto: ${summary['total_cost']:.6f} USD
   Chamadas realizadas: {summary['total_calls']}
   
POR PROVEDOR:"""

        for provider, data in summary['by_provider'].items():
            avg_cost = data['cost'] / data['calls'] if data['calls'] > 0 else 0
            report += f"""
   {provider.upper()}: ${data['cost']:.6f} USD ({data['calls']} calls)
   Média/chamada: ${avg_cost:.6f} USD"""

        # TOP 5 chamadas mais caras
        expensive_calls = sorted(self.current_session_costs, key=lambda x: x.cost_usd, reverse=True)[:5]
        if expensive_calls:
            report += f"\n\nTOP 5 CHAMADAS MAIS CARAS:"
            for i, call in enumerate(expensive_calls, 1):
                report += f"""
{i}. ${call.cost_usd:.6f} USD - {call.api_provider} 
   {call.operation}: {call.query_context}"""

        # Últimas N chamadas
        report += f"""

🕐 ÚLTIMAS {min(last_n_calls, len(self.current_session_costs))} CHAMADAS:"""
        
        for call in self.current_session_costs[-last_n_calls:]:
            timestamp = call.timestamp[11:19]
            report += f"""
   {call.api_provider}/{call.model} - ${call.cost_usd:.6f}
   ⏰ {timestamp} | 🔤 {call.total_tokens} tokens | {call.operation}
   📝 {call.query_context}"""

        report += f"""

⚠️ LIMITES DE ALERTA:
   Por sessão: ${self.alert_thresholds['session']:.2f} USD
   Por dia: ${self.alert_thresholds['daily']:.2f} USD
   Por mês: ${self.alert_thresholds['monthly']:.2f} USD

💡 DICAS PARA ECONOMIZAR:
   • Use gpt-4o-mini para tarefas simples (10x mais barato)
   • Claude Haiku para análises rápidas (mais barato que Sonnet)
   • Gemini Flash para operações de volume
   • Cache respostas similares
   • Otimize prompts para reduzir tokens

{'='*50}
"""
        
        return report
    
    def get_pricing_table(self) -> str:
        """Retorna tabela de preços atual das APIs"""
        
        return f"""
TABELA DE PREÇOS ATUAIS (USD por 1K tokens)
{'='*50}

OPENAI:
  gpt-4o               Input: $0.005    Output: $0.015
  gpt-4o-mini         Input: $0.00015  Output: $0.0006  [ECONÔMICO]

ANTHROPIC:
  claude-3-5-sonnet   Input: $0.003    Output: $0.015
  claude-3-5-haiku    Input: $0.001    Output: $0.005   [ECONÔMICO]

GOOGLE:
  gemini-1.5-pro      Input: $0.00125  Output: $0.005
  gemini-1.5-flash    Input: $0.000075 Output: $0.0003  [SUPER ECONÔMICO]

SEARCH APIS:
  Tavily/Perplexity   $0.005 por busca

DICA: Modelos marcados com [ECONÔMICO] são mais eficientes para tarefas similares
"""
    
    def estimate_query_cost(self, query_length: int, complexity: str = "medium") -> Dict[str, float]:
        """Estima custo de uma consulta baseado na complexidade"""
        
        # Estimativas de tokens baseadas na complexidade
        token_estimates = {
            "simple": {"input": 50, "output": 200},
            "medium": {"input": 150, "output": 800},
            "complex": {"input": 300, "output": 1500}
        }
        
        tokens = token_estimates.get(complexity, token_estimates["medium"])
        
        # Ajusta baseado no tamanho da query
        token_multiplier = max(1.0, query_length / 100)
        input_tokens = int(tokens["input"] * token_multiplier)
        output_tokens = int(tokens["output"] * token_multiplier)
        
        estimates = {}
        
        # OpenAI models
        for model in ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]:
            estimates[f"openai_{model}"] = self.calculate_openai_cost(model, input_tokens, output_tokens)
        
        # Anthropic models
        for model in ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"]:
            estimates[f"anthropic_{model.split('-')[2]}"] = self.calculate_anthropic_cost(model, input_tokens, output_tokens)
        
        # Google models
        for model in ["gemini-1.5-pro", "gemini-1.5-flash"]:
            estimates[f"google_{model}"] = self.calculate_gemini_cost(model, input_tokens, output_tokens)
        
        # Web search
        estimates["tavily_search"] = self.calculate_tavily_cost("search", 1)
        estimates["perplexity_search"] = self.calculate_perplexity_cost("search", 1)
        
        return estimates

# Instância global do cost tracker
cost_tracker = CostTracker()

def track_openai_call(model: str, input_tokens: int, output_tokens: int, 
                     operation: str = "completion", query_context: str = "", 
                     response_preview: str = "") -> float:
    """Função helper para rastrear chamadas OpenAI"""
    return cost_tracker.track_api_call(
        api_provider="openai",
        model=model,
        operation=operation,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        query_context=query_context,
        response_preview=response_preview
    )

def track_anthropic_call(model: str, input_tokens: int, output_tokens: int,
                        operation: str = "completion", query_context: str = "",
                        response_preview: str = "") -> float:
    """Função helper para rastrear chamadas Anthropic"""
    return cost_tracker.track_api_call(
        api_provider="anthropic",
        model=model,
        operation=operation,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        query_context=query_context,
        response_preview=response_preview
    )

def track_gemini_call(model: str, input_tokens: int, output_tokens: int,
                     operation: str = "completion", query_context: str = "",
                     response_preview: str = "") -> float:
    """Função helper para rastrear chamadas Gemini"""
    return cost_tracker.track_api_call(
        api_provider="google",
        model=model,
        operation=operation,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        query_context=query_context,
        response_preview=response_preview
    )

def track_tavily_call(operation: str = "search", count: int = 1,
                     query_context: str = "", response_preview: str = "") -> float:
    """Função helper para rastrear chamadas Tavily"""
    return cost_tracker.track_api_call(
        api_provider="tavily",
        model="api",
        operation=operation,
        request_count=count,
        query_context=query_context,
        response_preview=response_preview
    )

def track_perplexity_call(operation: str = "search", count: int = 1,
                         query_context: str = "", response_preview: str = "") -> float:
    """Função helper para rastrear chamadas Perplexity"""
    return cost_tracker.track_api_call(
        api_provider="perplexity",
        model="api",
        operation=operation,
        request_count=count,
        query_context=query_context,
        response_preview=response_preview
    ) 