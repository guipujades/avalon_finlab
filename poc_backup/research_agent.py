import os
import asyncio
import json
from datetime import datetime
from datetime import timedelta
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
from dotenv import load_dotenv
from tavily import AsyncTavilyClient
from llama_index.llms.openai import OpenAI
from llama_index.core.agent import FunctionCallingAgentWorker
from llama_index.core.agent import AgentRunner
from llama_index.core.tools import FunctionTool
from llama_index.core.memory import ChatMemoryBuffer
from collections import defaultdict
from document_agent import EnhancedDocumentAgent
from media_processing import setup_knowledge_base_structure

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

# ===== AGENTE DE DOCUMENTOS =====
class DocumentAgent:
    """Agente que gerencia a base de conhecimento local usando protocolos nativos"""
    
    def __init__(self, llm: OpenAI, base_path: str = DOCUMENTS_PATH):
        self.llm = llm
        self.base_path = Path(base_path)
        self.registry_path = Path(DOCUMENT_REGISTRY)
        self.registry = self.load_registry()
        
        # Cria diretório se não existir
        self.base_path.mkdir(exist_ok=True)
        
        # Prompt do agente
        prompt_file = "document_agent_prompt.txt"
        self.system_prompt = load_system_prompt(prompt_file, "document")
    
    def load_registry(self) -> Dict:
        """Carrega o registro de documentos"""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"documents": {}, "last_scan": None}
    
    def save_registry(self):
        """Salva o registro de documentos"""
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(self.registry, f, ensure_ascii=False, indent=2)
    
    async def scan_documents(self) -> Dict:
        """Escaneia a pasta de documentos e atualiza o registro"""
        documents_found = {}
        
        for file_path in self.base_path.rglob("*"):
            if file_path.is_file():
                rel_path = str(file_path.relative_to(self.base_path))
                file_info = {
                    "path": rel_path,
                    "size": file_path.stat().st_size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    "extension": file_path.suffix.lower(),
                    "name": file_path.name
                }
                documents_found[rel_path] = file_info
        
        self.registry["documents"] = documents_found
        self.registry["last_scan"] = datetime.now().isoformat()
        self.save_registry()
        
        return {
            "total_documents": len(documents_found),
            "types": self._count_types(documents_found),
            "last_scan": self.registry["last_scan"]
        }
    
    def _count_types(self, documents: Dict) -> Dict:
        """Conta documentos por tipo"""
        types = defaultdict(int)
        for doc in documents.values():
            types[doc["extension"]] += 1
        return dict(types)
    
    async def search_documents(self, query: str) -> List[Dict]:
        """Busca documentos relevantes baseado na query"""
        # Usa o LLM para analisar quais documentos podem ser relevantes
        analysis_prompt = f"""Analise a seguinte query e os documentos disponíveis:

Query: {query}

Documentos disponíveis:
{json.dumps(list(self.registry["documents"].values()), ensure_ascii=False, indent=2)}

Retorne um JSON com:
{{
    "relevant_files": ["lista de arquivos que podem conter informação relevante"],
    "reasoning": "explicação de por que esses arquivos foram selecionados",
    "search_strategy": "estratégia recomendada para buscar a informação"
}}"""
        
        response = await self.llm.acomplete(analysis_prompt)
        
        try:
            analysis = json.loads(response.text)
            return analysis
        except:
            # Fallback: busca por nome
            relevant = []
            query_lower = query.lower()
            for path, info in self.registry["documents"].items():
                if query_lower in info["name"].lower() or query_lower in path.lower():
                    relevant.append(info)
            return {
                "relevant_files": [r["path"] for r in relevant],
                "reasoning": "Busca por nome de arquivo",
                "search_strategy": "name_match"
            }
    
    async def read_document_content(self, file_path: str) -> str:
        """Lê o conteúdo de um documento usando ferramentas nativas"""
        # Aqui usaríamos o protocolo MCP ou ferramentas nativas do LlamaIndex
        # Por enquanto, vamos simular com uma leitura básica
        full_path = self.base_path / file_path
        
        if not full_path.exists():
            return f"Erro: arquivo {file_path} não encontrado"
        
        # Para arquivos de texto simples
        if full_path.suffix.lower() in ['.txt', '.md']:
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                return f"Erro ao ler arquivo: {str(e)}"
        
        # Para outros tipos, retornamos metadados
        # Em produção, aqui entraria o MCP ou outras ferramentas
        return f"Arquivo {file_path} identificado. Tipo: {full_path.suffix}. Use ferramentas específicas para processar este tipo de arquivo."
    
    async def process_query(self, request: Dict) -> Dict:
        """Processa uma query do agente principal"""
        query = request["query"]
        
        try:
            # 1. Busca documentos relevantes
            search_result = await self.search_documents(query)
            
            # 2. Para cada documento relevante, tenta extrair informação
            extracted_info = []
            for file_path in search_result.get("relevant_files", [])[:3]:  # Limita a 3 arquivos
                content = await self.read_document_content(file_path)
                
                # Usa o LLM para extrair informação relevante
                extraction_prompt = f"""Extraia informações relevantes para a query:

Query: {query}

Conteúdo do arquivo {file_path}:
{content[:2000]}...  # Limita para não exceder contexto

Retorne apenas as informações relevantes para responder a query."""
                
                extraction = await self.llm.acomplete(extraction_prompt)
                
                extracted_info.append({
                    "source": file_path,
                    "content": extraction.text,
                    "modified": self.registry["documents"].get(file_path, {}).get("modified", "unknown")
                })
            
            # 3. Sintetiza a resposta
            if extracted_info:
                synthesis_prompt = f"""Sintetize as seguintes informações extraídas da base de conhecimento local:

Query original: {query}

Informações extraídas:
{json.dumps(extracted_info, ensure_ascii=False, indent=2)}

Crie uma resposta coerente e completa."""
                
                synthesis = await self.llm.acomplete(synthesis_prompt)
                
                return AgentCommunicationProtocol.create_response(
                    request["request_id"],
                    synthesis.text,
                    {
                        "sources": [info["source"] for info in extracted_info],
                        "search_strategy": search_result.get("search_strategy", "unknown")
                    }
                )
            else:
                return AgentCommunicationProtocol.create_response(
                    request["request_id"],
                    "Nenhuma informação relevante encontrada na base de conhecimento local.",
                    {"sources": [], "search_strategy": "no_matches"}
                )
                
        except Exception as e:
            return AgentCommunicationProtocol.create_error_response(
                request["request_id"],
                str(e)
            )

