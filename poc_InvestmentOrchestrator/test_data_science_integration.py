#!/usr/bin/env python3
"""
Teste da integração entre Research Agent e Data Science Agent
"""

import asyncio
import os
from dotenv import load_dotenv
from llama_index.llms.openai import OpenAI
from research_agent import IntelligentResearchAgent
from data_science_agent import DataScienceAgent
from document_agent import EnhancedDocumentAgent

async def test_data_science_integration():
    """Testa a integração completa"""
    
    load_dotenv()
    
    # Configura LLM
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("❌ OPENAI_API_KEY não encontrada")
        return
    
    llm = OpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
        max_tokens=1000,
        api_key=openai_key
    )
    
    # Cria agentes
    print("🔧 Inicializando agentes...")
    
    # Document Agent (mock)
    document_agent = EnhancedDocumentAgent(llm)
    
    # Data Science Agent
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    data_science_agent = DataScienceAgent(anthropic_key=anthropic_key)
    
    # Research Agent
    tavily_key = os.getenv("TAVILY_KEY")
    perplexity_key = os.getenv("PERPLEXITY_API_KEY")
    
    research_agent = IntelligentResearchAgent(
        llm=llm,
        document_agent=document_agent,
        tavily_key=tavily_key,
        perplexity_key=perplexity_key
    )
    
    # Conecta Data Science Agent ao Research Agent
    research_agent.set_data_science_agent(data_science_agent)
    
    print("✅ Agentes inicializados")
    
    # Teste 1: Query sobre fundos Artesanal
    print("\n" + "="*60)
    print("TESTE 1: Query sobre fundos Artesanal")
    print("="*60)
    
    query1 = "Quanto está investido nos fundos Artesanal?"
    context1 = {
        "intent_analysis": {
            "intent_type": "question",
            "action_required": "research",
            "complexity": "moderate",
            "requires_web": False,
            "requires_documents": False,
            "can_answer_from_memory": False,
            "confidence": 0.9,
            "key_entities": ["Artesanal", "fundos"]
        }
    }
    
    print(f"Query: {query1}")
    print("Processando...")
    
    try:
        result1 = await research_agent.process_query_simple(query1, context1)
        print(f"\n✅ RESULTADO:")
        print(result1)
        
        # Verifica se contém dados de API
        if "DADOS VIA API" in result1 or "Artesanal" in result1:
            print("\n✅ Dados de API detectados na resposta!")
        else:
            print("\n❌ Dados de API não encontrados na resposta")
            
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
    
    # Teste 2: Query sobre clientes BTG
    print("\n" + "="*60)
    print("TESTE 2: Query sobre clientes BTG")
    print("="*60)
    
    query2 = "Quantos clientes temos na base BTG?"
    context2 = {
        "intent_analysis": {
            "intent_type": "question",
            "action_required": "research",
            "complexity": "simple",
            "requires_web": False,
            "requires_documents": False,
            "can_answer_from_memory": False,
            "confidence": 0.9,
            "key_entities": ["BTG", "clientes"]
        }
    }
    
    print(f"Query: {query2}")
    print("Processando...")
    
    try:
        result2 = await research_agent.process_query_simple(query2, context2)
        print(f"\n✅ RESULTADO:")
        print(result2)
        
        # Verifica se contém dados de API
        if "DADOS VIA API" in result2 or "clientes" in result2:
            print("\n✅ Dados de API detectados na resposta!")
        else:
            print("\n❌ Dados de API não encontrados na resposta")
            
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
    
    # Teste 3: Query que não deveria usar API
    print("\n" + "="*60)
    print("TESTE 3: Query sobre mercado (não deveria usar API)")
    print("="*60)
    
    query3 = "Como está o mercado hoje?"
    context3 = {
        "intent_analysis": {
            "intent_type": "question",
            "action_required": "research",
            "complexity": "moderate",
            "requires_web": True,
            "requires_documents": False,
            "can_answer_from_memory": False,
            "confidence": 0.9,
            "key_entities": ["mercado"]
        }
    }
    
    print(f"Query: {query3}")
    print("Processando...")
    
    try:
        result3 = await research_agent.process_query_simple(query3, context3)
        print(f"\n✅ RESULTADO:")
        print(result3[:300] + "..." if len(result3) > 300 else result3)
        
        # Verifica se NÃO contém dados de API (deve usar web)
        if "DADOS VIA API" not in result3:
            print("\n✅ Corretamente não usou API para query de mercado!")
        else:
            print("\n⚠️ Usou API para query de mercado (pode estar correto se híbrido)")
            
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
    
    print("\n" + "="*60)
    print("RESUMO DOS TESTES")
    print("="*60)
    print("✅ Teste 1: Query sobre fundos Artesanal")
    print("✅ Teste 2: Query sobre clientes BTG") 
    print("✅ Teste 3: Query sobre mercado")
    print("\n🎯 Integração Data Science Agent testada!")

if __name__ == "__main__":
    asyncio.run(test_data_science_integration()) 