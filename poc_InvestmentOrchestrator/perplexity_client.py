import os
import json
import aiohttp
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import re


class PerplexityClient:
    """Cliente assíncrono para a API do Perplexity"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.perplexity.ai"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Modelos disponíveis do Perplexity
        self.available_models = {
            "sonar_small": "llama-3.1-sonar-small-128k-online",
            "sonar_large": "llama-3.1-sonar-large-128k-online", 
            "sonar_huge": "llama-3.1-sonar-huge-128k-online"
        }
    
    async def search(
        self,
        query: str,
        model: str = "llama-3.1-sonar-large-128k-online",
        max_tokens: int = 2000,
        temperature: float = 0.2,
        top_p: float = 0.9,
        search_domain_filter: List[str] = None,
        search_recency_filter: str = "month",
        return_images: bool = False,
        return_related_questions: bool = True
    ) -> Dict:
        """
        Executa uma busca no Perplexity com parâmetros configuráveis
        """
        
        if not query.strip():
            return self._create_error_response("Query vazia fornecida")
        
        # Prepara dados da requisição
        data = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "Você é um assistente de pesquisa especializado. Forneça respostas detalhadas e bem estruturadas com informações precisas e atualizadas."
                },
                {
                    "role": "user", 
                    "content": query
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "return_citations": True,
            "return_images": return_images,
            "return_related_questions": return_related_questions
        }
        
        # Adiciona filtros opcionais
        if search_domain_filter:
            data["search_domain_filter"] = search_domain_filter
            
        if search_recency_filter:
            data["search_recency_filter"] = search_recency_filter
        
        try:
            response = await self._make_request(data)
            
            if response["status"] == "success":
                # Processa a resposta com o novo método
                processed_response = self._process_perplexity_response(response["data"])
                
                return {
                    "status": "success",
                    "response": processed_response,
                    "query": query,
                    "model_used": model,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return response
                
        except Exception as e:
            return self._create_error_response(f"Erro na busca: {str(e)}")
    
    def _process_perplexity_response(self, response_data: Dict) -> Dict:
        """Processa resposta do Perplexity"""
        try:
            if "choices" not in response_data or not response_data["choices"]:
                return {
                    "content": "",
                    "citations": [],
                    "key_insights": [],
                    "model_used": response_data.get("model", ""),
                    "related_questions": []
                }
            
            choice = response_data["choices"][0]
            message = choice.get("message", {})
            full_content = message.get("content", "")
            
            # Extrai citações
            citations = []
            if "citations" in choice:
                for citation in choice["citations"]:
                    citations.append({
                        "title": citation.get("title", "Fonte não identificada"),
                        "url": citation.get("url", ""),
                        "snippet": citation.get("text", "")[:1000]  # AUMENTADO: de 500 para 1000
                    })
            
            # NOVO: Melhor extração de insights do conteúdo completo
            key_insights = []
            if full_content:
                # Extrai frases importantes do conteúdo
                sentences = [s.strip() for s in full_content.split('.') if s.strip() and len(s.strip()) > 30]
                
                # Prioriza sentenças que contenham informações importantes
                important_patterns = [
                    r'\d+%', r'\$[\d,]+', r'aumentou', r'diminuiu', r'crescimento', 
                    r'queda', r'alta', r'baixa', r'resultado', r'lucro', r'receita',
                    r'investimento', r'mercado', r'análise', r'previsão', r'expectativa'
                ]
                
                # Ordena sentenças por relevância
                scored_sentences = []
                for sentence in sentences[:20]:  # AUMENTADO: de 10 para 20 sentenças
                    score = 0
                    for pattern in important_patterns:
                        score += len(re.findall(pattern, sentence, re.IGNORECASE))
                    scored_sentences.append((score, sentence))
                
                # Pega as sentenças mais relevantes
                scored_sentences.sort(reverse=True)
                
                # Se há sentenças pontuadas, usa as melhores
                if scored_sentences and scored_sentences[0][0] > 0:
                    key_insights = [sentence for score, sentence in scored_sentences[:8] if score > 0]  # AUMENTADO: de 5 para 8
                
                # Se não há sentenças pontuadas, usa parágrafos completos
                if not key_insights:
                    paragraphs = [p.strip() for p in full_content.split('\n\n') if p.strip() and len(p.strip()) > 50]
                    key_insights = paragraphs[:5]  # Máximo 5 parágrafos
                
                # Se ainda não há insights, usa o conteúdo completo dividido em partes
                if not key_insights and full_content:
                    # Divide em chunks de tamanho razoável
                    chunk_size = 500  # AUMENTADO: de 300 para 500 caracteres
                    chunks = [full_content[i:i+chunk_size] for i in range(0, len(full_content), chunk_size)]
                    key_insights = chunks[:4]  # Máximo 4 chunks
            
            # Questões relacionadas (se disponíveis)
            related_questions = []
            if "related_questions" in choice:
                related_questions = choice["related_questions"][:8]  # AUMENTADO: de 5 para 8
            
            return {
                "content": full_content,  # Conteúdo completo, sem truncamento
                "citations": citations,
                "key_insights": key_insights,
                "model_used": response_data.get("model", ""),
                "related_questions": related_questions,
                "usage": response_data.get("usage", {})
            }
            
        except Exception as e:
            print(f"PERPLEXITY CLIENT: Erro ao processar resposta: {e}")
            return {
                "content": "",
                "citations": [],
                "key_insights": [],
                "model_used": "",
                "related_questions": [],
                "error": str(e)
            }
    
    async def search_simple(self, query: str) -> str:
        """Versão simplificada que retorna apenas o conteúdo principal"""
        result = await self.search(query)
        
        if result["status"] == "success":
            return result["response"]["content"]
        else:
            return f"Erro na busca: {result.get('error', 'Erro desconhecido')}"
    
    def get_available_models(self) -> Dict[str, str]:
        """Retorna modelos disponíveis do Perplexity"""
        return self.available_models.copy()
    
    def _create_error_response(self, error_message: str) -> Dict:
        """Cria uma resposta de erro padronizada"""
        return {
            "status": "error",
            "error": error_message,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _make_request(self, data: Dict) -> Dict:
        """Faz a requisição HTTP para a API do Perplexity"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "status": "success",
                            "data": result
                        }
                    else:
                        error_text = await response.text()
                        return self._create_error_response(f"HTTP {response.status}: {error_text}")
                        
        except asyncio.TimeoutError:
            return self._create_error_response("Timeout na requisição ao Perplexity")
        except Exception as e:
            return self._create_error_response(f"Erro inesperado: {str(e)}")


# Função de conveniência para uso direto
async def search_with_perplexity(api_key: str, query: str, **kwargs) -> Dict:
    """Função de conveniência para busca rápida com Perplexity"""
    client = PerplexityClient(api_key)
    return await client.search(query, **kwargs)


# Exemplo de uso
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    async def test_perplexity():
        api_key = os.getenv("PERPLEXITY_API_KEY")
        
        if not api_key:
            print("PERPLEXITY_API_KEY não encontrada no .env")
            return
        
        client = PerplexityClient(api_key)
        
        # Teste básico
        result = await client.search("Como está o mercado financeiro brasileiro hoje?")
        
        if result["status"] == "success":
            response = result["response"]
            print("Conteúdo:", response["content"][:200] + "...")
            print("Fontes:", len(response["citations"]))
            print("Insights:", len(response["key_insights"]))
        else:
            print("Erro:", result["error"])
    
    # Para testar: asyncio.run(test_perplexity()) 