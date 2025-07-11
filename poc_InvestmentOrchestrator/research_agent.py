import os
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
from dotenv import load_dotenv
from tavily.client import AsyncTavilyClient
from llama_index.llms.openai import OpenAI
from llama_index.core.agent import FunctionCallingAgentWorker, AgentRunner
from llama_index.core.tools import FunctionTool
from llama_index.core.memory import ChatMemoryBuffer
from collections import defaultdict

# LlamaParse integration
try:
    from llama_parse import LlamaParse
    LLAMA_PARSE_AVAILABLE = True
except ImportError:
    LLAMA_PARSE_AVAILABLE = False

# Smart Query Builder integration
try:
    from smart_query_builder import SmartSearchQueryBuilder
    SMART_QUERY_BUILDER_AVAILABLE = True
except ImportError:
    SMART_QUERY_BUILDER_AVAILABLE = False

# ===== CONFIGURAÇÕES GLOBAIS =====
DOCUMENTS_PATH = "knowledge_base"
DOCUMENT_REGISTRY = "document_registry.json"

def get_current_date():
    """Retorna a data atual formatada em português"""
    now = datetime.now()
    months = [
        "janeiro", "fevereiro", "março", "abril", "maio", "junho",
        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
    ]
    day = now.day
    month = months[now.month - 1]
    year = now.year
    weekdays = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
    weekday = weekdays[now.weekday()]
   
    return f"{weekday}-feira, {day} de {month} de {year}"

def load_system_prompt(file_path, agent_type="research"):
    """Carrega o system prompt de um arquivo txt"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        if agent_type == "research":
            default_prompt = """Você é um assistente de pesquisa inteligente com acesso à web e a uma base de conhecimento local.
Você possui conhecimentos de economia e finanças e está sempre atualizado.
Data atual: {date}

CAPACIDADES:
1. Pesquisar na web usando search_web
2. Consultar base de conhecimento local usando query_knowledge_base
3. Combinar informações de ambas as fontes

PROCESSO:
1. Analise a pergunta do usuário
2. Determine se precisa consultar a base local, a web, ou ambas
3. Para tópicos específicos da empresa/pessoais, sempre consulte a base local primeiro
4. Para informações atuais de mercado, use a web
5. Combine as informações de forma coerente

REGRAS:
- Sempre indique a fonte da informação (web ou base local)
- Priorize a base local para informações proprietárias
- Use a web para dados em tempo real
- Seja transparente sobre as fontes consultadas"""
        else:  # document agent
            default_prompt = """Você é um agente especializado em gerenciar e consultar documentos locais.
Sua função é processar queries sobre a base de conhecimento local e retornar informações relevantes.

CAPACIDADES:
- Listar documentos disponíveis
- Buscar informações específicas em documentos
- Fornecer contexto sobre quando os documentos foram atualizados
- Identificar lacunas no conhecimento

PROCESSO:
1. Receba a query do agente principal
2. Identifique documentos relevantes
3. Extraia informações pertinentes
4. Retorne de forma estruturada

