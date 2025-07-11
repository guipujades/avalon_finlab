#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste do Sistema de Monitoramento de Custos
Demonstra o rastreamento de custos para todas as APIs
"""

import asyncio
from cost_tracker import (
    cost_tracker, 
    track_openai_call, 
    track_anthropic_call, 
    track_gemini_call,
    track_tavily_call,
    track_perplexity_call
)

def test_cost_tracking():
    """Testa o sistema de rastreamento de custos"""
    
    print("="*70)
    print("TESTE DO SISTEMA DE MONITORAMENTO DE CUSTOS")
    print("="*70)
    
    # Simula chamadas para diferentes APIs
    print("\n🧪 SIMULANDO CHAMADAS DE API...")
    
    # OpenAI - Consulta típica
    cost1 = track_openai_call(
        model="gpt-4o",
        input_tokens=150,
        output_tokens=800,
        operation="research_query",
        query_context="como está o mercado hoje?",
        response_preview="O mercado brasileiro apresenta..."
    )
    print(f"✅ OpenAI gpt-4o: ${cost1:.6f}")
    
    # Anthropic Claude - Supervisão
    cost2 = track_anthropic_call(
        model="claude-3-5-sonnet-20241022",
        input_tokens=300,
        output_tokens=400,
        operation="supervision",
        query_context="verificação de coerência",
        response_preview="A análise temporal mostra..."
    )
    print(f"✅ Anthropic Claude: ${cost2:.6f}")
    
    # Google Gemini - Meta-auditoria
    cost3 = track_gemini_call(
        model="gemini-1.5-pro",
        input_tokens=500,
        output_tokens=600,
        operation="meta_audit",
        query_context="auditoria sistêmica",
        response_preview="A eficiência geral do sistema..."
    )
    print(f"✅ Google Gemini: ${cost3:.6f}")
    
    # Tavily - Busca web
    cost4 = track_tavily_call(
        operation="search",
        count=1,
        query_context="pesquisa web: mercado financeiro",
        response_preview="Resultados encontrados: 8 artigos..."
    )
    print(f"✅ Tavily Search: ${cost4:.6f}")
    
    # Perplexity - Busca alternativa
    cost5 = track_perplexity_call(
        operation="search", 
        count=1,
        query_context="busca perplexity: cotações",
        response_preview="Dados atualizados sobre..."
    )
    print(f"✅ Perplexity Search: ${cost5:.6f}")
    
    # OpenAI modelo econômico
    cost6 = track_openai_call(
        model="gpt-4o-mini",
        input_tokens=100,
        output_tokens=300,
        operation="simple_query",
        query_context="consulta simples",
        response_preview="Resposta básica sobre..."
    )
    print(f"✅ OpenAI gpt-4o-mini (econômico): ${cost6:.6f}")
    
    total_cost = cost1 + cost2 + cost3 + cost4 + cost5 + cost6
    
    print(f"\n💰 CUSTO TOTAL SIMULADO: ${total_cost:.6f} USD")
    
    # Exibe resumo da sessão
    print("\n" + "="*70)
    print("RESUMO DA SESSÃO")
    print("="*70)
    
    summary = cost_tracker.get_session_summary()
    print(f"Total gasto: ${summary['total_cost']:.6f} USD")
    print(f"Total de chamadas: {summary['total_calls']}")
    print(f"Custo médio/chamada: ${summary['total_cost']/summary['total_calls']:.6f} USD")
    
    print("\nPOR PROVEDOR:")
    for provider, data in summary['by_provider'].items():
        avg_cost = data['cost'] / data['calls'] if data['calls'] > 0 else 0
        print(f"   {provider.upper()}: ${data['cost']:.6f} ({data['calls']} calls, ~${avg_cost:.6f}/call)")
    
    # Demonstra estimativas
    print("\n" + "="*70)
    print("ESTIMATIVAS DE CUSTO")
    print("="*70)
    
    query_lengths = [20, 100, 200]
    complexities = ["simple", "medium", "complex"]
    
    for length in query_lengths:
        for complexity in complexities:
            estimates = cost_tracker.estimate_query_cost(length, complexity)
            
            print(f"\nConsulta {complexity} (~{length} chars):")
            print(f"   OpenAI gpt-4o: ${estimates.get('openai_gpt-4o', 0):.6f}")
            print(f"   OpenAI gpt-4o-mini: ${estimates.get('openai_gpt-4o-mini', 0):.6f} (economiza {((estimates.get('openai_gpt-4o', 0) - estimates.get('openai_gpt-4o-mini', 0))/estimates.get('openai_gpt-4o', 1)*100):.0f}%)")
            print(f"   Claude Sonnet: ${estimates.get('anthropic_sonnet', 0):.6f}")
            print(f"   Gemini Pro: ${estimates.get('google_gemini-1.5-pro', 0):.6f}")
    
    # Demonstra tabela de preços
    print("\n" + "="*70)
    print("TABELA DE PREÇOS")
    print("="*70)
    print(cost_tracker.get_pricing_table_display())
    
    print("\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
    print("\nO sistema agora rastreia automaticamente:")
    print("   ✅ Custos de todas as APIs")
    print("   ✅ Tokens utilizados") 
    print("   ✅ Operações realizadas")
    print("   ✅ Contexto das consultas")
    print("   ✅ Alertas de limite")
    print("   ✅ Relatórios detalhados")
    print("   ✅ Estimativas de custo")

if __name__ == "__main__":
    test_cost_tracking() 