# ===== AGENTE DE PESQUISA PRINCIPAL =====
class IntelligentMemoryManager:
    """Gerenciador inteligente de memória com capacidades de aprendizado"""
    
    def __init__(self, memory_file: str, patterns_file: str, llm: OpenAI, document_agent=None):
        self.memory_file = memory_file
        self.patterns_file = patterns_file
        self.llm = llm
        self.document_agent = document_agent  # Referência ao agente de documentos
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
            except:
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
            except:
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
        
        # Primeiro, verifica se há documentos recentes relacionados
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
            
            # Força consulta local se houver documentos muito recentes (últimas 24h)
            if recent_docs and not analysis.get("needs_local_knowledge"):
                analysis["needs_local_knowledge"] = True
                analysis["suggested_sources"] = ["both"]
                
            # Adiciona documentos relacionados se não vieram do LLM
            if recent_docs and not analysis.get("related_documents"):
                analysis["related_documents"] = recent_docs
                
            return analysis
        except:
            # Se houver menção a empresas específicas, assume que precisa consultar base local
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
        # Lista de empresas conhecidas (expandir conforme necessário)
        known_companies = [
            "petrobras", "petrobrás", "vale", "itaú", "itau", "bradesco", 
            "ambev", "magazine luiza", "magalu", "b3", "weg", "natura",
            "jbs", "suzano", "gerdau", "embraer", "tim", "vivo", "claro",
            "santander", "caixa", "banco do brasil", "bb", "cielo", "stone",
            "locaweb", "totvs", "linx", "vtex", "mercado livre", "ifood",
            "nubank", "pagseguro", "getnet", "rede", "azul", "gol", "latam",
            "americanas", "via", "casas bahia", "ponto frio", "extra",
            "carrefour", "assaí", "atacadão", "raia drogasil", "dpsp",
            "hapvida", "notredame", "fleury", "dasa", "klabin", "brf",
            "marfrig", "minerva", "arezzo", "alpargatas", "havaianas",
            "movida", "localiza", "unidas", "cogna", "yduqs", "ser educacional",
            "cyrela", "mrv", "even", "direcional", "tenda", "eztec",
            "multiplan", "iguatemi", "brmalls", "aliansce sonae", "log cp",
            "rumo", "ccr", "ecorodovias", "taesa", "isa cteep", "copel",
            "cemig", "light", "engie", "cpfl", "eletrobras", "chesf"
        ]
        
        entities = []
        text_lower = text.lower()
        
        # Verifica empresas conhecidas
        for company in known_companies:
            if company in text_lower:
                # Capitaliza corretamente
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
        
        # Extrai palavras com inicial maiúscula (possíveis nomes próprios)
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
        
        # Verifica todos os documentos no registro
        for filename, info in self.document_agent.registry.get("documents", {}).items():
            # Verifica se é recente
            try:
                processed_at = datetime.fromisoformat(info.get("processed_at", ""))
                if processed_at < cutoff_time:
                    continue
            except:
                continue
            
            # Verifica se está relacionado às entidades
            filename_lower = filename.lower()
            doc_related = False
            
            # Verifica no nome do arquivo
            for entity in entities:
                if entity.lower() in filename_lower:
                    doc_related = True
                    break
            
            # Também verifica no resumo se disponível
            if not doc_related and hasattr(self.document_agent, 'registry'):
                base_name = Path(filename).stem
                resumos = self.document_agent.registry.get("resumos", {})
                
                # Verifica no resumo preview
                if base_name in resumos:
                    resumo = resumos[base_name].lower()
                    for entity in entities:
                        if entity.lower() in resumo:
                            doc_related = True
                            break
                
                # Se ainda não encontrou, verifica no resumo completo se existir
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
                        except:
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


