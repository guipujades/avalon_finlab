"""
compatibility_adapter.py - Adaptador para usar o novo Document Agent com código antigo
"""

from pathlib import Path
from typing import Dict, List, Optional
import json
from datetime import datetime

class DocumentAgentCompat:
    """
    Wrapper de compatibilidade para o EnhancedDocumentAgent
    Permite usar o novo agent com código que espera a interface antiga
    """
    
    def __init__(self, enhanced_agent):
        self.agent = enhanced_agent
        # Espelha atributos necessários
        self.llm = enhanced_agent.llm
        self.base_path = enhanced_agent.base_path
        self.registry_path = enhanced_agent.registry_path
        self.registry = enhanced_agent.registry
        
        # Adiciona métodos/atributos que o código antigo pode esperar
        self.processed_media_cache = {}
        self.media_processor = None
        self.external_tools = None
    
    async def scan_documents(self) -> Dict:
        """Adapta o retorno do scan_documents para formato antigo"""
        # Chama o método novo
        result = await self.agent.scan_documents()
        
        # Adiciona campo 'types' que o código antigo espera
        if 'types' not in result:
            # Conta tipos baseado nos documentos
            types = {}
            for doc in self.agent.registry.get("documents", {}).values():
                ext = doc.get("extension", "unknown")
                types[ext] = types.get(ext, 0) + 1
            result['types'] = types
        
        return result
    
    async def search_documents(self, query: str) -> List[Dict]:
        """Mantém compatibilidade com método antigo"""
        return await self.agent.search_documents(query)
    
    async def read_document_content(self, file_path: str) -> str:
        """Proxy para o método do agent novo"""
        return await self.agent.read_document_content(file_path)
    
    async def process_query(self, request: Dict) -> Dict:
        """Adapta process_query antigo para process_intelligent_request novo"""
        # O novo agent usa process_intelligent_request
        if hasattr(self.agent, 'process_intelligent_request'):
            # Adapta o request para o novo formato
            adapted_request = {
                "query": request.get("query", ""),
                "request_id": request.get("request_id", f"req_{datetime.now().timestamp()}"),
                "context": request.get("context", {}),
                "specific_needs": {}
            }
            
            # Chama o novo método
            response = await self.agent.process_intelligent_request(adapted_request)
            
            # Se o novo método retorna formato diferente, adapta de volta
            if response.get("status") == "success":
                # Formato compatível com AgentCommunicationProtocol
                from research_agent import AgentCommunicationProtocol
                
                data = response.get("data", {})
                
                # Tenta extrair informação sintetizada
                synthesis = "Nenhuma informação relevante encontrada."
                if data.get("extracted_information", {}).get("combined_insights"):
                    synthesis = data["extracted_information"]["combined_insights"]
                elif data.get("recommendations", {}).get("assessment"):
                    synthesis = data["recommendations"]["assessment"]
                
                return AgentCommunicationProtocol.create_response(
                    request["request_id"],
                    synthesis,
                    {
                        "sources": [doc["filename"] for doc in data.get("documents_found", {}).get("perfect_matches", [])[:3]],
                        "search_strategy": "intelligent_analysis",
                        "confidence": data.get("metadata", {}).get("confidence", "unknown")
                    }
                )
            else:
                # Erro
                from research_agent import AgentCommunicationProtocol
                return AgentCommunicationProtocol.create_error_response(
                    request["request_id"],
                    response.get("error", "Erro desconhecido")
                )
        else:
            # Fallback para método antigo se existir
            return await self.agent.process_query(request)
    
    def load_registry(self) -> Dict:
        """Proxy para o agent"""
        return self.agent.load_registry()
    
    def save_registry(self):
        """Proxy para o agent"""
        return self.agent.save_registry()
    
    # Métodos específicos de mídia (stubs para compatibilidade)
    async def process_media_file(self, file_name: str) -> Dict:
        """Stub para compatibilidade - retorna erro amigável"""
        return {
            "status": "error",
            "message": "Processamento de mídia não disponível na versão atual. Use o processamento de documentos padrão."
        }
    
    def processar_novos_documentos(self, llm):
        """Stub para compatibilidade"""
        print("⚠️  Método 'processar_novos_documentos' não disponível na versão atual.")
        print("💡 Use o scan_documents() para indexar novos documentos.")
        return None
    
    def consultar_documento(self, doc_name, pergunta, llm, complexa=False):
        """Stub para compatibilidade"""
        return "Método 'consultar_documento' não disponível. Use process_query() para consultas."
    
    # Métodos adicionais que podem ser necessários
    def _count_types(self, documents: Dict) -> Dict:
        """Conta documentos por tipo"""
        return self.agent._count_types(documents) if hasattr(self.agent, '_count_types') else {}
    
    async def get_knowledge_base_overview(self) -> Dict:
        """Proxy se o método existir"""
        if hasattr(self.agent, 'get_knowledge_base_overview'):
            return await self.agent.get_knowledge_base_overview()
        else:
            # Retorna visão básica
            return {
                "total_documents": len(self.registry.get("documents", {})),
                "last_update": self.registry.get("last_scan", "Never"),
                "categories": {},
                "documents_by_type": {},
                "recent_additions": []
            }


def create_compatible_agent(llm, base_path="knowledge_base"):
    """
    Factory function para criar um agent compatível
    
    Uso:
        from compatibility_adapter import create_compatible_agent
        
        # Em vez de:
        # document_agent = EnhancedDocumentAgent(llm)
        
        # Use:
        document_agent = create_compatible_agent(llm)
    """
    try:
        # Tenta importar o novo EnhancedDocumentAgent
        from document_agent import EnhancedDocumentAgent
        
        # Cria o agent novo
        enhanced_agent = EnhancedDocumentAgent(llm, base_path)
        
        # Envolve no adaptador de compatibilidade
        return DocumentAgentCompat(enhanced_agent)
        
    except ImportError:
        # Se não conseguir importar o novo, tenta o antigo
        print("⚠️  Não foi possível importar EnhancedDocumentAgent. Usando versão antiga.")
        from document_agent import DocumentAgent
        return DocumentAgent(llm, base_path)


# Função helper para detectar qual tipo de query está sendo feita
def is_base_local_query(query: str) -> bool:
    """Detecta se é uma query sobre a base local (compatibilidade)"""
    query_lower = query.lower()
    local_indicators = [
        "base local", "base de conhecimento", "documentos disponíveis",
        "o que temos", "o que há", "lista de documentos", "documentos na base"
    ]
    return any(indicator in query_lower for indicator in local_indicators)


# Para testes
if __name__ == "__main__":
    import asyncio
    from llama_index.llms.openai import OpenAI
    
    async def test_compatibility():
        # Testa o adaptador
        llm = OpenAI(model="gpt-4o-mini")
        agent = create_compatible_agent(llm)
        
        # Testa scan
        print("Testando scan_documents...")
        result = await agent.scan_documents()
        print(f"Total: {result['total_documents']}")
        print(f"Tipos: {result.get('types', {})}")
        
        # Testa query
        print("\nTestando process_query...")
        request = {
            "query": "teste",
            "request_id": "test_123",
            "context": {}
        }
        response = await agent.process_query(request)
        print(f"Status: {response.get('status')}")
    
    # asyncio.run(test_compatibility())