FORMATO DE RESPOSTA:
Sempre retorne informações indicando:
- Fonte (nome do arquivo)
- Data de última atualização
- Relevância para a query
- Conteúdo extraído"""
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(default_prompt)
        
        return default_prompt

# ===== PROTOCOLO DE COMUNICAÇÃO ENTRE AGENTES =====
class AgentCommunicationProtocol:
    """Define o protocolo de comunicação entre agentes"""
    @staticmethod
    def create_request(query: str, context: Dict = None) -> Dict:
        """Cria uma requisição padronizada"""
        return {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "context": context or {},
            "request_id": f"req_{datetime.now().timestamp()}"
        }
    
    @staticmethod
    def create_response(request_id: str, data: Any, metadata: Dict = None) -> Dict:
        """Cria uma resposta padronizada"""
        return {
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "data": data,
            "metadata": metadata or {},
            "status": "success"
        }
    
    @staticmethod
    def create_error_response(request_id: str, error: str) -> Dict:
        """Cria uma resposta de erro padronizada"""
        return {
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "error": error,
            "status": "error"
        }

# ===== ENHANCED LLAMA PARSE INTEGRATION =====
class EnhancedLlamaParseProcessor:
    """Processador avançado usando LlamaParse"""
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("LLAMA_CLOUD_API_KEY")
        self.parser = None
        self.setup_parser()
    
    def setup_parser(self):
        """Configura o parser do LlamaParse"""
        if LLAMA_PARSE_AVAILABLE and self.api_key:
            try:
                self.parser = LlamaParse(
                    api_key=self.api_key,
                    result_type="markdown",
                    verbose=False,
                    language="pt"
                )
            except Exception:
                self.parser = None
    
    async def parse_document(self, file_path: str) -> Dict:
        """Parse avançado de documento com LlamaParse"""
        if not self.parser:
            return await self._basic_parse(file_path)
        
        try:
            documents = await self.parser.aload_data(file_path)
            
            # Extrai conteúdo estruturado
            parsed_content = ""
            for doc in documents:
                parsed_content += doc.text + "\n\n"
            
            # Gera resumo estruturado
            summary = await self._generate_structured_summary(parsed_content)
            
            return {
                "status": "success",
                "content": parsed_content,
                "summary": summary,
                "metadata": {
                    "parser": "llama_parse",
                    "pages": len(documents),
                    "file_path": file_path
                }
            }
            
        except Exception as e:
            return await self._basic_parse(file_path)
    
    async def _basic_parse(self, file_path: str) -> Dict:
        """Parse básico para fallback"""
        file_path = Path(file_path)
        
        if file_path.suffix.lower() == '.txt':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return {
                    "status": "success",
                    "content": content,
                    "summary": content[:500] + "..." if len(content) > 500 else content,
                    "metadata": {"parser": "basic_text", "file_path": str(file_path)}
                }
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e),
                    "metadata": {"parser": "failed", "file_path": str(file_path)}
                }
        else:
            return {
                "status": "error",
                "error": f"Tipo de arquivo não suportado: {file_path.suffix}",
                "metadata": {"parser": "unsupported", "file_path": str(file_path)}
            }
    
    async def _generate_structured_summary(self, content: str) -> Dict:
        """Gera resumo estruturado do conteúdo"""
        # Análise básica de estrutura
        lines = content.split('\n')
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        
        # Detecta seções
        sections = []
        current_section = ""
        
        for line in non_empty_lines[:50]:  # Analisa primeiras 50 linhas
            if line.startswith('#') or line.isupper() or len(line) < 50:
                if current_section:
                    sections.append(current_section)
                current_section = line
            
        return {
            "length": len(content),
            "estimated_reading_time": len(content.split()) // 200,  # ~200 palavras/minuto
            "sections_detected": len(sections),
            "key_sections": sections[:5],
            "summary_preview": content[:300] + "..." if len(content) > 300 else content
        }

# ===== GERENCIADOR DE MEMÓRIA INTELIGENTE =====
class IntelligentMemoryManager:
    """Gerenciador inteligente de memória com capacidades de aprendizado"""
    def __init__(self, memory_file: str, patterns_file: str, llm: OpenAI, document_agent=None):
        self.memory_file = memory_file
        self.patterns_file = patterns_file
        self.llm = llm
        self.document_agent = document_agent
        self.memories = self.load_memories()
        self.patterns = self.load_patterns()
        
    def load_memories(self) -> List[Dict]:
        """Carrega memórias do arquivo"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        return json.loads(content)
            except Exception:
                pass
        return []
    
    def load_patterns(self) -> Dict:
        """Carrega padrões aprendidos"""
        if os.path.exists(self.patterns_file):
            try:
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        return json.loads(content)
            except Exception:
                pass
        return {
            "categories": {},
            "common_questions": defaultdict(int),
            "question_evolution": [],
            "successful_contexts": []
        }
    
    def save_memories(self):
        """Salva memórias no arquivo"""
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.memories, f, ensure_ascii=False, indent=2)
    
    def save_patterns(self):
        """Salva padrões aprendidos"""
        with open(self.patterns_file, 'w', encoding='utf-8') as f:
            patterns_to_save = self.patterns.copy()
            patterns_to_save["common_questions"] = dict(patterns_to_save["common_questions"])
            json.dump(patterns_to_save, f, ensure_ascii=False, indent=2)
    
    async def analyze_question(self, question: str) -> Dict:
        """Analisa a pergunta usando IA para extrair insights"""
        
        entities = self._extract_entities(question)
        recent_docs = await self._check_recent_documents(entities) if self.document_agent else []
        
        analysis_prompt = f"""Analise a seguinte pergunta e forneça uma resposta em JSON:

Pergunta: {question}

Entidades identificadas: {entities}

Documentos recentes na base local:
{json.dumps(recent_docs, ensure_ascii=False)}

Retorne um JSON com:
{{
    "category": "categoria principal (ex: cotação, juros, investimentos, economia, análise_empresa, etc)",
    "entities": ["entidades mencionadas (empresas, produtos, mercados)"],
    "temporal_context": "contexto temporal",
    "intent": "intenção principal",
    "keywords": ["palavras-chave importantes"],
    "needs_local_knowledge": true/false (se há documentos locais relevantes ou se menciona empresas/tópicos específicos),
    "suggested_sources": ["local", "web", "both"] (onde buscar informações),
    "related_documents": ["lista de documentos relevantes da base local"]
}}"""
        
        response = await self.llm.acomplete(analysis_prompt)
        try:
            analysis = json.loads(response.text)
            
            if recent_docs and not analysis.get("needs_local_knowledge"):
                analysis["needs_local_knowledge"] = True
                analysis["suggested_sources"] = ["both"]
                
            if recent_docs and not analysis.get("related_documents"):
                analysis["related_documents"] = recent_docs
                
            return analysis
        except Exception:
            needs_local = any(entity.lower() in question.lower() 
                             for entity in ["petrobras", "petrobrás", "vale", "itaú", "bradesco", "ambev"])
            
            return {
                "category": "análise_empresa" if needs_local else "geral",
                "entities": entities,
                "temporal_context": "atual",
                "intent": "informação",
                "keywords": question.split()[:5],
                "needs_local_knowledge": needs_local or len(recent_docs) > 0,
                "suggested_sources": ["both"] if needs_local or recent_docs else ["web"],
                "related_documents": recent_docs
            }
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extrai entidades (empresas, produtos) do texto"""
        known_companies = [
            "petrobras", "petrobrás", "vale", "itaú", "itau", "bradesco", 
            "ambev", "magazine luiza", "magalu", "b3", "weg", "natura",
            "jbs", "suzano", "gerdau", "embraer", "tim", "vivo", "claro",
            "santander", "caixa", "banco do brasil", "bb", "cielo", "stone"
        ]
        
        entities = []
        text_lower = text.lower()
        
        for company in known_companies:
            if company in text_lower:
                if company == "b3":
                    entities.append("B3")
                elif company == "bb":
                    entities.append("BB")
                elif company in ["petrobrás", "petrobras"]:
                    entities.append("Petrobras")
                elif company == "itaú":
                    entities.append("Itaú")
                else:
                    entities.append(company.title())
        
        words = text.split()
        for word in words:
            if len(word) > 2 and word[0].isupper() and word not in ["Como", "Qual", "Onde", "Quando"]:
                if word not in entities:
                    entities.append(word)
        
        return list(set(entities))
    
    async def _check_recent_documents(self, entities: List[str], hours: int = 48) -> List[str]:
        """Verifica documentos processados recentemente relacionados às entidades"""
        if not self.document_agent or not hasattr(self.document_agent, 'registry'):
            return []
        
        recent_docs = []
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        for filename, info in self.document_agent.registry.get("documents", {}).items():
            try:
                processed_at = datetime.fromisoformat(info.get("processed_at", ""))
                if processed_at < cutoff_time:
                    continue
            except Exception:
                continue
            
            filename_lower = filename.lower()
            doc_related = False
            
            for entity in entities:
                if entity.lower() in filename_lower:
                    doc_related = True
                    break
            
            if not doc_related and hasattr(self.document_agent, 'registry'):
                base_name = Path(filename).stem
                resumos = self.document_agent.registry.get("resumos", {})
                
                if base_name in resumos:
                    resumo = resumos[base_name].lower()
                    for entity in entities:
                        if entity.lower() in resumo:
                            doc_related = True
                            break
                
                if not doc_related:
                    resumo_path = Path("knowledge_base/documentos/relatorios") / f"r_{base_name}.txt"
                    if resumo_path.exists():
                        try:
                            with open(resumo_path, "r", encoding="utf-8") as f:
                                resumo_completo = f.read().lower()
                            for entity in entities:
                                if entity.lower() in resumo_completo:
                                    doc_related = True
                                    break
                        except Exception:
                            pass
            
            if doc_related and filename not in recent_docs:
                recent_docs.append(filename)
        
        return recent_docs
    
    def add_memory(self, question: str, answer: str, analysis: Dict, was_useful: bool = True):
        """Adiciona memória e atualiza padrões"""
        memory = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "question": question,
            "answer": answer,
            "analysis": analysis,
            "usage_count": 0,
            "usefulness_score": 1.0 if was_useful else 0.5
        }
        
        self.memories.append(memory)
        self.save_memories()
        
# ===== AGENTE DE PESQUISA PRINCIPAL =====
class IntelligentResearchAgent:
    """Research Agent inteligente com melhor integração com Document Agent"""
    def __init__(self, llm: OpenAI, document_agent, tavily_key: str = None, perplexity_key: str = None):
        self.llm = llm
        self.document_agent = document_agent
        
        # NOVO: Suporte a múltiplos provedores de busca
        self.web_search_providers = {}
        
        # Configura Tavily se disponível
        if tavily_key:
            try:
                from tavily.client import AsyncTavilyClient
                self.web_search_providers["tavily"] = AsyncTavilyClient(api_key=tavily_key)
                print("RESEARCH AGENT: Cliente Tavily configurado")
            except ImportError:
                print("RESEARCH AGENT: Tavily não disponível (pip install tavily-python)")
        
        # Configura Perplexity se disponível
        if perplexity_key:
            try:
                from perplexity_client import PerplexityClient
                self.web_search_providers["perplexity"] = PerplexityClient(perplexity_key)
                print("RESEARCH AGENT: Cliente Perplexity configurado")
            except ImportError:
                print("RESEARCH AGENT: Perplexity client não encontrado")
        
        # Define provedor padrão
        self.default_web_provider = None
        if "tavily" in self.web_search_providers:
            self.default_web_provider = "tavily"
        elif "perplexity" in self.web_search_providers:
            self.default_web_provider = "perplexity"
        
        # Fallback para compatibilidade
        self.tavily_client = self.web_search_providers.get("tavily")
        
        # Carrega configurações
        from config import get_config
        self.config = get_config()
        self.web_provider_config = self.config["research_agent"]["web_search_providers"]
        self.current_provider = self.web_provider_config.get("default_provider", "tavily")
        
        # Se o provedor padrão não está disponível, usa o primeiro disponível
        if (self.current_provider not in self.web_search_providers and 
            self.web_search_providers):
            self.current_provider = next(iter(self.web_search_providers.keys()))
        
        self.decision_history = []
        self.llama_parse_processor = EnhancedLlamaParseProcessor()
        
        # Sistema de feedback e aprendizado
        self.feedback_memory = self.load_feedback_memory()
        
        # NOVO: Carrega correções críticas salvas
        if "critical_corrections" in self.feedback_memory:
            self.critical_corrections = self.feedback_memory["critical_corrections"]
            if self.critical_corrections:
                print(f"RESEARCH AGENT: Carregou {len(self.critical_corrections)} correções críticas")
        else:
            self.critical_corrections = []
        
        self.query_patterns = {}
        self.failed_queries = []
        
        # NOVO: Sistema inteligente de construção de queries
        if SMART_QUERY_BUILDER_AVAILABLE:
            try:
                self.smart_query_builder = SmartSearchQueryBuilder()
                print(f"RESEARCH AGENT: Smart Query Builder configurado")
                
                # Log de informações sobre as empresas carregadas
                info = self.smart_query_builder.get_companies_info()
                print(f"  - {info['total_companies']} empresas cadastradas")
                print(f"  - {info['total_tickers']} tickers disponíveis")
            except Exception as e:
                print(f"RESEARCH AGENT: Erro ao inicializar Smart Query Builder: {e}")
                self.smart_query_builder = None
        else:
            print("RESEARCH AGENT: Smart Query Builder não disponível")
            self.smart_query_builder = None
        
        # Sistema de decisão
        self.decision_criteria = {
            "use_local_only": {
                "confidence_threshold": 0.8,
                "coverage_threshold": 0.9
            },
            "use_web_only": {
                "local_confidence_below": 0.3,
                "requires_realtime": True
            },
            "use_both": {
                "default": True
            }
        }
    
        print(f"RESEARCH AGENT: Provedor de busca ativo - {self.current_provider}")
        if not self.web_search_providers:
            print("RESEARCH AGENT: ATENÇÃO - Nenhum provedor de busca web configurado!")
        
        # NOVO: Integração com Maestro Agent para otimização dinâmica
        self.maestro_agent = None  # Será definido após a inicialização
        
        # NOVO: Integração com Data Science Agent para dados via APIs
        self.data_science_agent = None  # Será definido após a inicialização
    
    def set_web_provider(self, provider: str):
        """Define o provedor de busca web ativo"""
        if provider in self.web_search_providers:
            self.current_provider = provider
            print(f"RESEARCH AGENT: Provedor alterado para {provider}")
            return True
        else:
            available = list(self.web_search_providers.keys())
            print(f"RESEARCH AGENT: Provedor {provider} não disponível. Disponíveis: {available}")
            return False
    
    def get_available_providers(self) -> List[str]:
        """Retorna lista de provedores de busca disponíveis"""
        return list(self.web_search_providers.keys())
    
    async def perform_web_search(self, query: str, analysis: Dict) -> Dict:
        """Executa busca web usando o provedor ativo"""
        
        if not self.web_search_providers:
            return {
                "error": "Nenhum provedor de busca web configurado",
                "query": query,
                "relevant_findings": [],
                "key_insights": []
            }
        
        provider = self.current_provider
        client = self.web_search_providers.get(provider)
        
        if not client:
            return {
                "error": f"Provedor {provider} não está disponível",
                "query": query,
                "relevant_findings": [],
                "key_insights": []
            }
        
        print(f"RESEARCH AGENT: Executando busca web via {provider.upper()}")
        
        try:
            if provider == "tavily":
                return await self._search_with_tavily(client, query, analysis)
            elif provider == "perplexity":
                return await self._search_with_perplexity(client, query, analysis)
            else:
                return {
                    "error": f"Provedor {provider} não implementado",
                    "query": query,
                    "relevant_findings": [],
                    "key_insights": []
                }
        
        except Exception as e:
            print(f"RESEARCH AGENT: Erro na busca web ({provider}): {e}")
            return {
                "error": f"Erro na busca via {provider}: {str(e)}",
            "query": query,
                "relevant_findings": [],
                "key_insights": []
            }
    
    async def _search_with_tavily(self, client, query: str, analysis: Dict) -> Dict:
        """Executa busca usando Tavily (método original)"""
        
        config = self.web_provider_config["tavily"]
        search_query = self._build_smart_search_query(query, analysis)
        
        print(f"TAVILY: Buscando por '{search_query}'")
        
        try:
            # Configura parâmetros da busca
            search_params = {
                "query": search_query,
                "search_depth": config.get("search_depth", "advanced"),
                "max_results": config.get("max_results", 10),
                "include_answer": True,
                "include_raw_content": True
            }
            
            # Adiciona filtros se configurados
            if config.get("include_domains"):
                search_params["include_domains"] = config["include_domains"]
            if config.get("exclude_domains"):
                search_params["exclude_domains"] = config["exclude_domains"]
            
            results = await client.search(**search_params)
            
            if not results.get("results"):
                return {
                "query": query,
                    "search_query_used": search_query,
                    "relevant_findings": [],
                    "key_insights": ["Nenhum resultado encontrado"],
                    "raw_results": results
                }
            
            # Processa resultados
            relevant_findings = []
            for result in results["results"][:config.get("max_results", 10)]:
                assessment = await self._assess_result_relevance(result, analysis)
                if assessment["relevance_score"] >= config.get("relevance_threshold", 0.5):
                    relevant_findings.append({
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "content": result.get("content", "")[:config.get("max_content_per_result", 500)],
                        "relevance_score": assessment["relevance_score"],
                        "key_points": assessment["key_points"]
                    })
            
            # Extrai insights principais
            key_insights = await self._extract_key_insights(relevant_findings, query, analysis)
            
            return {
                "query": query,
                "search_query_used": search_query,
                "relevant_findings": relevant_findings,
                "key_insights": key_insights,
                "total_results": len(results.get("results", [])),
                "filtered_results": len(relevant_findings),
                "raw_results": results
            }
        
        except Exception as e:
            print(f"TAVILY: Erro na busca: {e}")
            return {
                "error": f"Erro no Tavily: {str(e)}",
                "query": query,
                "relevant_findings": [],
                "key_insights": []
            }
    
    async def _search_with_perplexity(self, client, query: str, analysis: Dict) -> Dict:
        """Executa busca usando Perplexity"""
        
        config = self.web_provider_config["perplexity"]
        
        # Adapta a query para o Perplexity
        perplexity_query = self._build_perplexity_query(query, analysis)
        
        print(f"PERPLEXITY: Buscando por '{perplexity_query}'")
        
        try:
            # Configura parâmetros específicos do Perplexity
            search_params = {
                "query": perplexity_query,
                "model": config.get("model", "llama-3.1-sonar-large-128k-online"),
                "max_tokens": config.get("max_tokens", 2000),  # AUMENTADO
                "temperature": config.get("temperature", 0.2),
                "top_p": config.get("top_p", 0.9),
                "search_domain_filter": config.get("search_domain_filter", []),
                "search_recency_filter": config.get("search_recency_filter", "month"),
                "return_images": config.get("return_images", False),
                "return_related_questions": config.get("return_related_questions", True)
            }
            
            result = await client.search(**search_params)
            
            if result["status"] != "success":
                return {
                    "error": result.get("error", "Erro desconhecido no Perplexity"),
                "query": query,
                    "relevant_findings": [],
                    "key_insights": []
                }
            
            response_data = result["response"]
            
            # Converte formato do Perplexity para formato padrão
            relevant_findings = []
            for citation in response_data.get("citations", []):
                relevant_findings.append({
                    "title": citation.get("title", "Fonte"),
                    "url": citation.get("url", ""),
                    "content": citation.get("snippet", ""),  # REMOVIDO: truncamento [:300]
                    "relevance_score": 0.8,  # Perplexity já filtra relevância
                    "key_points": [citation.get("snippet", "")]  # REMOVIDO: truncamento [:100]
                })
            
            # NOVO: Processa o conteúdo completo do Perplexity sem truncar
            full_content = response_data.get("content", "")
            key_insights = []
            
            # Se há conteúdo principal, usa ele como insights
            if full_content:
                # Divide o conteúdo em parágrafos significativos
                paragraphs = [p.strip() for p in full_content.split('\n') if p.strip() and len(p.strip()) > 20]
                
                # Se há parágrafos estruturados, usa eles
                if paragraphs:
                    # Numera os insights para melhor organização
                    for i, paragraph in enumerate(paragraphs[:10], 1):  # Máximo 10 insights
                        if not paragraph.startswith(f"{i}."):
                            key_insights.append(f"{i}. {paragraph}")
                        else:
                            key_insights.append(paragraph)
                else:
                    # Se não há estrutura de parágrafo, usa o conteúdo completo
                    key_insights = [full_content]
            
            # Se não há insights do conteúdo, usa os insights pré-extraídos
            if not key_insights:
                key_insights = response_data.get("key_insights", [])
            
            return {
                "query": query,
                "search_query_used": perplexity_query,
                "relevant_findings": relevant_findings,
                "key_insights": key_insights,
                "total_results": len(response_data.get("citations", [])),
                "filtered_results": len(relevant_findings),
                "perplexity_content": full_content,  # Conteúdo completo disponível
                "related_questions": response_data.get("related_questions", []),
                "model_used": response_data.get("model_used", ""),
                "raw_results": result
            }
        
        except Exception as e:
            print(f"PERPLEXITY: Erro na busca: {e}")
            return {
                "error": f"Erro no Perplexity: {str(e)}",
                "query": query,
                "relevant_findings": [],
                "key_insights": []
            }
    
    def _build_perplexity_query(self, original_query: str, analysis: Dict) -> str:
        """Constrói query otimizada para o Perplexity considerando orientações do Maestro E correções críticas"""
        
        # NOVO: Usa SmartSearchQueryBuilder primeiro se disponível
        if self.smart_query_builder:
            try:
                enhanced_query = self.smart_query_builder.build_smart_search_query(
                    original_query, 
                    analysis
                )
                
                # Se SmartQueryBuilder fez otimizações, usa como base
                if base_query != original_query:
                    query_parts = [base_query]
                    print(f"RESEARCH AGENT: Query Perplexity baseada no Smart Builder")
                    print(f"RESEARCH AGENT: Query Perplexity baseada no Smart Builder")
                else:
                    query_parts = [original_query]
            except Exception as e:
                print(f"RESEARCH AGENT: Erro no Smart Query Builder para Perplexity: {e}")
                query_parts = [original_query]
        else:
            # Inicia com a query original
            query_parts = [original_query]
        
        # CRITICAL: Aplica correções críticas ANTES de outras orientações
        if analysis.get("information_requirements", {}).get("force_current_data"):
            print(f"RESEARCH AGENT: CORREÇÃO CRÍTICA - Forçando dados atuais específicos")
            current_date = datetime.now()
            current_year = current_date.year
            current_month = current_date.strftime("%B %Y")
            
            # Remove termos problemáticos se especificados
            avoid_terms = analysis.get("critical_avoid_terms", [])
            if avoid_terms:
                for term in avoid_terms:
                    for i, part in enumerate(query_parts):
                        if term in part:
                            query_parts[i] = part.replace(term, "")
                print(f"RESEARCH AGENT: Removidos termos problemáticos: {avoid_terms}")
            
            # Adiciona termos específicos para dados atuais
            query_parts.extend([
                f"dados atuais {current_year}",
                "cotação hoje",
                "fechamento atual"
            ])
            
            # Se é erro específico do Ibovespa
            if analysis.get("validation_required") == "ibovespa_current_value":
                query_parts.extend([
                    f"Ibovespa {current_month}",
                    "B3 hoje",
                    "pontos atuais",
                    "valor presente"
                ])
                print(f"RESEARCH AGENT: Forçando busca específica para Ibovespa atual")
        
        # CORRIGIDO: Aplica orientações do Maestro de forma mais efetiva
        maestro_guidance = analysis.get("maestro_guidance", {})
        if maestro_guidance:
            focus_points = maestro_guidance.get("focus_points", [])
            include_elements = maestro_guidance.get("include_elements", [])
            
            print(f"RESEARCH AGENT: Aplicando orientações específicas do Maestro")
            
            # NOVO: Detecta quando Maestro pede especificamente mercado brasileiro
            needs_brazilian_market = False
            for focus in focus_points:
                focus_lower = focus.lower()
                if any(term in focus_lower for term in ["mercado brasileiro", "ibovespa", "brasil", "b3", "ações em alta/baixa"]):
                    needs_brazilian_market = True
                    print(f"  Detectado pedido de mercado brasileiro: '{focus}'")
                    break
            
            # Se Maestro pede mercado brasileiro, adiciona termos específicos
            if needs_brazilian_market:
                brazilian_terms = ["Ibovespa", "B3", "mercado brasileiro", "ações Brasil", "Bovespa"]
                query_parts.extend(brazilian_terms)
                print(f"  Adicionando termos brasileiros: {', '.join(brazilian_terms)}")
            
            # Analisa pontos de foco para outras orientações
            for focus in focus_points:
                focus_lower = focus.lower()
                
                # Se menciona mercados internacionais (mas não exclui Brasil)
                if any(market in focus_lower for market in ["s&p 500", "nasdaq", "dow jones"]) and not needs_brazilian_market:
                    query_parts.append("S&P500 Nasdaq Dow Jones mercados mundiais")
                
                # Se menciona dados numéricos específicos
                if "dados numéricos" in focus_lower or "variação percentual" in focus_lower:
                    query_parts.append("cotação variação percentual pontos")
                
                # Se menciona fatores econômicos
                if "fatores econômicos" in focus_lower or "política" in focus_lower:
                    query_parts.append("economia política impactos")
                
                # Se menciona câmbio
                if "câmbio" in focus_lower or "dólar" in focus_lower:
                    query_parts.append("dólar real câmbio")
                
                # Se menciona setores
                if "setores" in focus_lower or "tecnologia" in focus_lower:
                    query_parts.append("setores tecnologia commodities")
            
            # NOVO: Processa elementos a incluir
            for element in include_elements:
                element_lower = element.lower()
                if "b3" in element_lower or "valor econômico" in element_lower:
                    # Se pede fontes brasileiras específicas
                    if "mercado brasileiro" not in " ".join(query_parts).lower():
                        query_parts.append("mercado brasileiro B3")
                        print(f"  Adicionando por fonte solicitada: mercado brasileiro B3")
        
        # Adiciona contexto temporal se relevante
        query_classification = analysis.get("query_classification", {})
        if query_classification.get("temporal_aspect") == "current":
            if "hoje" not in original_query.lower() and "atual" not in original_query.lower():
                query_parts.append("informações atuais")
        
        final_query = " ".join(query_parts)
        
        # Log para debug das orientações aplicadas
        if maestro_guidance or analysis.get("information_requirements", {}).get("force_current_data"):
            print(f"RESEARCH AGENT: Query final aplicando orientações + correções")
            print(f"  Original: {original_query}")
            print(f"  Final: {final_query}")
            if needs_brazilian_market:
                print(f"  ✓ Mercado brasileiro incluído conforme orientação")
            if analysis.get("information_requirements", {}).get("force_current_data"):
                print(f"  ✓ Correção crítica aplicada - dados atuais forçados")
        
        return final_query
    
    def _build_smart_search_query(self, original_query: str, analysis: Dict) -> str:
        """Constrói query inteligente para busca web baseada no contexto"""
        
        # NOVO: Usa SmartSearchQueryBuilder se disponível
        if self.smart_query_builder:
            try:
                enhanced_query = self.smart_query_builder.build_smart_search_query(
                    original_query, 
                    analysis
                )
                
                # Log da otimização quando há mudança significativa
                if enhanced_query != original_query:
                    print(f"RESEARCH AGENT: Query otimizada via Smart Builder")
                    print(f"  Original: {original_query}")
                    print(f"  Otimizada: {enhanced_query}")
                
                return enhanced_query
                
            except Exception as e:
                print(f"RESEARCH AGENT: Erro no Smart Query Builder, usando método padrão: {e}")
                # Fallback para método original
                pass
        
        # Método original como fallback
        query_lower = original_query.lower()
        
        # Detecção de contexto financeiro/mercado
        market_keywords = ["mercado", "bolsa", "ações", "índice", "bovespa", "nasdaq", "dow jones", "s&p"]
        financial_keywords = ["petrobras", "vale", "itau", "bradesco", "dólar", "real", "inflação", "juros"]
        temporal_keywords = ["hoje", "agora", "atual", "atualmente", "recente"]
        
        is_market_query = any(keyword in query_lower for keyword in market_keywords)
        is_financial_query = any(keyword in query_lower for keyword in financial_keywords)
        is_temporal_query = any(keyword in query_lower for keyword in temporal_keywords)
        
        # Para queries de mercado, constrói busca específica
        if is_market_query and is_temporal_query:
            if "brasil" in query_lower or "bovespa" in query_lower:
                return "Bovespa hoje índice ações Brasil mercado financeiro"
            elif "mundo" in query_lower or "global" in query_lower:
                return "stock market today global indices S&P500 Nasdaq Dow Jones"
            else:
                # Query genérica de mercado - prioriza mercado brasileiro
                return "mercado ações hoje Brasil Bovespa Ibovespa índices financeiro"
        
        # Para queries financeiras específicas
        if is_financial_query and is_temporal_query:
            companies = []
            if "petrobras" in query_lower:
                companies.append("Petrobras PETR4")
            if "vale" in query_lower:
                companies.append("Vale VALE3")
            if "itau" in query_lower:
                companies.append("Itaú ITUB4")
            if "bradesco" in query_lower:
                companies.append("Bradesco BBDC4")
            
            if companies:
                return f"{ ' '.join(companies)} cotação preço ação hoje"
            
            if "dólar" in query_lower:
                return "dólar hoje cotação real USD BRL"
        
        # Para outras queries temporais, adiciona contexto de data atual
        if is_temporal_query:
            current_year = datetime.now().year
            return f"{original_query.replace('hoje', '').replace('agora', '').strip()} {current_year}"
        
        # Para queries gerais, usa os termos sugeridos pela análise
        search_terms = analysis.get("search_hints", {}).get("must_include", [])
        if search_terms:
            return " ".join(search_terms)
        
        # Fallback: query original
        return original_query
    
    def receive_maestro_feedback(self, query: str, response: str, feedback_data: Dict):
        """Recebe feedback do Maestro e aplica aprendizado específico para problemas críticos"""
        
        print(f"MAESTRO → RESEARCH AGENT: Feedback recebido para '{query[:30]}...'")
        
        combined_score = feedback_data.get("combined_score", 5)
        user_comments = feedback_data.get("user_feedback", {}).get("comments", "")
        
        # Log do feedback
        print(f"RESEARCH AGENT: Score recebido: {combined_score}/10")
        if user_comments:
            print(f"RESEARCH AGENT: Comentários: {user_comments[:100]}")
        
        # NOVO: Processa feedback crítico independentemente do Maestro
        if combined_score <= 2:  # Feedback muito ruim
            self._process_critical_feedback(query, response, user_comments)
        
        # Salva no histórico independente
        feedback_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "query": query,
            "answer": response,
            "score": combined_score,
            "user_comments": user_comments,
            "analysis": self._analyze_feedback_for_learning(query, user_comments)
        }
        
        # Garante que feedback_memory existe
        if not hasattr(self, 'feedback_memory'):
            self.feedback_memory = self.load_feedback_memory()
        
        # Adiciona ao histórico
        if "query_feedback" not in self.feedback_memory:
            self.feedback_memory["query_feedback"] = []
        
        self.feedback_memory["query_feedback"].append(feedback_entry)
        
        # Mantém apenas últimos 50 feedbacks
        if len(self.feedback_memory["query_feedback"]) > 50:
            self.feedback_memory["query_feedback"] = self.feedback_memory["query_feedback"][-50:]
        
        # Salva no arquivo
        self.save_feedback_memory()
        
        print(f"RESEARCH AGENT: Feedback salvo no sistema independente")
    
    def _process_critical_feedback(self, query: str, response: str, user_comments: str):
        """Processa feedback crítico para evitar repetir erros graves"""
        
        comments_lower = user_comments.lower()
        query_lower = query.lower()
        
        # CRÍTICO: Informações desatualizadas
        if any(word in comments_lower for word in ["desatualizada", "erro", "incorreto", "errado", "crítico"]):
            print(f"RESEARCH AGENT: ERRO CRÍTICO detectado - processando correção imediata")
            
            # Identifica o problema específico
            problem_type = "outdated_data"
            if "ibov" in comments_lower or "137" in user_comments or "139" in user_comments:
                problem_type = "ibovespa_data_error"
            
            # Cria regra de correção específica
            correction_rule = {
                "query_pattern": query_lower,
                "problem_type": problem_type,
                "user_feedback": user_comments,
                "timestamp": datetime.now().isoformat(),
                "correction_action": "force_fresh_data_search",
                "avoid_terms": self._extract_problematic_terms(response),
                "priority": "critical"
            }
            
            # Salva regra de correção
            if not hasattr(self, 'critical_corrections'):
                self.critical_corrections = []
            
            self.critical_corrections.append(correction_rule)
            
            # Mantém apenas últimas 20 correções críticas
            if len(self.critical_corrections) > 20:
                self.critical_corrections = self.critical_corrections[-20:]
            
            print(f"RESEARCH AGENT: Regra de correção criada - {problem_type}")
            
    def _extract_problematic_terms(self, response: str) -> List[str]:
        """Extrai termos problemáticos da resposta que causaram erro"""
        problematic = []
        
        # Detecta números que podem estar errados
        import re
        numbers = re.findall(r'\d{3,}', response)  # Números com 3+ dígitos
        for num in numbers:
            if "139" in num:  # Específico para Ibovespa incorreto
                problematic.append(f"139{num[3:]}")
        
        # Detecta frases de máximas históricas
        if "máxima histórica" in response.lower():
            problematic.append("máxima histórica")
        if "ultrapassando" in response.lower():
            problematic.append("ultrapassando")
            
        return problematic
    
    def _analyze_feedback_for_learning(self, query: str, user_comments: str) -> Dict:
        """Analisa feedback para extrair aprendizados específicos"""
        
        analysis = {
            "query_type": "market_query" if "mercado" in query.lower() else "general",
            "feedback_type": "critical" if any(word in user_comments.lower() 
                                              for word in ["erro", "errado", "crítico", "desatualizada"]) else "regular",
            "improvement_needed": [],
            "specific_issues": []
        }
        
        comments_lower = user_comments.lower()
        
        if "desatualizada" in comments_lower or "incorret" in comments_lower:
            analysis["improvement_needed"].append("data_accuracy")
            analysis["specific_issues"].append("outdated_information")
        
        if "ibov" in comments_lower:
            analysis["specific_issues"].append("ibovespa_data_error")
            
        if "137" in user_comments and "139" in user_comments:
            analysis["specific_issues"].append("wrong_index_value")
        
        return analysis
    
    def load_feedback_memory(self) -> Dict:
        """Carrega memória de feedback independente"""
        feedback_file = "research_agent_feedback.json"
        if os.path.exists(feedback_file):
            try:
                with open(feedback_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                        print(f"RESEARCH AGENT: Carregou {len(data.get('query_feedback', []))} feedbacks históricos")
                        return data
            except Exception as e:
                print(f"RESEARCH AGENT: Erro ao carregar feedback: {e}")
        
        return {
            "query_feedback": [],
            "critical_corrections": [],
            "learned_patterns": {}
        }
    
    def save_feedback_memory(self):
        """Salva memória de feedback independente"""
        feedback_file = "research_agent_feedback.json"
        
        # Garante que critical_corrections existe
        if not hasattr(self, 'critical_corrections'):
            self.critical_corrections = []
        
        save_data = {
            "query_feedback": self.feedback_memory.get("query_feedback", []),
            "critical_corrections": getattr(self, 'critical_corrections', []),
            "learned_patterns": self.feedback_memory.get("learned_patterns", {}),
            "last_updated": datetime.now().isoformat()
        }
        
        try:
            with open(feedback_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            print(f"RESEARCH AGENT: Feedback salvo - {len(save_data['query_feedback'])} entradas")
        except Exception as e:
            print(f"RESEARCH AGENT: Erro ao salvar feedback: {e}")
    
    def apply_learned_improvements(self, query: str, analysis: Dict) -> Dict:
        """Aplica melhorias aprendidas do feedback - DUPLA: Maestro + Research Agent"""
        
        # Garante estrutura básica
        if "search_hints" not in analysis:
            analysis["search_hints"] = {"must_include": [], "should_include": [], "date_range": None}
        if "must_include" not in analysis["search_hints"]:
            analysis["search_hints"]["must_include"] = []
        if "information_requirements" not in analysis:
            analysis["information_requirements"] = {}
        
        # 1. PRIORIDADES DO MAESTRO (orientações gerais)
        maestro_guidance = analysis.get("maestro_guidance", {})
        if maestro_guidance:
            focus_points = maestro_guidance.get("focus_points", [])
            
            # Se Maestro orienta sobre mercado brasileiro, adiciona termos
            for focus in focus_points:
                if any(term in focus.lower() for term in ["mercado brasileiro", "ibovespa", "brasil", "b3"]):
                    analysis["search_hints"]["must_include"].extend([
                        "Ibovespa", "B3", "mercado brasileiro", "ações Brasil"
                    ])
                    print(f"RESEARCH AGENT: Aplicando orientação do Maestro - mercado brasileiro")
                    break
        
        # 2. CORREÇÕES CRÍTICAS DO RESEARCH AGENT (erros específicos)
        query_lower = query.lower()
        
        # Carrega correções críticas se existirem
        if hasattr(self, 'critical_corrections'):
            for correction in self.critical_corrections:
                # Verifica se a correção se aplica a esta query
                if correction["query_pattern"] in query_lower:
                    print(f"RESEARCH AGENT: CORREÇÃO CRÍTICA aplicada - {correction['problem_type']}")
                    
                    if correction["correction_action"] == "force_fresh_data_search":
                        # Força busca com termos mais específicos para dados atuais
                        analysis["search_hints"]["must_include"].extend([
                            "hoje", "atual", "tempo real", "data atual"
                        ])
                        
                        # Adiciona avisos para evitar termos problemáticos
                        avoid_terms = correction.get("avoid_terms", [])
                        if avoid_terms:
                            analysis["critical_avoid_terms"] = avoid_terms
                            print(f"RESEARCH AGENT: Evitando termos problemáticos: {avoid_terms}")
                        
                        # Força alta prioridade para dados atualizados
                        analysis["information_requirements"]["force_current_data"] = True
                        analysis["information_requirements"]["needs_realtime_data"] = True
                        
                        print(f"RESEARCH AGENT: Forçando busca de dados atuais para evitar repetir erro")
                        break
        
        # 3. VERIFICA FEEDBACK HISTÓRICO PARA PADRÕES
        if hasattr(self, 'feedback_memory') and self.feedback_memory:
            recent_feedback = self.feedback_memory.get("query_feedback", [])
            
            # Procura por feedback ruim similar
            for feedback in recent_feedback[-10:]:  # Últimos 10 feedbacks
                if (feedback.get("score", 5) <= 2 and  # Score muito ruim
                    query_lower in feedback.get("query", "").lower()):
                    
                    issues = feedback.get("analysis", {}).get("specific_issues", [])
                    if "ibovespa_data_error" in issues or "wrong_index_value" in issues:
                        print(f"RESEARCH AGENT: Detectado histórico de erro de dados do Ibovespa")
                        
                        # Força nova busca com termos específicos
                        analysis["search_hints"]["must_include"].extend([
                            "cotação atual", "fechamento", f"Ibovespa {datetime.now().strftime('%Y')}"
                        ])
                        
                        # Adiciona aviso específico para validar dados
                        analysis["validation_required"] = "ibovespa_current_value"
                        analysis["information_requirements"]["validate_index_data"] = True
                        
                        print(f"RESEARCH AGENT: Aplicando correção específica para dados do Ibovespa")
                        break
        
        return analysis
    
    async def analyze_query(self, query: str) -> Dict:
        """Análise aprofundada da query para determinar estratégia"""
        
        analysis_prompt = f"""Analise esta query e determine a melhor estratégia de busca.\n\nQUERY: {query}\n\nRetorne um JSON detalhado com:\n{{\n    "query_classification": {\n        "type": "factual/analytical/comparative/exploratory",
        "domain": "área principal (finance/macro/company/market/general)",
        "complexity": "simple/moderate/complex",
        "temporal_aspect": "historical/current/future/timeless"
    },\n    "information_requirements": {\n        "needs_realtime_data": true/false,
        "needs_historical_context": true/false,
        "needs_proprietary_data": true/false,
        "needs_multiple_perspectives": true/false,
        "needs_quantitative_data": true/false
    },\n    "source_preferences": {\n        "local_relevance": "probabilidade de ter na base local (0-1)",
        "web_necessity": "necessidade de busca web (0-1)",
        "source_priority": "local_first/web_first/parallel"
    },\n    "expected_content_types": [\n        "relatórios", "dados de mercado", "análises", "notícias", etc
    ],\n    "key_entities": ["empresas, produtos, conceitos mencionados"],
    "search_hints": {\n        "must_include": ["termos essenciais"],
        "should_include": ["termos adicionais"],
        "date_range": "período específico ou null"
    }\n}}"""
        
        try:
            response = await self.llm.acomplete(analysis_prompt)
            analysis = json.loads(response.text)
            
            # APLICA MELHORIAS APRENDIDAS
            analysis = self.apply_learned_improvements(query, analysis)
            
            return analysis
        except Exception as e:
            print(f"[RESEARCH AGENT] Erro na análise da query: {e}")
            # Fallback com melhorias aprendidas aplicadas
            basic_analysis = self._basic_query_classification(query)
            return self.apply_learned_improvements(query, basic_analysis)
    
    def _basic_query_classification(self, query: str) -> Dict:
        """Classificação básica quando LLM falha"""
        query_lower = query.lower()
        
        return {
            "query_classification": {
                "type": "factual",
                "domain": "general",
                "complexity": "simple",
                "temporal_aspect": "current"
            },
            "information_requirements": {
                "needs_realtime_data": "preço" in query_lower or "cotação" in query_lower,
                "needs_historical_context": "histórico" in query_lower,
                "needs_proprietary_data": False,
                "needs_multiple_perspectives": True,
                "needs_quantitative_data": any(term in query_lower for term in ["dados", "números", "valor"])
            },
            "source_preferences": {
                "local_relevance": 0.5,
                "web_necessity": 0.5,
                "source_priority": "parallel"
            },
            "expected_content_types": ["geral"],
            "key_entities": [],
            "search_hints": {
                "must_include": query.split()[:3],
                "should_include": [],
                "date_range": None
            }
        }
    
    async def consult_document_agent(self, query: str, analysis: Dict) -> Dict:
        """Consulta inteligente ao Document Agent"""
        
        request = {
            "query": query,
            "request_id": f"research_{datetime.now().timestamp()}",
            "context": {
                "query_analysis": analysis,
                "source": "research_agent"
            },
            "specific_needs": {
                "extract_information": analysis["information_requirements"].get("needs_quantitative_data", False),
                "priority_categories": self._map_domain_to_categories(analysis.get("query_classification", {}).get("domain", "general"))
            }
        }
        
        doc_response = await self.document_agent.process_intelligent_request(request)
        return doc_response
    
    def _map_domain_to_categories(self, domain: str) -> List[str]:
        """Mapeia domínio da query para categorias de documentos"""
        domain_mapping = {
            "finance": ["financial_reports", "market_data", "company_specific"],
            "macro": ["macroeconomic", "regulatory", "sector_analysis"],
            "company": ["company_specific", "financial_reports", "news_updates"],
            "market": ["market_data", "research_analysis", "sector_analysis"],
            "general": ["general", "educational", "news_updates"]
        }
        
        return domain_mapping.get(domain, ["general"])
    
    async def _assess_result_relevance(self, result: Dict, analysis: Dict) -> Dict:
        """Avalia relevância de um resultado web"""
        
        assessment_prompt = f"""Avalie a relevância deste resultado para a query.\n\nANÁLISE DA QUERY:\n{json.dumps(analysis, ensure_ascii=False, indent=2)}\n\nRESULTADO WEB:\nTítulo: {result.get('title', '')}\nConteúdo: {result.get('content', '')[:500]}\n\nRetorne JSON com:\n{{\n    "score": 0.0-1.0 (relevância),\n    "key_points": ["pontos principais relevantes"],
    "reason": "justificativa da pontuação"
}}\n"""
        
        try:
            response = await self.llm.acomplete(assessment_prompt)
            return json.loads(response.text)
        except Exception:
            return {
                "score": 0.5,
                "key_points": ["Conteúdo potencialmente relevante"],
                "reason": "Avaliação automática"
            }
    
    async def _extract_key_insights(self, findings: List[Dict], query: str, analysis: Dict = None) -> List[str]:
        """Extrai insights principais dos resultados aplicando melhorias aprendidas"""
        
        combined_content = "\n\n".join([
            f"Fonte: {f['title']}\n{f['content'][:300]}"
            for f in findings[:5]
        ])
        
        # NOVO: Constrói prompt baseado nos requirements aprendidos
        base_prompt = f"""Extraia os insights principais para responder:\n\nQUERY: {query}\n\nCONTEÚDO DOS RESULTADOS:\n{combined_content}"""
        
        # NOVO: Aplica requirements específicos
        requirements = []
        if analysis and analysis.get("response_requirements"):
            for req in analysis["response_requirements"]:
                if req == "include_data_collection_time":
                    requirements.append("IMPORTANTE: Inclua SEMPRE a data e horário atuais da consulta no formato 'Data da consulta: [dia/mês/ano] às [hora]'")
                elif req == "include_source_details":
                    requirements.append("IMPORTANTE: Mencione as fontes específicas das informações")
                    
        # NOVO: Aplica template de resposta se existir
        if analysis and analysis.get("response_template"):
            template = analysis["response_template"]
            for format_req in template.get("format_requirements", []):
                if format_req["type"] == "timestamp":
                    current_time = datetime.now()
                    date_str = current_time.strftime("%d/%m/%Y")
                    time_str = current_time.strftime("%H:%M")
                    requirements.append(f"OBRIGATÓRIO: Inclua no final de cada insight: 'Data da consulta: {date_str} às {time_str}'")
                elif format_req["type"] == "sources":
                    requirements.append("OBRIGATÓRIO: Para cada informação, mencione a fonte")
        
        if requirements:
            base_prompt += f"\n\nREQUISITOS ESPECIAIS:\n" + "\n".join(requirements)
        
        base_prompt += "\n\nListe os 3-5 insights mais importantes, cada um em uma linha numerada."
        
        try:
            response = await self.llm.acomplete(base_prompt)
            insights = response.text.strip().split('\n')
            
            # NOVO: Aplica formatação adicional se necessário
            if analysis and analysis.get("response_requirements"):
                insights = self._apply_post_processing(insights, analysis["response_requirements"])
            
            return insights
        except Exception as e:
            print(f"[RESEARCH AGENT] Erro na extração de insights: {e}")
            return ["Insights não puderam ser extraídos"]
    
    def _apply_post_processing(self, insights: List[str], requirements: List[str]) -> List[str]:
        """Aplica pós-processamento aos insights baseado nos requirements"""
        
        processed_insights = []
        current_time = datetime.now()
        date_time_str = current_time.strftime("%d/%m/%Y às %H:%M")
        
        for insight in insights:
            if not insight.strip():
                continue
                
            processed_insight = insight.strip()
            
            # Adiciona timestamp se necessário
            if "include_data_collection_time" in requirements:
                if "data da consulta" not in processed_insight.lower():
                    processed_insight += f" (Data da consulta: {date_time_str})"
            
            processed_insights.append(processed_insight)
        
        return processed_insights
    
    def make_source_decision(self, doc_response: Dict, query_analysis: Dict) -> Dict:
        """Decide se usa apenas documentos locais, web ou ambos"""
        
        decision = {
            "strategy": "both",
            "reasoning": "",
            "confidence": 0.0,
            "specific_actions": []
        }
        
        if doc_response.get("status") == "success":
            doc_data = doc_response.get("data", {})
            recommendations = doc_data.get("recommendations", {})
            confidence = recommendations.get("confidence_level", "baixa")
            
            confidence_map = {
                "alta": 0.9,
                "média-alta": 0.7,
                "média": 0.5,
                "baixa": 0.3
            }
            
            doc_confidence = confidence_map.get(confidence, 0.5)
            perfect_matches = len(doc_data.get("documents_found", {}).get("perfect_matches", []))
            
            if doc_confidence >= 0.8 and perfect_matches >= 2:
                decision["strategy"] = "local_only"
                decision["reasoning"] = "Base local tem cobertura excelente"
                decision["confidence"] = doc_confidence
                decision["specific_actions"] = [
                    f"Analisar em profundidade os {perfect_matches} documentos perfeitos"
                ]
                
            elif doc_confidence >= 0.5:
                decision["strategy"] = "web_complement"
                decision["reasoning"] = "Base local boa, mas web pode complementar"
                decision["confidence"] = doc_confidence
                decision["specific_actions"] = [
                    "Usar documentos locais como base",
                    "Buscar na web informações sobre: " +
                    ", ".join(recommendations.get("information_gaps", [])[:3])
                ]
                
            else:
                decision["strategy"] = "both"
                decision["reasoning"] = "Base local limitada, necessário busca ampla"
                decision["confidence"] = 0.5
                decision["specific_actions"] = [
                    "Busca web prioritária",
                    "Complementar com documentos locais disponíveis"
                ]
        
        if query_analysis.get("information_requirements", {}).get("needs_realtime_data", False):
            if decision["strategy"] == "local_only":
                decision["strategy"] = "web_complement"
                decision["reasoning"] += " + dados em tempo real necessários"
                decision["specific_actions"].append("Buscar dados atualizados na web")
        
        self.decision_history.append({
            "timestamp": datetime.now().isoformat(),
            "query": query_analysis,
            "decision": decision
        })
        
        return decision
    
    async def deep_analyze_documents(self, doc_ids: List[str], query: str) -> Dict:
        """Análise profunda de documentos específicos"""
        
        extraction_request = {
            "query": query,
            "request_id": f"deep_analysis_{datetime.now().timestamp()}",
            "document_ids": doc_ids,
            "extraction_type": "comprehensive"
        }
        
        extracted = await self.document_agent.extract_specific_information(doc_ids, query)
        return extracted
    
    async def synthesize_response(self, 
                                query: str,
                                query_analysis: Dict,
                                doc_response: Dict,
                                web_results: Optional[Dict],
                                decision: Dict) -> str:
        """Sintetiza resposta final combinando todas as fontes"""
        
        synthesis_parts = []
        
        if doc_response.get("status") == "success":
            doc_data = doc_response.get("data", {})
            
            if doc_data.get("extracted_information"):
                synthesis_parts.append({
                    "source": "Base de Conhecimento Local",
                    "content": doc_data["extracted_information"].get("combined_insights", ""),
                    "confidence": "alta",
                    "documents": [
                        doc["document"] 
                        for doc in doc_data["extracted_information"].get("documents_analyzed", [])
                    ]
                })
        
        if web_results and web_results.get("key_insights"):
            synthesis_parts.append({
                "source": "Pesquisa Web",
                "content": "\n".join(web_results["key_insights"]),
                "confidence": "média",
                "sources": web_results.get("sources", [])[:3]
            })
        
        synthesis_prompt = f"""Crie uma resposta completa e coerente para a pergunta do usuário.\n\nPERGUNTA ORIGINAL: {query}\n\nANÁLISE DA QUERY:\nTipo: {query_analysis.get('query_classification', {}).get('type', 'factual')}\nDomínio: {query_analysis.get('query_classification', {}).get('domain', 'general')}\nComplexidade: {query_analysis.get('query_classification', {}).get('complexity', 'moderate')}\n\nESTRATÉGIA UTILIZADA:\n{decision['strategy']} - {decision['reasoning']}\n\nINFORMAÇÕES COLETADAS:\n{json.dumps(synthesis_parts, ensure_ascii=False, indent=2)}\n\nDIRETRIZES PARA RESPOSTA:\n1. Responda diretamente à pergunta\n2. Use informações de maior confiança como base\n3. Mencione as fontes (local/web) quando relevante\n4. Seja claro sobre limitações ou incertezas\n5. Forneça contexto quando necessário\n6. Se houver dados quantitativos, destaque-os\n7. Conclua com insights acionáveis quando aplicável\n\nCrie uma resposta bem estruturada e informativa."""
        
        try:
            response = await self.llm.acomplete(synthesis_prompt)
            
            final_response = response.text
            
            if decision["strategy"] != "web_only":
                docs_used = []
                if doc_response.get("status") == "success":
                    doc_data = doc_response.get("data", {})
                    for doc in doc_data.get("documents_found", {}).get("perfect_matches", [])[:3]:
                        docs_used.append(doc["filename"])
                
                if docs_used:
                    final_response += f"\n\n*Documentos consultados:* {', '.join(docs_used)}"
            
            if web_results and web_results.get("sources"):
                final_response += f"\n\n*Fontes web consultadas:* {len(web_results['sources'])} fontes"
            
            return final_response
            
        except Exception as e:
            return f"Erro ao sintetizar resposta: {str(e)}"
    
    async def process_query(self, query: str) -> Dict:
        """Processa query completa com decisão inteligente"""
        
        result = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "analysis": None,
            "decision": None,
            "response": None,
            "metadata": {}
        }
        
        try:
            query_analysis = await self.analyze_query(query)
            result["analysis"] = query_analysis
            
            doc_response = await self.consult_document_agent(query, query_analysis)
            
            decision = self.make_source_decision(doc_response, query_analysis)
            result["decision"] = decision
            
            web_results = None
            
            if decision["strategy"] in ["web_only", "both", "web_complement"]:
                web_results = await self.perform_web_search(query, query_analysis)
            
            if decision["strategy"] == "local_only" and doc_response.get("status") == "success":
                doc_data = doc_response.get("data", {})
                perfect_matches = doc_data.get("documents_found", {}).get("perfect_matches", [])
                
                if perfect_matches and decision.get("specific_actions"):
                    doc_ids = [doc["document_id"] for doc in perfect_matches[:3]]
                    deep_analysis = await self.deep_analyze_documents(doc_ids, query)
                    
                    if "data" in doc_response:
                        doc_response["data"]["extracted_information"] = deep_analysis
            
            final_response = await self.synthesize_response(
                query,
                query_analysis,
                doc_response,
                web_results,
                decision
            )
            
            result["response"] = final_response
            result["metadata"] = {
                "doc_sources": len(doc_response.get("data", {}).get("documents_found", {}).get("perfect_matches", [])),
                "web_sources": len(web_results.get("sources", [])) if web_results else 0,
                "strategy_used": decision["strategy"],
                "confidence": decision["confidence"]
            }
            
            return result
            
        except Exception as e:
            result["response"] = f"Erro no processamento: {str(e)}"
            result["metadata"]["error"] = str(e)
            return result
    
    async def process_query_simple(self, query: str, context: Dict) -> str:
        """
        Versão simplificada do processamento com CONSULTA OBRIGATÓRIA AO DOCUMENT AGENT
        """
        try:
            print(f"\nRESEARCH AGENT: Iniciando processamento simplificado")
            print(f"Query: {query}")
            
            # ============= CONSULTA OBRIGATÓRIA AO DOCUMENT AGENT =============
            print("\n" + "="*60)
            print("CONSULTA OBRIGATÓRIA AO DOCUMENT AGENT")
            print("="*60)
            
            document_response = await self._mandatory_document_consultation(query, context)
            
            # ============= ANÁLISE E ESTRATÉGIA =============
            print("\n" + "="*60)
            print("ANÁLISE: Definindo estratégia baseada na consulta")
            print("="*60)
            
            strategy = self._decide_strategy_from_document_consultation(query, document_response, context)
            
            print(f"RESEARCH AGENT: Estratégia escolhida -> {strategy['name']}")
            print(f"  Razão: {strategy['reasoning']}")
            
            # ============= EXECUÇÃO DA ESTRATÉGIA =============
            print(f"\n" + "="*60)
            print(f"EXECUÇÃO: {strategy['name'].upper()}")
            print("="*60)
            
            final_response = await self._execute_simplified_strategy(
                strategy, query, context, document_response
            )
            
            # ============= ORIENTAÇÕES DO MAESTRO (SE DISPONÍVEL) =============
            if context.get("maestro_guidance"):
                print("\nRESEARCH AGENT: Aplicando orientações do Maestro")
                final_response = self.apply_maestro_guidance(final_response, context["maestro_guidance"])
            
            return final_response
            
        except Exception as e:
            print(f"RESEARCH AGENT: Erro interno no processamento: {e}")
            return f"Erro no processamento: {str(e)}"

    def _decide_strategy_from_document_consultation(self, query: str, doc_response: Dict, context: Dict) -> Dict:
        """
        Decide a estratégia baseada apenas na resposta do Document Agent
        """
        print("🤔 Analisando resposta do Document Agent para decidir estratégia...")
        
        # Verifica disponibilidade de dados nos documentos
        has_document_data = doc_response.get("available") and doc_response.get("confidence", 0) > 0.3
        doc_confidence = doc_response.get("confidence", 0)
        
        print(f"  📚 Dados em documentos: {'Sim' if has_document_data else 'Não'} (conf: {doc_confidence:.1%})")
        
        # PRIORIDADE 1: Se tem bons dados em documentos (alta confiança), usa apenas eles
        if has_document_data and doc_confidence > 0.7:
            return {
                "name": "documents_only", 
                "reasoning": "Documentos locais têm alta relevância",
                "confidence": 0.8,
                "primary_source": "documents"
            }
        
        # PRIORIDADE 2: Se tem dados em documentos com confiança média, complementa com web
        elif has_document_data and doc_confidence > 0.3:
            return {
                "name": "documents_plus_web",
                "reasoning": "Documentos com confiança média, complementar com web",
                "confidence": 0.6,
                "primary_source": "documents",
                "secondary_source": "web"
            }
        
        # PRIORIDADE 3: Se não tem dados relevantes nos documentos, usa apenas web
        else:
            return {
                "name": "web_only",
                "reasoning": "Documentos não têm dados relevantes",
                "confidence": 0.5,
                "primary_source": "web",
                "secondary_source": None
            }

    async def _execute_simplified_strategy(self, strategy: Dict, query: str, context: Dict,
                                         doc_response: Dict) -> str:
        """
        Executa a estratégia escolhida (versão simplificada)
        """
        strategy_name = strategy["name"]
        
        if strategy_name == "documents_only":
            return doc_response["index_summary"]
        
        elif strategy_name == "documents_plus_web":
            # Documentos + Web
            doc_data = doc_response["index_summary"]
            web_data = await self.execute_web_research(query, context)
            
            combined = f"INFORMAÇÕES DOS DOCUMENTOS:\n{doc_data}\n\n"
            combined += f"INFORMAÇÕES ADICIONAIS DA WEB:\n{web_data}"
            
            return combined
        
        else:  # web_only
            return await self.execute_web_research(query, context)
    
    async def _mandatory_document_consultation(self, query: str, context: Dict) -> Dict:
        """
        CAMINHO 1: Consulta obrigatória ao Document Agent
        Retorna: índice, sugestões e dados disponíveis
        """
        print("RESEARCH AGENT → DOCUMENT AGENT: Iniciando consulta obrigatória")
        
        try:
            if not self.document_agent:
                print("❌ Document Agent não disponível")
                return {
                    "available": False,
                    "index_summary": "Document Agent não configurado",
                    "suggestions": [],
                    "relevant_docs": [],
                    "confidence": 0.0
                }
            
            # Cria request estruturado
            doc_request = {
                "query": query,
                "request_id": f"doc_consultation_{datetime.now().timestamp()}",
                "context": context,
                "consultation_type": "index_and_suggestions"
            }
            
            # Consulta o Document Agent
            print("📋 Solicitando índice da base de documentos...")
            doc_response = await self.document_agent.process_intelligent_request(doc_request)
            
            if doc_response and doc_response.get("status") == "success":
                extracted_info = doc_response.get("data", {}).get("extracted_information", {})
                
                response = {
                    "available": True,
                    "index_summary": extracted_info.get("combined_insights", "Documentos disponíveis"),
                    "suggestions": extracted_info.get("recommendations", []),
                    "relevant_docs": extracted_info.get("relevant_documents", []),
                    "confidence": extracted_info.get("confidence_score", 0.5),
                    "categories": extracted_info.get("categories", []),
                    "raw_response": doc_response
                }
                
                print(f"✅ Document Agent respondeu:")
                print(f"  📚 Documentos relevantes: {len(response['relevant_docs'])}")
                print(f"  💡 Sugestões: {len(response['suggestions'])}")
                print(f"  🎯 Confiança: {response['confidence']:.1%}")
                
                if response['suggestions']:
                    print(f"  📝 Principais sugestões:")
                    for i, suggestion in enumerate(response['suggestions'][:3], 1):
                        print(f"    {i}. {suggestion}")
                
                return response
            else:
                print("⚠️ Document Agent não retornou dados válidos")
                return {
                    "available": False,
                    "index_summary": "Sem dados disponíveis nos documentos",
                    "suggestions": [],
                    "relevant_docs": [],
                    "confidence": 0.0
                }
                
        except Exception as e:
            print(f"❌ Erro na consulta ao Document Agent: {e}")
            return {
                "available": False,
                "index_summary": f"Erro na consulta: {str(e)}",
                "suggestions": [],
                "relevant_docs": [],
                "confidence": 0.0,
                "error": str(e)
            }

    async def _mandatory_data_science_consultation(self, query: str, context: Dict) -> Dict:
        """
        CAMINHO 2: Consulta obrigatória ao Data Science Agent
        Retorna: dados de API BTG se relevantes
        """
        print("RESEARCH AGENT → DATA SCIENCE: Iniciando consulta obrigatória")
        
        try:
            if not hasattr(self, 'data_science_agent') or not self.data_science_agent:
                print("❌ Data Science Agent não disponível")
                return {
                    "available": False,
                    "has_api_data": False,
                    "summary": "Data Science Agent não configurado",
                    "data_type": None,
                    "confidence": 0.0
                }
            
            # Consulta o Data Science Agent
            print("🔍 Verificando relevância para dados de API BTG...")
            data_response = await self.data_science_agent.process_data_request(query, context)
            
            if data_response.success:
                print(f"✅ Data Science Agent encontrou dados relevantes:")
                print(f"  📊 Tipo: {data_response.data_type}")
                print(f"  📝 Resumo: {data_response.summary[:100]}...")
                print(f"  ⏱️ Tempo de execução: {data_response.execution_time:.2f}s")
                
                return {
                    "available": True,
                    "has_api_data": True,
                    "summary": data_response.summary,
                    "data_type": data_response.data_type,
                    "processed_data": data_response.processed_data,
                    "execution_time": data_response.execution_time,
                    "confidence": 0.9,  # Alta confiança quando há dados de API
                    "raw_response": data_response
                }
            else:
                print(f"ℹ️ Data Science Agent: {data_response.summary}")
                return {
                    "available": True,
                    "has_api_data": False,
                    "summary": data_response.summary,
                    "data_type": None,
                    "confidence": 0.1,
                    "reasoning": "Consulta não requer dados de API BTG"
                }
                
        except Exception as e:
            print(f"❌ Erro na consulta ao Data Science Agent: {e}")
            return {
                "available": False,
                "has_api_data": False,
                "summary": f"Erro na consulta: {str(e)}",
                "data_type": None,
                "confidence": 0.0,
                "error": str(e)
            }

    def _decide_strategy_from_consultations(self, query: str, doc_response: Dict, 
                                          data_response: Dict, context: Dict) -> Dict:
        """
        Decide a estratégia baseada nas respostas dos dois agentes
        """
        print("🤔 Analisando respostas para decidir estratégia...")
        
        # Verifica disponibilidade de dados
        has_document_data = doc_response.get("available") and doc_response.get("confidence", 0) > 0.3
        has_api_data = data_response.get("has_api_data", False)
        
        print(f"  📚 Dados em documentos: {'Sim' if has_document_data else 'Não'} (conf: {doc_response.get('confidence', 0):.1%})")
        print(f"  📊 Dados de API: {'Sim' if has_api_data else 'Não'}")
        
        # PRIORIDADE 1: Se tem dados de API suficientes, usa apenas eles
        if has_api_data and len(data_response.get("summary", "")) > 100:
            return {
                "name": "api_only",
                "reasoning": "Dados de API BTG são suficientes para responder",
                "confidence": 0.9,
                "primary_source": "data_science",
                "secondary_source": None
            }
        
        # PRIORIDADE 2: Se tem bons dados em documentos, usa apenas eles
        if has_document_data and doc_response.get("confidence", 0) > 0.7:
            return {
                "name": "documents_only", 
                "reasoning": "Documentos locais têm alta relevância",
                "confidence": 0.8,
                "primary_source": "documents",
                "secondary_source": None
            }
        
        # PRIORIDADE 3: Se tem dados de API + documentos, combina
        if has_api_data and has_document_data:
            return {
                "name": "api_plus_documents",
                "reasoning": "Combinar dados de API com documentos locais",
                "confidence": 0.85,
                "primary_source": "data_science",
                "secondary_source": "documents"
            }
        
        # PRIORIDADE 4: Se tem só dados de API parciais, complementa com web
        if has_api_data:
            return {
                "name": "api_plus_web",
                "reasoning": "Dados de API parciais, complementar com web",
                "confidence": 0.7,
                "primary_source": "data_science", 
                "secondary_source": "web"
            }
        
        # PRIORIDADE 5: Se tem só documentos com baixa confiança, complementa com web
        if has_document_data:
            return {
                "name": "documents_plus_web",
                "reasoning": "Documentos com baixa confiança, complementar com web",
                "confidence": 0.6,
                "primary_source": "documents",
                "secondary_source": "web"
            }
        
        # FALLBACK: Busca web
        return {
            "name": "web_only",
            "reasoning": "Nem documentos nem API têm dados relevantes",
            "confidence": 0.5,
            "primary_source": "web",
            "secondary_source": None
        }

    async def _execute_strategy(self, strategy: Dict, query: str, context: Dict,
                              doc_response: Dict, data_response: Dict) -> str:
        """
        Executa a estratégia escolhida
        """
        strategy_name = strategy["name"]
        
        if strategy_name == "api_only":
            return data_response["summary"]
        
        elif strategy_name == "documents_only":
            return doc_response["index_summary"]
        
        elif strategy_name == "api_plus_documents":
            api_data = data_response["summary"]
            doc_data = doc_response["index_summary"]
            
            combined = f"DADOS DA API BTG:\n{api_data}\n\n"
            combined += f"INFORMAÇÕES DOS DOCUMENTOS:\n{doc_data}"
            
            return combined
        
        elif strategy_name == "api_plus_web":
            # API + Web
            api_data = data_response["summary"]
            web_data = await self.execute_web_research(query, context)
            
            combined = f"DADOS DA API BTG:\n{api_data}\n\n"
            combined += f"INFORMAÇÕES ADICIONAIS DA WEB:\n{web_data}"
            
            return combined
        
        elif strategy_name == "documents_plus_web":
            # Documentos + Web
            doc_data = doc_response["index_summary"]
            web_data = await self.execute_web_research(query, context)
            
            combined = f"INFORMAÇÕES DOS DOCUMENTOS:\n{doc_data}\n\n"
            combined += f"INFORMAÇÕES ADICIONAIS DA WEB:\n{web_data}"
            
            return combined
        
        else:  # web_only
            return await self.execute_web_research(query, context)
    
    async def execute_web_research(self, query: str, context: Dict) -> str:
        """
        Executa pesquisa focada na web
        """
        print("RESEARCH AGENT: Iniciando pesquisa web")
        
        try:
            # Verifica se tavily_client está disponível
            if not hasattr(self, 'tavily_client') or not self.tavily_client:
                return "Erro: Cliente Tavily não foi inicializado. Verifique a TAVILY_KEY no arquivo .env"
            
            # Cria análise básica
            basic_analysis = {
                "query_classification": {
                    "type": "factual",
                    "domain": "market" if any(word in query.lower() for word in ["mercado", "bolsa"]) else "general",
                    "complexity": "simple",
                    "temporal_aspect": "current"
                },
                "search_hints": {
                    "must_include": query.split()[:3],
                    "should_include": [],
                    "date_range": None
                }
            }
            
            # Executa busca web
            web_results = await self.perform_web_search(query, basic_analysis)
            
            if web_results.get("status") == "success":
                content = web_results.get("content", "")
                sources = web_results.get("sources", [])
                
                # Formata resposta
                response = content
                if sources:
                    response += "\n\nFontes consultadas:\n"
                    for i, source in enumerate(sources[:3], 1):
                        response += f"{i}. {source.get('title', 'Fonte')}: {source.get('url', '')}\n"
                
                return response
            else:
                error_msg = web_results.get("error", "Erro desconhecido na busca web")
                return f"Erro na pesquisa web: {error_msg}"
                
        except Exception as e:
            print(f"RESEARCH AGENT: Erro na pesquisa web: {e}")
            return f"Erro na pesquisa web: {str(e)}"
    
    def apply_maestro_guidance(self, response: str, guidance: Dict) -> str:
        """Aplica orientações do Maestro para melhorar a resposta"""
        print("RESEARCH AGENT: Aplicando orientações do Maestro na resposta")
        
        try:
            # Se a resposta é muito básica, não aplica processamento complexo
            if len(response) < 50:
                return response
            
            enhanced_response = response
            focus_points = guidance.get("focus_points", [])
            include_elements = guidance.get("include_elements", [])
            avoid_points = guidance.get("avoid_points", [])
            
            # NOVO: Verifica se a resposta está seguindo os pontos de foco
            missing_focus = []
            for focus in focus_points:
                focus_lower = focus.lower()
                response_lower = response.lower()
                
                # Verifica mercados internacionais
                if any(market in focus_lower for market in ["s&p 500", "nasdaq", "dow jones", "panorama geral"]):
                    if not any(market in response_lower for market in ["s&p", "nasdaq", "dow", "estados unidos", "eua"]):
                        missing_focus.append("mercados_internacionais")
                
                # Verifica dados numéricos
                if "dados numéricos" in focus_lower or "variação percentual" in focus_lower:
                    if not any(char.isdigit() for char in response):
                        missing_focus.append("dados_numericos")
                
                # Verifica fatores econômicos
                if "fatores econômicos" in focus_lower:
                    if not any(word in response_lower for word in ["economia", "política", "fator"]):
                        missing_focus.append("fatores_economicos")
            
            # NOVO: Adiciona avisos se pontos importantes estão faltando
            if missing_focus:
                print(f"RESEARCH AGENT: Detectados pontos em falta: {missing_focus}")
                
                if "mercados_internacionais" in missing_focus:
                    enhanced_response += "\n\n[AVISO: Para uma análise mais completa, consulte também mercados internacionais como S&P 500, Nasdaq e Dow Jones]"
                
                if "dados_numericos" in missing_focus:
                    enhanced_response += "\n\n[AVISO: Dados numéricos específicos podem variar - consulte fontes em tempo real]"
                
                if "fatores_economicos" in missing_focus:
                    enhanced_response += "\n\n[AVISO: Considere também fatores macroeconômicos e políticos que podem impactar o mercado]"
            
            # Adiciona elementos sugeridos se não estão presentes
            for element in include_elements:
                element_lower = element.lower()
                if element_lower not in response.lower():
                    if "dados numéricos" in element_lower and not any(char.isdigit() for char in response):
                        enhanced_response += "\n\n[Nota: Dados específicos podem variar - consulte fontes atualizadas]"
                    elif "fonte" in element_lower and "fonte" not in response.lower():
                        enhanced_response += "\n\n[Fontes: Informações baseadas em pesquisa web atual]"
                    elif "mercados" in element_lower and "s&p" not in response.lower():
                        enhanced_response += "\n\n[Complemento: Para visão global, considere também S&P 500, Nasdaq e mercados asiáticos]"
            
            # Aplica tom sugerido se necessário
            tone = guidance.get("tone_suggestion", "")
            if tone == "technical" and not any(word in response for word in ["índice", "variação", "pontos"]):
                enhanced_response = enhanced_response.replace("está", "encontra-se")
                enhanced_response = enhanced_response.replace("subiu", "apresentou alta")
                enhanced_response = enhanced_response.replace("caiu", "registrou baixa")
            
            # NOVO: Verifica pontos a evitar mais rigorosamente
            for avoid in avoid_points:
                avoid_lower = avoid.lower()
                if "genérica" in avoid_lower or "vago" in avoid_lower:
                    # Se a resposta é muito genérica (poucas palavras, poucos números)
                    word_count = len(response.split())
                    number_count = len([word for word in response.split() if any(char.isdigit() for char in word)])
                    
                    if word_count < 100 or number_count < 3:
                        enhanced_response += "\n\n[MAESTRO: Esta resposta pode estar muito genérica. Considere buscar informações mais específicas]"
                
                if "estrutura exata" in avoid_lower:
                    # Adiciona variação na estrutura
                    if enhanced_response.startswith("1."):
                        enhanced_response = enhanced_response.replace("1. Here are", "Principais destaques:", 1)
            
            if enhanced_response != response:
                print("RESEARCH AGENT: Orientações aplicadas - resposta modificada")
            else:
                print("RESEARCH AGENT: Resposta já estava alinhada com as orientações")
                
            return enhanced_response
            
        except Exception as e:
            print(f"RESEARCH AGENT: Erro ao aplicar orientações: {e}")
            return response  # Retorna resposta original se houver erro
    
    def check_memory_for_decision(self, query: str, intent_analysis: Dict) -> Optional[Dict]:
        """Verifica se há uma decisão similar na memória"""
        try:
            # Procura por queries similares recentes
            query_lower = query.lower()
            for decision in self.decision_history[-10:]:  # Últimas 10 decisões
                past_query = decision.get("query", "").lower()
                
                # Se a query é muito similar e foi recente (últimas 5 decisões)
                if (len(set(query_lower.split()) & set(past_query.split())) >= 2 and
                    decision in self.decision_history[-5:]):
                    
                    cached_decision = decision.get("decision", {})
                    print(f"RESEARCH AGENT: Decisão similar encontrada na memória - {cached_decision.get('strategy')}")
                    return cached_decision
            
            return None
            
        except Exception:
            return None
    
    def register_decision(self, query: str, decision: Dict, intent_analysis: Dict):
        """Registra a decisão tomada para aprendizado futuro"""
        try:
            decision_entry = {
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "decision": decision,
                "intent_analysis": intent_analysis
            }
            
            self.decision_history.append(decision_entry)
            
            # Limita histórico
            if len(self.decision_history) > 100:
                self.decision_history = self.decision_history[-100:]
                
        except Exception as e:
            print(f"RESEARCH AGENT: Erro ao registrar decisão: {e}")
    
    def set_maestro_agent(self, maestro_agent):
        """Conecta o Maestro Agent para receber orientações"""
        self.maestro_agent = maestro_agent
        print("RESEARCH AGENT ← ORCHESTRATOR: Maestro Agent configurado")
    
    def set_data_science_agent(self, data_science_agent):
        """Conecta o Data Science Agent para coleta de dados via APIs"""
        self.data_science_agent = data_science_agent
        print("RESEARCH AGENT ← ORCHESTRATOR: Data Science Agent configurado")
    
    def add_company_to_database(self, company_name: str, tickers: List[str]) -> bool:
        """Adiciona nova empresa à base de dados do Smart Query Builder"""
        if self.smart_query_builder:
            try:
                self.smart_query_builder.add_company(company_name, tickers)
                print(f"RESEARCH AGENT: Empresa '{company_name}' adicionada com tickers: {', '.join(tickers)}")
                return True
            except Exception as e:
                print(f"RESEARCH AGENT: Erro ao adicionar empresa: {e}")
                return False
        else:
            print("RESEARCH AGENT: Smart Query Builder não disponível")
            return False
    
    def get_companies_info(self) -> Dict:
        """Retorna informações sobre empresas cadastradas"""
        if self.smart_query_builder:
            return self.smart_query_builder.get_companies_info()
        else:
            return {"error": "Smart Query Builder não disponível"}
    
    def list_available_companies(self) -> List[str]:
        """Lista empresas disponíveis na base"""
        if self.smart_query_builder:
            return list(self.smart_query_builder.company_names)[:20]  # Primeiras 20
        else:
            return []
    
    async def decide_research_strategy(self, query: str, intent_analysis: Dict) -> Dict:
        """Decide a estratégia de pesquisa baseada na análise de intenção"""
        
        # Análise básica dos requisitos
        requires_web = intent_analysis.get("requires_web", True)
        requires_docs = intent_analysis.get("requires_documents", False)
        
        # Estratégia padrão: híbrida
        if requires_web and requires_docs:
            return {
                "strategy": "hybrid",
                "confidence": 0.8,
                "reasoning": "Necessita tanto informações web quanto documentos locais"
            }
        elif requires_web and not requires_docs:
            return {
                "strategy": "web_only",
                "confidence": 0.9,
                "reasoning": "Necessita apenas informações da web"
            }
        elif requires_docs and not requires_web:
            return {
                "strategy": "local_only",
                "confidence": 0.9,
                "reasoning": "Necessita apenas documentos locais"
            }
        else:
            # Fallback para híbrida
            return {
                "strategy": "hybrid",
                "confidence": 0.6,
                "reasoning": "Estratégia híbrida como fallback"
            }

# ===== FUNÇÕES DE FERRAMENTAS =====
async def search_web(query: str) -> str:
    """Ferramenta para busca web usando Tavily"""
    return f"Resultados da busca web para: {query}"

async def query_knowledge_base(query: str) -> str:
    """Ferramenta para consulta à base de conhecimento"""
    return f"Resultados da base local para: {query}"