class IntelligentResearchAgent:
    """Research Agent inteligente com melhor integração com Document Agent"""
    
    def __init__(self, llm: OpenAI, document_agent, tavily_key: str):
        self.llm = llm
        self.document_agent = document_agent
        self.tavily_client = AsyncTavilyClient(api_key=tavily_key)
        self.decision_history = []
        
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
    
    async def analyze_query(self, query: str) -> Dict:
        """Análise aprofundada da query para determinar estratégia"""
        
        analysis_prompt = f"""Analise esta query e determine a melhor estratégia de busca.

QUERY: {query}

Retorne um JSON detalhado com:
{{
    "query_classification": {{
        "type": "factual/analytical/comparative/exploratory",
        "domain": "área principal (finance/macro/company/market/general)",
        "complexity": "simple/moderate/complex",
        "temporal_aspect": "historical/current/future/timeless"
    }},
    "information_requirements": {{
        "needs_realtime_data": true/false,
        "needs_historical_context": true/false,
        "needs_proprietary_data": true/false,
        "needs_multiple_perspectives": true/false,
        "needs_quantitative_data": true/false
    }},
    "source_preferences": {{
        "local_relevance": "probabilidade de ter na base local (0-1)",
        "web_necessity": "necessidade de busca web (0-1)",
        "source_priority": "local_first/web_first/parallel"
    }},
    "expected_content_types": [
        "relatórios", "dados de mercado", "análises", "notícias", etc
    ],
    "key_entities": ["empresas, produtos, conceitos mencionados"],
    "search_hints": {{
        "must_include": ["termos essenciais"],
        "should_include": ["termos desejáveis"],
        "date_range": "período relevante se aplicável"
    }}
}}"""
        
        try:
            response = await self.llm.acomplete(analysis_prompt)
            return json.loads(response.text)
        except Exception as e:
            # Fallback para análise básica
            return self._basic_query_classification(query)
    
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
        
        # Prepara requisição estruturada
        request = {
            "query": query,
            "request_id": f"research_{datetime.now().timestamp()}",
            "context": {
                "query_analysis": analysis,
                "source": "research_agent"
            },
            "specific_needs": {
                "extract_information": analysis["information_requirements"].get("needs_quantitative_data", False),
                "priority_categories": self._map_domain_to_categories(analysis["query_classification"]["domain"])
            }
        }
        
        # Consulta Document Agent
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
    
    async def perform_web_search(self, query: str, analysis: Dict) -> Dict:
        """Busca web inteligente usando Tavily"""
        
        # Prepara query otimizada
        search_terms = analysis["search_hints"]["must_include"]
        if analysis["query_classification"]["temporal_aspect"] == "current":
            search_terms.append("2024 2025")
        
        search_query = " ".join(search_terms)
        
        try:
            # Busca com Tavily
            results = await self.tavily_client.search(
                query=search_query,
                search_depth="advanced",
                max_results=10
            )
            
            # Processa resultados
            processed_results = {
                "raw_results": results,
                "relevant_findings": [],
                "key_insights": [],
                "sources": []
            }
            
            for result in results.get("results", []):
                relevance = await self._assess_result_relevance(result, analysis)
                
                if relevance["score"] > 0.5:
                    processed_results["relevant_findings"].append({
                        "title": result.get("title", ""),
                        "content": result.get("content", ""),
                        "url": result.get("url", ""),
                        "relevance_score": relevance["score"],
                        "key_points": relevance["key_points"]
                    })
                    
                    processed_results["sources"].append(result.get("url", ""))
            
            # Extrai insights principais
            if processed_results["relevant_findings"]:
                insights = await self._extract_key_insights(
                    processed_results["relevant_findings"], 
                    query
                )
                processed_results["key_insights"] = insights
            
            return processed_results
            
        except Exception as e:
            return {
                "error": str(e),
                "raw_results": {},
                "relevant_findings": [],
                "key_insights": [],
                "sources": []
            }
    
    async def _assess_result_relevance(self, result: Dict, analysis: Dict) -> Dict:
        """Avalia relevância de um resultado web"""
        
        assessment_prompt = f"""Avalie a relevância deste resultado para a query.

ANÁLISE DA QUERY:
{json.dumps(analysis, ensure_ascii=False, indent=2)}

RESULTADO WEB:
Título: {result.get('title', '')}
Conteúdo: {result.get('content', '')[:500]}

Retorne JSON com:
{{
    "score": 0.0-1.0 (relevância),
    "key_points": ["pontos principais relevantes"],
    "reason": "justificativa da pontuação"
}}"""
        
        try:
            response = await self.llm.acomplete(assessment_prompt)
            return json.loads(response.text)
        except:
            # Fallback simples
            return {
                "score": 0.5,
                "key_points": ["Conteúdo potencialmente relevante"],
                "reason": "Avaliação automática"
            }
    
    async def _extract_key_insights(self, findings: List[Dict], query: str) -> List[str]:
        """Extrai insights principais dos resultados"""
        
        combined_content = "\n\n".join([
            f"Fonte: {f['title']}\n{f['content'][:300]}"
            for f in findings[:5]
        ])
        
        extraction_prompt = f"""Extraia os insights principais para responder:

QUERY: {query}

CONTEÚDO DOS RESULTADOS:
{combined_content}

Liste os 3-5 insights mais importantes, cada um em uma linha."""
        
        try:
            response = await self.llm.acomplete(extraction_prompt)
            return response.text.strip().split('\n')
        except:
            return ["Insights não puderam ser extraídos"]
    
    def make_source_decision(self, doc_response: Dict, query_analysis: Dict) -> Dict:
        """Decide se usa apenas documentos locais, web ou ambos"""
        
        decision = {
            "strategy": "both",  # local_only, web_only, both, web_complement
            "reasoning": "",
            "confidence": 0.0,
            "specific_actions": []
        }
        
        # Analisa resposta do Document Agent
        if doc_response.get("status") == "success":
            doc_data = doc_response.get("data", {})
            recommendations = doc_data.get("recommendations", {})
            confidence = recommendations.get("confidence_level", "baixa")
            
            # Mapeia confiança para número
            confidence_map = {
                "alta": 0.9,
                "média-alta": 0.7,
                "média": 0.5,
                "baixa": 0.3
            }
            
            doc_confidence = confidence_map.get(confidence, 0.5)
            perfect_matches = len(doc_data.get("documents_found", {}).get("perfect_matches", []))
            
            # Decisão baseada em confiança e matches
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
        
        # Sobrescreve se precisa dados em tempo real
        if query_analysis["information_requirements"]["needs_realtime_data"]:
            if decision["strategy"] == "local_only":
                decision["strategy"] = "web_complement"
                decision["reasoning"] += " + dados em tempo real necessários"
                decision["specific_actions"].append("Buscar dados atualizados na web")
        
        # Registra decisão
        self.decision_history.append({
            "timestamp": datetime.now().isoformat(),
            "query": query_analysis,
            "decision": decision
        })
        
        return decision
    
    async def deep_analyze_documents(self, doc_ids: List[str], query: str) -> Dict:
        """Análise profunda de documentos específicos"""
        
        # Solicita extração detalhada ao Document Agent
        extraction_request = {
            "query": query,
            "request_id": f"deep_analysis_{datetime.now().timestamp()}",
            "document_ids": doc_ids,
            "extraction_type": "comprehensive"
        }
        
        # Por simplicidade, usa o método existente
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
        
        # Parte 1: Informações da base local
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
        
        # Parte 2: Informações da web
        if web_results and web_results.get("key_insights"):
            synthesis_parts.append({
                "source": "Pesquisa Web",
                "content": "\n".join(web_results["key_insights"]),
                "confidence": "média",
                "sources": web_results.get("sources", [])[:3]
            })
        
        # Prompt de síntese final
        synthesis_prompt = f"""Crie uma resposta completa e coerente para a pergunta do usuário.

PERGUNTA ORIGINAL: {query}

ANÁLISE DA QUERY:
Tipo: {query_analysis['query_classification']['type']}
Domínio: {query_analysis['query_classification']['domain']}
Complexidade: {query_analysis['query_classification']['complexity']}

ESTRATÉGIA UTILIZADA:
{decision['strategy']} - {decision['reasoning']}

INFORMAÇÕES COLETADAS:
{json.dumps(synthesis_parts, ensure_ascii=False, indent=2)}

DIRETRIZES PARA RESPOSTA:
1. Responda diretamente à pergunta
2. Use informações de maior confiança como base
3. Mencione as fontes (local/web) quando relevante
4. Seja claro sobre limitações ou incertezas
5. Forneça contexto quando necessário
6. Se houver dados quantitativos, destaque-os
7. Conclua com insights acionáveis quando aplicável

Crie uma resposta bem estruturada e informativa."""
        
        try:
            response = await self.llm.acomplete(synthesis_prompt)
            
            # Adiciona metadados à resposta
            final_response = response.text
            
            # Adiciona rodapé com fontes se relevante
            if decision["strategy"] != "web_only":
                docs_used = []
                if doc_response.get("status") == "success":
                    doc_data = doc_response.get("data", {})
                    for doc in doc_data.get("documents_found", {}).get("perfect_matches", [])[:3]:
                        docs_used.append(doc["filename"])
                
                if docs_used:
                    final_response += f"\n\n📚 *Documentos consultados:* {', '.join(docs_used)}"
            
            if web_results and web_results.get("sources"):
                final_response += f"\n\n🌐 *Fontes web consultadas:* {len(web_results['sources'])} fontes"
            
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
            # 1. Analisa query
            print("📊 Analisando query...")
            query_analysis = await self.analyze_query(query)
            result["analysis"] = query_analysis
            
            # 2. Consulta Document Agent
            print("📚 Consultando base de conhecimento local...")
            doc_response = await self.consult_document_agent(query, query_analysis)
            
            # 3. Decide estratégia
            decision = self.make_source_decision(doc_response, query_analysis)
            result["decision"] = decision
            print(f"🎯 Estratégia: {decision['strategy']} - {decision['reasoning']}")
            
            # 4. Executa estratégia
            web_results = None
            
            if decision["strategy"] in ["web_only", "both", "web_complement"]:
                print("🌐 Realizando busca web...")
                web_results = await self.perform_web_search(query, query_analysis)
            
            # 5. Análise profunda se necessário
            if decision["strategy"] == "local_only" and doc_response.get("status") == "success":
                doc_data = doc_response.get("data", {})
                perfect_matches = doc_data.get("documents_found", {}).get("perfect_matches", [])
                
                if perfect_matches and decision.get("specific_actions"):
                    print("🔍 Realizando análise profunda de documentos...")
                    doc_ids = [doc["document_id"] for doc in perfect_matches[:3]]
                    deep_analysis = await self.deep_analyze_documents(doc_ids, query)
                    
                    # Atualiza doc_response com análise profunda
                    if "data" in doc_response:
                        doc_response["data"]["extracted_information"] = deep_analysis
            
            # 6. Sintetiza resposta
            print("✍️ Sintetizando resposta final...")
            final_response = await self.synthesize_response(
                query,
                query_analysis,
                doc_response,
                web_results,
                decision
            )
            
            result["response"] = final_response
            result["metadata"] = {
                "local_documents_found": len(doc_response.get("data", {})
                                          .get("documents_found", {})
                                          .get("perfect_matches", [])) if doc_response.get("status") == "success" else 0,
                "web_results_found": len(web_results.get("relevant_findings", [])) if web_results else 0,
                "confidence_level": decision["confidence"],
                "processing_time": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            result["error"] = str(e)
            result["response"] = f"Erro ao processar consulta: {str(e)}"
            return result


# Funções auxiliares para manter compatibilidade
async def search_web(query: str) -> str:
    """Função de busca web para compatibilidade"""
    # Esta função seria integrada com o IntelligentResearchAgent
    return f"Busca web para: {query}"

async def query_knowledge_base(query: str) -> str:
    """Função de consulta à base para compatibilidade"""
    # Esta função seria integrada com o EnhancedDocumentAgent
    return f"Consulta base local: {query}"


# Classe principal para integração
class MultiAgentSystem:
    """Sistema multi-agente integrado"""
    
    def __init__(self, openai_key: str, tavily_key: str):
        self.llm = OpenAI(model="gpt-4o-mini", api_key=openai_key)
        self.document_agent = None  # Importado do arquivo melhorado
        self.research_agent = None
        
    async def initialize(self):
        """Inicializa o sistema"""
        # Importa o EnhancedDocumentAgent do arquivo melhorado
        from document_agent import EnhancedDocumentAgent
        
        # Inicializa agentes
        self.document_agent = EnhancedDocumentAgent(self.llm)
        self.research_agent = IntelligentResearchAgent(
            self.llm, 
            self.document_agent,
            os.getenv('TAVILY_KEY')
        )
        
        # Escaneia documentos
        print("🔍 Escaneando base de documentos...")
        scan_result = await self.document_agent.scan_documents()
        print(f"✅ {scan_result['total_documents']} documentos encontrados")
        
        return scan_result
    
    async def process_user_query(self, query: str) -> str:
        """Processa query do usuário"""
        result = await self.research_agent.process_query(query)
        return result["response"]
    
    def get_statistics(self) -> Dict:
        """Retorna estatísticas do sistema"""
        stats = {
            "documents": len(self.document_agent.registry.get("documents", {})),
            "categories": len(self.document_agent.registry.get("categories", {})),
            "topics": len(self.document_agent.registry.get("topics_index", {})),
            "decisions_made": len(self.research_agent.decision_history),
            "last_scan": self.document_agent.registry.get("last_scan", "Never")
        }
        return stats


async def main():
    global tavily_api_key, api_key, document_agent

    # Garante estrutura de pastas
    setup_knowledge_base_structure()

    # Define caminhos dos arquivos necessários
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_file = os.path.join(base_dir, "system_prompt.txt")
    memory_file = os.path.join(base_dir, "long_term_memory.json")
    patterns_file = os.path.join(base_dir, "memory_patterns.json")

    load_dotenv()
    tavily_api_key = os.getenv('TAVILY_KEY')
    api_key = os.getenv('OPENAI_API_KEY')

    # Inicializa o LLM
    llm = OpenAI(model="gpt-4o-mini", api_key=api_key)

    # Inicializa o agente de documentos com suporte a mídia
    document_agent = EnhancedDocumentAgent(llm)

    # Escaneia documentos na inicialização
    print("Escaneando base de documentos...")
    scan_result = await document_agent.scan_documents()
    print(f"Encontrados {scan_result['total_documents']} documentos")
    print(f"Tipos: {scan_result['types']}")
    print("-" * 50)

    # Carrega system prompt
    system_prompt_template = load_system_prompt(prompt_file, "research")
    system_prompt = system_prompt_template.format(date=get_current_date())
    
    # Inicializa o gerenciador de memória
    memory_manager = IntelligentMemoryManager(memory_file, patterns_file, llm, document_agent)
    
    # Cria as ferramentas
    search_tool = FunctionTool.from_defaults(
        fn=search_web,
        name="search_web",
        description="Pesquisa informações na web sobre economia, finanças e notícias atuais"
    )
    
    knowledge_tool = FunctionTool.from_defaults(
        fn=query_knowledge_base,
        name="query_knowledge_base",
        description="Consulta a base de conhecimento local com documentos, relatórios e informações proprietárias"
    )
    
    # Cria a memória de chat
    memory = ChatMemoryBuffer.from_defaults(
        llm=llm,
        token_limit=3000,
    )
    
    # Cria o agente worker com ambas as ferramentas
    agent_worker = FunctionCallingAgentWorker.from_tools(
        tools=[search_tool, knowledge_tool],
        llm=llm,
        system_prompt=system_prompt,
        verbose=False
    )
    
    # Cria o AgentRunner
    agent = AgentRunner(
        agent_worker,
        memory=memory,
    )
    
    print("Sistema Multi-Agente iniciado!")
    print("Comandos disponíveis:")
    print("  - 'sair' para encerrar")
    print("  - 'scan' para re-escanear documentos")
    print("  - 'docs' para listar documentos disponíveis")
    print("  - 'memoria' para estatísticas da memória")
    print("  - 'processar_midia <nome_do_arquivo>' para processar mídia manualmente")
    print("  - 'processar_docs' para processar todos os documentos novos")
    print("  - 'resuma <nome_do_documento>' para resumir um documento")
    print("  - 'analise profunda <nome_do_documento>: <pergunta>' para analisar um documento profundamente")
    print("-" * 50)
    
    while True:
        try:
            user_prompt = input("\nSua pergunta: ")
            
            # Comandos especiais
            if user_prompt.lower() in ['sair', 'exit', 'quit']:
                print("Encerrando o sistema. Até logo!")
                break
            
            if user_prompt.lower() == 'scan':
                print("Re-escaneando base de documentos...")
                scan_result = await document_agent.scan_documents()
                print(f"Encontrados {scan_result['total_documents']} documentos")
                print(f"Tipos: {scan_result['types']}")
                continue
            
            if user_prompt.lower() == 'docs':
                print("\nDocumentos disponíveis:")
                for path, info in document_agent.registry["documents"].items():
                    print(f"  - {path} ({info['extension']}) - Modificado: {info['modified'][:10]}")
                continue
            
            if user_prompt.lower() == 'memoria':
                print(f"\nMemória de longo prazo: {len(memory_manager.memories)} registros")
                if memory_manager.memories:
                    print(f"Primeiro registro: {memory_manager.memories[0]['timestamp']}")
                    print(f"Último registro: {memory_manager.memories[-1]['timestamp']}")
                continue
            
            # Comando para processar mídia manualmente
            if user_prompt.lower().startswith('processar_midia '):
                file_name = user_prompt.split(' ', 1)[1]
                result = await document_agent.process_media_file(file_name)
                print(result)
                continue
            
            # Comando para processar todos os documentos novos
            if user_prompt.lower() == 'processar_docs':
                document_agent.processar_novos_documentos(llm)
                print("Documentos processados e resumidos.")
                continue
            
            # Checagem para perguntas sobre a base local
            if is_base_local_query(user_prompt):
                docs = document_agent.registry["documents"]
                if docs:
                    print("\nDocumentos disponíveis na base local:")
                    for path, info in docs.items():
                        print(f"  - {path} ({info['extension']}) - Modificado: {info['modified'][:10]}")
                else:
                    print("Não há documentos na base local no momento.")
                continue
            
            # Consulta direta a documento (exemplo: 'resuma relatorio_2024.pdf' ou 'analise profunda relatorio_2024.pdf: ...')
            if user_prompt.lower().startswith('resuma '):
                doc_name = user_prompt[7:].strip()
                resposta = document_agent.consultar_documento(doc_name, '', llm, complexa=False)
                print(f"\nResumo do documento {doc_name}:")
                print(resposta)
                continue
            if user_prompt.lower().startswith('analise profunda '):
                # Exemplo: 'analise profunda relatorio_2024.pdf: Qual a tendência?'
                partes = user_prompt[16:].split(':', 1)
                doc_name = partes[0].strip()
                pergunta = partes[1].strip() if len(partes) > 1 else ''
                resposta = document_agent.consultar_documento(doc_name, pergunta, llm, complexa=True)
                print(f"\nAnálise profunda do documento {doc_name}:")
                print(resposta)
                continue
            
            if not user_prompt.strip():
                continue
            
            print("\nAnalisando sua pergunta...")
            
            # Analisa a pergunta
            analysis = await memory_manager.analyze_question(user_prompt)
            print(f"Categoria: {analysis['category']}")
            
            if analysis.get("entities"):
                print(f"Entidades detectadas: {', '.join(analysis['entities'])}")

            if analysis.get("needs_local_knowledge"):
                print("Detectei que preciso consultar a base de conhecimento local.")
                if analysis.get("related_documents"):
                    print(f"Documentos relevantes: {', '.join(analysis['related_documents'][:3])}")
                            
            # Processa a pergunta
            print("\nProcessando...")
            response = await agent.achat(user_prompt)
            
            # Exibe a resposta
            print(f"\nResposta: {response}")
            
            # Feedback
            feedback = input("\nA resposta foi útil? (s/n/pular): ").lower()
            
            if feedback != 'pular':
                was_useful = feedback == 's'
                
                save_memory = input("Salvar na memória? (s/n): ").lower()
                
                if save_memory == 's':
                    memory_manager.add_memory(
                        user_prompt, 
                        str(response), 
                        analysis,
                        was_useful
                    )
                    print("Salvo na memória!")
           
        except KeyboardInterrupt:
            print("\n\nInterrompido pelo usuário.")
            break
        except Exception as e:
            print(f"Erro: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())