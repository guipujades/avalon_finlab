#!/usr/bin/env python3
"""
Teste do Fluxo Simplificado do Research Agent
Apenas Document Agent + Web Search
"""

import asyncio
from typing import Dict

# Mock classes para simular os agentes
class MockDocumentAgent:
    """Simula o Document Agent para teste"""
    
    async def process_intelligent_request(self, request: Dict) -> Dict:
        """Simula resposta do document agent"""
        query = request.get("query", "")
        
        # Simula diferentes tipos de resposta baseado na query
        if "artesanal" in query.lower() or "fundos" in query.lower():
            return {
                "status": "success",
                "data": {
                    "extracted_information": {
                        "combined_insights": "Encontrados 3 documentos sobre fundos com informações de performance e estratégia de investimento.",
                        "recommendations": [
                            "Analisar performance dos fundos de investimento",
                            "Verificar estratégias de alocação",
                            "Consultar relatórios mensais de performance"
                        ],
                        "relevant_documents": [
                            "fund_performance_2024.pdf",
                            "investment_strategy_report.pdf",
                            "monthly_report_nov2024.pdf"
                        ],
                        "confidence_score": 0.85,
                        "categories": ["investments", "funds", "performance"]
                    }
                }
            }
        elif "mercado" in query.lower() or "bolsa" in query.lower():
            return {
                "status": "success", 
                "data": {
                    "extracted_information": {
                        "combined_insights": "Documentos disponíveis contêm análises básicas de mercado, mas dados em tempo real devem ser obtidos via web.",
                        "recommendations": [
                            "Complementar com dados em tempo real da web",
                            "Verificar tendências nos relatórios arquivados",
                            "Consultar análises técnicas históricas"
                        ],
                        "relevant_documents": [
                            "market_analysis_q3_2024.pdf",
                            "economic_outlook_2024.pdf"
                        ],
                        "confidence_score": 0.4,  # Baixa para forçar complemento com web
                        "categories": ["market", "analysis"]
                    }
                }
            }
        else:
            return {
                "status": "success",
                "data": {
                    "extracted_information": {
                        "combined_insights": "Nenhum documento específico encontrado para esta consulta.",
                        "recommendations": [],
                        "relevant_documents": [],
                        "confidence_score": 0.1,
                        "categories": []
                    }
                }
            }


