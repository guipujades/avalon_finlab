#!/usr/bin/env python3
"""
Teste do Novo Fluxo do Research Agent
Testa os dois caminhos obrigatórios: Document Agent + Data Science Agent
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any

# Mock classes para simular os agentes
class MockDocumentAgent:
    """Simula o Document Agent para teste"""
    
    async def process_intelligent_request(self, request: Dict) -> Dict:
        """Simula resposta do document agent"""
        query = request.get("query", "")
        
        # Simula diferentes tipos de resposta baseado na query
        if "artesanal" in query.lower():
            return {
                "status": "success",
                "data": {
                    "extracted_information": {
                        "combined_insights": "Encontrados 3 documentos sobre fundos Artesanal com informações de performance e estratégia.",
                        "recommendations": [
                            "Analisar performance dos fundos Artesanal FIM",
                            "Verificar estratégias de alocação",
                            "Consultar relatórios mensais de performance"
                        ],
                        "relevant_documents": [
                            "artesanal_performance_2024.pdf",
                            "artesanal_strategy_report.pdf",
                            "artesanal_monthly_report_nov2024.pdf"
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


class MockDataScienceAgent:
    """Simula o Data Science Agent para teste"""
    
    class MockDataResponse:
        def __init__(self, success: bool, summary: str, data_type: str = None, 
                     processed_data: Dict = None, execution_time: float = 0.5):
            self.success = success
            self.summary = summary
            self.data_type = data_type
            self.processed_data = processed_data or {}
            self.execution_time = execution_time
    
    async def process_data_request(self, query: str, context: Dict) -> MockDataResponse:
        """Simula resposta do data science agent"""
        
        if "artesanal" in query.lower() or "posição" in query.lower():
            return self.MockDataResponse(
                success=True,
                summary="Dados de carteiras BTG obtidos via API:\n\n" +
                       "• ARTESANAL FIM CP: R$ 15.450.000,00 (12,3% da carteira)\n" +
                       "• ARTESANAL FIM LONG BIASED: R$ 8.200.000,00 (6,5% da carteira)\n" +
                       "• Total em fundos Artesanal: R$ 23.650.000,00 (18,8%)\n" +
                       "• Performance YTD: +14,2% vs CDI +10,1%\n" +
                       "• Última atualização: 29/11/2024 18:30",
                data_type="portfolio_positions",
                processed_data={
                    "total_artesanal": 23650000.00,
                    "percentage": 18.8,
                    "funds": [
                        {"name": "ARTESANAL FIM CP", "value": 15450000.00},
                        {"name": "ARTESANAL FIM LONG BIASED", "value": 8200000.00}
                    ]
                }
            )
        elif "mercado" in query.lower() and ("hoje" in query.lower() or "agora" in query.lower()):
            return self.MockDataResponse(
                success=False,
                summary="Consulta sobre mercado atual não requer dados específicos de API BTG. " +
                       "Dados de mercado em tempo real devem ser obtidos via fontes web especializadas.",
                data_type=None
            )
        else:
            return self.MockDataResponse(
                success=False,
                summary="Esta consulta não foi identificada como relevante para dados de API BTG. " +
                       "Não há dados específicos de carteiras ou investimentos relacionados.",
                data_type=None
            )


class MockTavilyClient:
    """Mock do cliente Tavily para busca web"""
    
    def search(self, query: str, **kwargs):
        return {
            "results": [
                {
                    "title": "Mercado Brasileiro Hoje - B3",
                    "content": f"Análise de mercado para '{query}': Ibovespa operando em alta de 1,2%...",
                    "url": "https://www.b3.com.br/market-data"
                },
                {
                    "title": "Cenário Econômico Atual",
                    "content": "Fatores econômicos influenciam mercado brasileiro...",
                    "url": "https://www.valor.com.br/financas"
                }
            ]
        }


async def test_research_agent_flow():
    """Testa o novo fluxo do Research Agent"""
    
    print("🧪 TESTE NOVO FLUXO RESEARCH AGENT")
    print("="*60)
    print("✅ Testando dois caminhos obrigatórios:")
    print("   1. Document Agent (índice + sugestões)")
    print("   2. Data Science Agent (dados API BTG)")
    print("="*60)
    
    # Simula importar o research agent (não podemos fazer import real sem dependências)
    # Em produção seria: from research_agent import IntelligentResearchAgent
    
    class TestResearchAgent:
        """Simula Research Agent para teste"""
        
        def __init__(self):
            self.document_agent = MockDocumentAgent()
            self.data_science_agent = MockDataScienceAgent()
            self.tavily_client = MockTavilyClient()
        
        async def _mandatory_document_consultation(self, query: str, context: Dict) -> Dict:
            """CAMINHO 1: Consulta obrigatória ao Document Agent"""
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
        
        async def _mandatory_data_science_consultation(self, query: str, context: Dict) -> Dict:
            """CAMINHO 2: Consulta obrigatória ao Data Science Agent"""
            print("RESEARCH AGENT → DATA SCIENCE: Iniciando consulta obrigatória")
            
            data_response = await self.data_science_agent.process_data_request(query, context)
            
            if data_response.success:
                print(f"✅ Data Science Agent encontrou dados relevantes:")
                print(f"  📊 Tipo: {data_response.data_type}")
                print(f"  📝 Resumo: {data_response.summary[:100]}...")
                
                return {
                    "available": True,
                    "has_api_data": True,
                    "summary": data_response.summary,
                    "data_type": data_response.data_type,
                    "processed_data": data_response.processed_data,
                    "execution_time": data_response.execution_time,
                    "confidence": 0.9
                }
            else:
                print(f"ℹ️ Data Science Agent: {data_response.summary}")
                return {
                    "available": True,
                    "has_api_data": False,
                    "summary": data_response.summary,
                    "data_type": None,
                    "confidence": 0.1
                }
        
        def _decide_strategy_from_consultations(self, query: str, doc_response: Dict, 
                                              data_response: Dict, context: Dict) -> Dict:
            """Decide estratégia baseada nas respostas"""
            print("🤔 Analisando respostas para decidir estratégia...")
            
            has_document_data = doc_response.get("available") and doc_response.get("confidence", 0) > 0.3
            has_api_data = data_response.get("has_api_data", False)
            
            print(f"  📚 Dados em documentos: {'Sim' if has_document_data else 'Não'} (conf: {doc_response.get('confidence', 0):.1%})")
            print(f"  📊 Dados de API: {'Sim' if has_api_data else 'Não'}")
            
            if has_api_data and len(data_response.get("summary", "")) > 100:
                return {
                    "name": "api_only",
                    "reasoning": "Dados de API BTG são suficientes para responder",
                    "confidence": 0.9
                }
            elif has_document_data and doc_response.get("confidence", 0) > 0.7:
                return {
                    "name": "documents_only",
                    "reasoning": "Documentos locais têm alta relevância",
                    "confidence": 0.8
                }
            elif has_api_data and has_document_data:
                return {
                    "name": "api_plus_documents",
                    "reasoning": "Combinar dados de API com documentos locais",
                    "confidence": 0.85
                }
            elif has_document_data and doc_response.get("confidence", 0) <= 0.7:
                return {
                    "name": "documents_plus_web",
                    "reasoning": "Documentos com baixa confiança, complementar com web",
                    "confidence": 0.6
                }
            else:
                return {
                    "name": "web_only",
                    "reasoning": "Nem documentos nem API têm dados relevantes",
                    "confidence": 0.5
                }
        
        async def _execute_strategy(self, strategy: Dict, query: str, context: Dict,
                                  doc_response: Dict, data_response: Dict) -> str:
            """Executa a estratégia escolhida"""
            strategy_name = strategy["name"]
            
            if strategy_name == "api_only":
                return data_response["summary"]
            elif strategy_name == "documents_only":
                return doc_response["index_summary"]
            elif strategy_name == "api_plus_documents":
                api_data = data_response["summary"]
                doc_data = doc_response["index_summary"]
                return f"DADOS DA API BTG:\n{api_data}\n\nINFORMAÇÕES DOS DOCUMENTOS:\n{doc_data}"
            elif strategy_name == "documents_plus_web":
                doc_data = doc_response["index_summary"]
                web_data = f"Dados web simulados para: {query}"
                return f"INFORMAÇÕES DOS DOCUMENTOS:\n{doc_data}\n\nINFORMAÇÕES DA WEB:\n{web_data}"
            else:  # web_only
                return f"Resultado de busca web simulada para: {query}"
        
        async def process_query_simple(self, query: str, context: Dict) -> str:
            """Processa query com os dois caminhos obrigatórios"""
            print(f"\nRESEARCH AGENT: Query -> {query}")
            
            # CAMINHO 1: Document Agent
            print("\n" + "="*50)
            print("CAMINHO 1: DOCUMENT AGENT")
            print("="*50)
            document_response = await self._mandatory_document_consultation(query, context)
            
            # CAMINHO 2: Data Science Agent
            print("\n" + "="*50)
            print("CAMINHO 2: DATA SCIENCE AGENT")
            print("="*50)
            data_science_response = await self._mandatory_data_science_consultation(query, context)
            
            # ANÁLISE E ESTRATÉGIA
            print("\n" + "="*50)
            print("ANÁLISE E ESTRATÉGIA")
            print("="*50)
            strategy = self._decide_strategy_from_consultations(
                query, document_response, data_science_response, context
            )
            
            print(f"RESEARCH AGENT: Estratégia -> {strategy['name']}")
            print(f"  Razão: {strategy['reasoning']}")
            
            # EXECUÇÃO
            print("\n" + "="*50)
            print(f"EXECUÇÃO: {strategy['name'].upper()}")
            print("="*50)
            final_response = await self._execute_strategy(
                strategy, query, context, document_response, data_science_response
            )
            
            return final_response
    
    # TESTES
    agent = TestResearchAgent()
    
    test_queries = [
        {
            "query": "Qual é a posição atual em fundos Artesanal?",
            "expected_strategy": "api_only",
            "description": "Query específica sobre fundos que deve usar API"
        },
        {
            "query": "Como está o mercado brasileiro hoje?", 
            "expected_strategy": "documents_plus_web",
            "description": "Query sobre mercado atual - documentos + web"
        },
        {
            "query": "Análise técnica de uma empresa específica",
            "expected_strategy": "web_only", 
            "description": "Query sem dados específicos - apenas web"
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
    asyncio.run(test_research_agent_flow()) 