class TestSimplifiedResearchAgent:
    """Simula Research Agent simplificado para teste"""
    
    def __init__(self):
        self.document_agent = MockDocumentAgent()
    
    async def _mandatory_document_consultation(self, query: str, context: Dict) -> Dict:
        """Consulta obrigatória ao Document Agent"""
        print("RESEARCH AGENT → DOCUMENT AGENT: Iniciando consulta obrigatória")
        
        doc_request = {
            "query": query,
            "context": context,
            "consultation_type": "index_and_suggestions"
        }
        
        doc_response = await self.document_agent.process_intelligent_request(doc_request)
        
        if doc_response and doc_response.get("status") == "success":
            extracted_info = doc_response.get("data", {}).get("extracted_information", {})
            
            response = {
                "available": True,
                "index_summary": extracted_info.get("combined_insights", ""),
                "suggestions": extracted_info.get("recommendations", []),
                "relevant_docs": extracted_info.get("relevant_documents", []),
                "confidence": extracted_info.get("confidence_score", 0.5),
                "categories": extracted_info.get("categories", [])
            }
            
            print(f"✅ Document Agent respondeu:")
            print(f"  📚 Documentos relevantes: {len(response['relevant_docs'])}")
            print(f"  💡 Sugestões: {len(response['suggestions'])}")
            print(f"  🎯 Confiança: {response['confidence']:.1%}")
            
            return response
        else:
            return {
                "available": False,
                "index_summary": "Sem dados disponíveis",
                "suggestions": [],
                "relevant_docs": [],
                "confidence": 0.0
            }
    
    def _decide_strategy_from_document_consultation(self, query: str, doc_response: Dict, context: Dict) -> Dict:
        """Decide estratégia baseada apenas na resposta do Document Agent"""
        print("🤔 Analisando resposta do Document Agent para decidir estratégia...")
        
        has_document_data = doc_response.get("available") and doc_response.get("confidence", 0) > 0.3
        doc_confidence = doc_response.get("confidence", 0)
        
        print(f"  📚 Dados em documentos: {'Sim' if has_document_data else 'Não'} (conf: {doc_confidence:.1%})")
        
        if has_document_data and doc_confidence > 0.7:
            return {
                "name": "documents_only",
                "reasoning": "Documentos locais têm alta relevância",
                "confidence": 0.8
            }
        elif has_document_data and doc_confidence > 0.3:
            return {
                "name": "documents_plus_web",
                "reasoning": "Documentos com confiança média, complementar com web",
                "confidence": 0.6
            }
        else:
            return {
                "name": "web_only",
                "reasoning": "Documentos não têm dados relevantes",
                "confidence": 0.5
            }
    
    async def _execute_simplified_strategy(self, strategy: Dict, query: str, context: Dict,
                                         doc_response: Dict) -> str:
        """Executa a estratégia escolhida (versão simplificada)"""
        strategy_name = strategy["name"]
        
        if strategy_name == "documents_only":
            return doc_response["index_summary"]
        elif strategy_name == "documents_plus_web":
            doc_data = doc_response["index_summary"]
            web_data = f"Dados web simulados para: {query}"
            return f"INFORMAÇÕES DOS DOCUMENTOS:\n{doc_data}\n\nINFORMAÇÕES DA WEB:\n{web_data}"
        else:  # web_only
            return f"Resultado de busca web simulada para: {query}"
    
    async def process_query_simple(self, query: str, context: Dict) -> str:
        """Processa query com fluxo simplificado"""
        print(f"\nRESEARCH AGENT: Query -> {query}")
        
        # CONSULTA DOCUMENT AGENT
        print("\n" + "="*50)
        print("CONSULTA DOCUMENT AGENT")
        print("="*50)
        document_response = await self._mandatory_document_consultation(query, context)
        
        # ANÁLISE E ESTRATÉGIA
        print("\n" + "="*50)
        print("ANÁLISE E ESTRATÉGIA")
        print("="*50)
        strategy = self._decide_strategy_from_document_consultation(
            query, document_response, context
        )
        
        print(f"RESEARCH AGENT: Estratégia -> {strategy['name']}")
        print(f"  Razão: {strategy['reasoning']}")
        
        # EXECUÇÃO
        print("\n" + "="*50)
        print(f"EXECUÇÃO: {strategy['name'].upper()}")
        print("="*50)
        final_response = await self._execute_simplified_strategy(
            strategy, query, context, document_response
        )
        
        return final_response


async def test_simplified_research_flow():
    """Testa o fluxo simplificado do Research Agent"""
    
    print("🧪 TESTE FLUXO SIMPLIFICADO RESEARCH AGENT")
    print("="*60)
    print("✅ Testando apenas:")
    print("   1. Document Agent (índice + sugestões)")
    print("   2. Estratégia baseada nos documentos")
    print("   3. Web search como complemento")
    print("="*60)
    
    agent = TestSimplifiedResearchAgent()
    
    test_queries = [
        {
            "query": "Qual é a performance dos fundos de investimento?",
            "expected_strategy": "documents_only",
            "description": "Query sobre fundos - alta confiança nos documentos"
        },
        {
            "query": "Como está o mercado brasileiro hoje?", 
            "expected_strategy": "documents_plus_web",
            "description": "Query sobre mercado - documentos + web"
        },
        {
            "query": "Análise de uma empresa específica XYZ",
            "expected_strategy": "web_only", 
            "description": "Query sem dados nos documentos - apenas web"
        }
    ]
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n\n🧪 TESTE {i}: {test['description']}")
        print("="*80)
        
        result = await agent.process_query_simple(test["query"], {})
        
        print(f"\n📋 RESULTADO FINAL:")
        print("-" * 40)
        print(result[:200] + "..." if len(result) > 200 else result)
        
        print(f"\n✅ Teste {i} concluído")


if __name__ == "__main__":
    asyncio.run(test_simplified_research_flow()) 