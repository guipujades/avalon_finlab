import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from llama_index.llms.openai import OpenAI
from media_processing import MediaProcessingProtocol, ExternalToolsInterface, DOCUMENTS_PATH
import os
import shutil

# Importação condicional do LlamaParse
try:
    from llama_parse import LlamaParse
    LLAMA_PARSE_AVAILABLE = True
except ImportError:
    LLAMA_PARSE_AVAILABLE = False
    print("Aviso: LlamaParse não está instalado. Usando processamento básico.")

class DocumentAgent:
    """Agente de documentos base (pode ser expandido)"""
    def __init__(self, llm: OpenAI, base_path: str = DOCUMENTS_PATH):
        self.llm = llm
        self.base_path = Path(base_path)
        self.registry_path = Path("document_registry.json")
        self.registry = self.load_registry()
        self.base_path.mkdir(exist_ok=True)
        
        # Cria estrutura de pastas necessária
        self._setup_folders()
        
    def _setup_folders(self):
        """Cria todas as pastas necessárias"""
        folders = [
            Path("knowledge_base/novos_docs"),
            Path("knowledge_base/docs_processados"),
            Path("knowledge_base/documentos/relatorios"),
        ]
        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)
    
    def load_registry(self) -> Dict:
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"documents": {}, "resumos": {}, "last_scan": None}
    
    def save_registry(self):
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(self.registry, f, ensure_ascii=False, indent=2)
    
    async def scan_documents(self) -> Dict:
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
        types = {}
        for doc in documents.values():
            ext = doc["extension"]
            types[ext] = types.get(ext, 0) + 1
        return types

class EnhancedDocumentAgent:
    """Document Agent genérico e inteligente para qualquer tipo de documento"""
    
    def __init__(self, llm, base_path: str = "knowledge_base"):
        self.llm = llm
        self.base_path = Path(base_path)
        self.registry_path = Path("document_registry.json")
        self.registry = self.load_registry()
        
        # Categorias expandidas para diversos tipos de conteúdo
        self.content_categories = {
            "financial_reports": {
                "keywords": ["earnings", "resultado", "balanço", "demonstração", "financial statement"],
                "priority": "high"
            },
            "market_data": {
                "keywords": ["cotação", "preço", "price", "ticker", "trading", "mercado"],
                "priority": "high"
            },
            "research_analysis": {
                "keywords": ["análise", "research", "recomendação", "target", "rating"],
                "priority": "high"
            },
            "macroeconomic": {
                "keywords": ["macro", "economia", "inflação", "pib", "gdp", "selic", "fed", "banco central"],
                "priority": "medium"
            },
            "news_updates": {
                "keywords": ["notícia", "news", "atualização", "update", "evento", "announcement"],
                "priority": "medium"
            },
            "educational": {
                "keywords": ["livro", "book", "curso", "tutorial", "guia", "manual", "teoria"],
                "priority": "low"
            },
            "company_specific": {
                "keywords": ["empresa", "company", "corporate", "perfil", "profile"],
                "priority": "high"
            },
            "sector_analysis": {
                "keywords": ["setor", "indústria", "sector", "industry", "segmento"],
                "priority": "medium"
            },
            "regulatory": {
                "keywords": ["regulação", "regulatory", "compliance", "lei", "norma", "cvm", "sec"],
                "priority": "medium"
            },
            "general": {
                "keywords": [],
                "priority": "low"
            }
        }
        
        self._setup_folders()
    
    def _setup_folders(self):
        """Cria estrutura de pastas necessária"""
        folders = [
            self.base_path / "novos_docs",
            self.base_path / "docs_processados",
            self.base_path / "documentos/resumos",
            self.base_path / "documentos/extratos",
            self.base_path / "indices"
        ]
        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)
    
    def load_registry(self) -> Dict:
        """Carrega registro de documentos"""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r', encoding='utf-8') as f:
                    registry = json.load(f)
                    # Garante estrutura completa
                    registry.setdefault("documents", {})
                    registry.setdefault("categories", {})
                    registry.setdefault("topics_index", {})
                    registry.setdefault("entities_index", {})
                    return registry
            except:
                pass
        return {
            "documents": {},
            "categories": {},
            "topics_index": {},
            "entities_index": {},
            "last_scan": None
        }
    
    def save_registry(self):
        """Salva registro de documentos"""
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(self.registry, f, ensure_ascii=False, indent=2)
    
    async def get_knowledge_base_snapshot(self) -> Dict:
        """Retorna snapshot completo e estruturado da base de conhecimento"""
        snapshot = {
            "summary": {
                "total_documents": len(self.registry["documents"]),
                "last_update": self.registry.get("last_scan", "Never"),
                "categories": {}
            },
            "detailed_catalog": [],
            "topics_coverage": {},
            "recent_additions": [],
            "data_types": {},
            "recommendations": []
        }
        
        # Conta documentos por categoria
        category_counts = defaultdict(int)
        for doc_id, doc_info in self.registry["documents"].items():
            for cat in doc_info.get("categories", ["general"]):
                category_counts[cat] += 1
        
        snapshot["summary"]["categories"] = dict(category_counts)
        
        # Catálogo detalhado
        for doc_id, doc_info in self.registry["documents"].items():
            catalog_entry = {
                "id": doc_id,
                "filename": doc_info.get("name", doc_id),
                "type": doc_info.get("extension", "unknown"),
                "categories": doc_info.get("categories", ["general"]),
                "topics": doc_info.get("topics", []),
                "entities": doc_info.get("entities", []),
                "summary": doc_info.get("summary_preview", ""),
                "processed_date": doc_info.get("processed_at", ""),
                "relevance_score": doc_info.get("relevance_score", 0),
                "size": doc_info.get("size", 0)
            }
            snapshot["detailed_catalog"].append(catalog_entry)
        
        # Cobertura de tópicos
        snapshot["topics_coverage"] = dict(self.registry.get("topics_index", {}))
        
        # Adições recentes (últimos 7 dias)
        cutoff = datetime.now() - timedelta(days=7)
        for doc_id, doc_info in self.registry["documents"].items():
            try:
                processed = datetime.fromisoformat(doc_info.get("processed_at", ""))
                if processed > cutoff:
                    snapshot["recent_additions"].append({
                        "filename": doc_info.get("name", doc_id),
                        "date": doc_info.get("processed_at", ""),
                        "categories": doc_info.get("categories", [])
                    })
            except:
                pass
        
        # Tipos de dados disponíveis
        data_types = defaultdict(list)
        for doc_id, doc_info in self.registry["documents"].items():
            ext = doc_info.get("extension", "unknown")
            data_types[ext].append(doc_info.get("name", doc_id))
        snapshot["data_types"] = dict(data_types)
        
        # Recomendações automáticas
        snapshot["recommendations"] = self._generate_kb_recommendations()
        
        return snapshot
    
    def _generate_kb_recommendations(self) -> List[str]:
        """Gera recomendações sobre a base de conhecimento"""
        recommendations = []
        
        # Analisa cobertura
        total_docs = len(self.registry["documents"])
        if total_docs == 0:
            recommendations.append("Base vazia - adicione documentos em knowledge_base/novos_docs")
        elif total_docs < 10:
            recommendations.append("Base pequena - adicione mais documentos para melhor cobertura")
        
        # Analisa diversidade
        categories = set()
        for doc in self.registry["documents"].values():
            categories.update(doc.get("categories", []))
        
        if len(categories) < 3:
            recommendations.append("Baixa diversidade - adicione documentos de diferentes categorias")
        
        # Analisa atualização
        if self.registry.get("last_scan"):
            try:
                last_scan = datetime.fromisoformat(self.registry["last_scan"])
                if datetime.now() - last_scan > timedelta(days=7):
                    recommendations.append("Base desatualizada - execute scan para verificar novos documentos")
            except:
                pass
        
        return recommendations
    
    async def analyze_query_needs(self, query: str, context: Dict = None) -> Dict:
        """Analisa query e determina necessidades de informação"""
        
        # Obtém snapshot atual
        kb_snapshot = await self.get_knowledge_base_snapshot()
        
        analysis_prompt = f"""Analise a query e determine as necessidades de informação.

QUERY: {query}

CONTEXTO ADICIONAL: {json.dumps(context or {}, ensure_ascii=False)}

BASE DE CONHECIMENTO DISPONÍVEL:
Total de documentos: {kb_snapshot['summary']['total_documents']}
Categorias: {json.dumps(kb_snapshot['summary']['categories'], ensure_ascii=False)}
Tipos de dados: {json.dumps(list(kb_snapshot['data_types'].keys()), ensure_ascii=False)}
Tópicos cobertos: {json.dumps(list(kb_snapshot['topics_coverage'].keys())[:20], ensure_ascii=False)}

Retorne um JSON detalhado com:
{{
    "query_intent": {{
        "primary_goal": "objetivo principal da query",
        "information_type": "tipo de informação buscada (dados, análise, histórico, etc)",
        "temporal_scope": "escopo temporal (atual, histórico, projeção)",
        "specificity": "específico/geral",
        "urgency": "alta/média/baixa"
    }},
    "information_needs": {{
        "essential": ["informações essenciais para responder"],
        "complementary": ["informações que enriqueceriam a resposta"],
        "nice_to_have": ["informações adicionais úteis"]
    }},
    "relevant_categories": ["categorias de documentos relevantes"],
    "search_strategy": {{
        "primary_keywords": ["palavras-chave principais"],
        "related_terms": ["termos relacionados"],
        "entities_to_find": ["entidades específicas mencionadas"],
        "data_types_needed": ["tipos de arquivo úteis (pdf, xlsx, csv, etc)"]
    }},
    "expected_documents": {{
        "must_have": ["tipos de documentos essenciais"],
        "should_have": ["tipos de documentos desejáveis"],
        "could_have": ["tipos de documentos opcionais"]
    }},
    "quality_criteria": {{
        "recency": "importância da atualidade (crítica/importante/baixa)",
        "source_reliability": "importância da fonte (crítica/importante/baixa)",
        "depth": "profundidade necessária (superficial/média/profunda)"
    }}
}}"""
        
        try:
            response = await self.llm.acomplete(analysis_prompt)
            return json.loads(response.text)
        except Exception as e:
            # Fallback com análise básica
            return self._basic_query_analysis(query)
    
    def _basic_query_analysis(self, query: str) -> Dict:
        """Análise básica quando LLM falha"""
        query_lower = query.lower()
        
        # Detecta categoria principal
        primary_category = "general"
        for cat, info in self.content_categories.items():
            if any(kw in query_lower for kw in info["keywords"]):
                primary_category = cat
                break
        
        return {
            "query_intent": {
                "primary_goal": "information_retrieval",
                "information_type": "mixed",
                "temporal_scope": "current",
                "specificity": "general",
                "urgency": "medium"
            },
            "information_needs": {
                "essential": ["documentos relacionados à query"],
                "complementary": ["contexto adicional"],
                "nice_to_have": ["análises relacionadas"]
            },
            "relevant_categories": [primary_category],
            "search_strategy": {
                "primary_keywords": query.split()[:5],
                "related_terms": [],
                "entities_to_find": [],
                "data_types_needed": ["pdf", "xlsx", "txt"]
            },
            "expected_documents": {
                "must_have": ["documentos com palavras-chave"],
                "should_have": ["análises relacionadas"],
                "could_have": ["contexto adicional"]
            },
            "quality_criteria": {
                "recency": "importante",
                "source_reliability": "importante",
                "depth": "média"
            }
        }
    
    async def find_relevant_documents(self, needs_analysis: Dict) -> Dict:
        """Busca documentos relevantes baseado na análise de necessidades"""
        
        relevant_docs = {
            "perfect_matches": [],
            "good_matches": [],
            "partial_matches": [],
            "metadata": {
                "search_performed_at": datetime.now().isoformat(),
                "total_documents_scanned": len(self.registry["documents"]),
                "search_criteria": needs_analysis
            }
        }
        
        # Palavras-chave para busca
        keywords = set()
        keywords.update(needs_analysis["search_strategy"]["primary_keywords"])
        keywords.update(needs_analysis["search_strategy"]["related_terms"])
        
        # Busca em cada documento
        for doc_id, doc_info in self.registry["documents"].items():
            relevance_score = 0
            match_reasons = []
            
            # Verifica categorias
            doc_categories = set(doc_info.get("categories", []))
            relevant_categories = set(needs_analysis.get("relevant_categories", []))
            if doc_categories & relevant_categories:
                relevance_score += 3
                match_reasons.append(f"Categoria relevante: {doc_categories & relevant_categories}")
            
            # Verifica palavras-chave
            doc_text = f"{doc_info.get('name', '')} {doc_info.get('summary_preview', '')}".lower()
            doc_topics = set(doc_info.get("topics", []))
            doc_entities = set(doc_info.get("entities", []))
            
            for keyword in keywords:
                if keyword.lower() in doc_text:
                    relevance_score += 2
                    match_reasons.append(f"Palavra-chave encontrada: {keyword}")
                elif keyword in doc_topics or keyword in doc_entities:
                    relevance_score += 1
                    match_reasons.append(f"Tópico/entidade relacionada: {keyword}")
            
            # Verifica tipo de arquivo
            if doc_info.get("extension", "") in needs_analysis["search_strategy"]["data_types_needed"]:
                relevance_score += 1
                match_reasons.append(f"Tipo de arquivo relevante: {doc_info.get('extension')}")
            
            # Verifica atualidade se importante
            if needs_analysis["quality_criteria"]["recency"] in ["crítica", "importante"]:
                try:
                    doc_date = datetime.fromisoformat(doc_info.get("processed_at", ""))
                    if datetime.now() - doc_date < timedelta(days=30):
                        relevance_score += 2
                        match_reasons.append("Documento recente")
                except:
                    pass
            
            # Classifica documento
            if relevance_score > 0:
                doc_match = {
                    "document_id": doc_id,
                    "filename": doc_info.get("name", doc_id),
                    "type": doc_info.get("extension", "unknown"),
                    "categories": doc_info.get("categories", []),
                    "relevance_score": relevance_score,
                    "match_reasons": match_reasons,
                    "summary": doc_info.get("summary_preview", ""),
                    "size": doc_info.get("size", 0),
                    "processed_date": doc_info.get("processed_at", "")
                }
                
                if relevance_score >= 5:
                    relevant_docs["perfect_matches"].append(doc_match)
                elif relevance_score >= 3:
                    relevant_docs["good_matches"].append(doc_match)
                else:
                    relevant_docs["partial_matches"].append(doc_match)
        
        # Ordena por relevância
        for category in ["perfect_matches", "good_matches", "partial_matches"]:
            relevant_docs[category].sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return relevant_docs
    
    async def generate_recommendations(self, needs_analysis: Dict, found_documents: Dict) -> Dict:
        """Gera recomendações sobre como proceder com a busca"""
        
        total_matches = (len(found_documents["perfect_matches"]) + 
                        len(found_documents["good_matches"]) + 
                        len(found_documents["partial_matches"]))
        
        recommendations = {
            "assessment": "",
            "coverage_analysis": {},
            "recommended_documents": [],
            "information_gaps": [],
            "suggested_approach": "",
            "confidence_level": "",
            "additional_actions": []
        }
        
        # Avalia cobertura
        if len(found_documents["perfect_matches"]) >= 3:
            recommendations["assessment"] = "Excelente cobertura - documentos altamente relevantes disponíveis"
            recommendations["confidence_level"] = "alta"
        elif len(found_documents["perfect_matches"]) > 0 or len(found_documents["good_matches"]) >= 3:
            recommendations["assessment"] = "Boa cobertura - documentos relevantes disponíveis"
            recommendations["confidence_level"] = "média-alta"
        elif total_matches > 0:
            recommendations["assessment"] = "Cobertura parcial - alguns documentos relevantes"
            recommendations["confidence_level"] = "média"
        else:
            recommendations["assessment"] = "Cobertura insuficiente - poucos documentos relevantes"
            recommendations["confidence_level"] = "baixa"
        
        # Análise detalhada de cobertura
        for need_type, needs in needs_analysis["information_needs"].items():
            covered = []
            not_covered = []
            
            # Verifica o que está coberto
            all_summaries = " ".join([
                doc["summary"] for matches in found_documents.values() 
                for doc in matches if isinstance(matches, list)
            ]).lower()
            
            for need in needs:
                if need.lower() in all_summaries or any(kw in all_summaries for kw in need.split()):
                    covered.append(need)
                else:
                    not_covered.append(need)
            
            recommendations["coverage_analysis"][need_type] = {
                "covered": covered,
                "not_covered": not_covered,
                "coverage_rate": len(covered) / len(needs) if needs else 0
            }
        
        # Documentos recomendados para análise profunda
        priority_docs = []
        priority_docs.extend(found_documents["perfect_matches"][:3])
        priority_docs.extend(found_documents["good_matches"][:2])
        
        for doc in priority_docs:
            recommendations["recommended_documents"].append({
                "filename": doc["filename"],
                "reason": doc["match_reasons"][0] if doc["match_reasons"] else "Relevante",
                "priority": "high" if doc in found_documents["perfect_matches"] else "medium"
            })
        
        # Identifica lacunas
        for need_type, analysis in recommendations["coverage_analysis"].items():
            if analysis["coverage_rate"] < 0.5 and need_type == "essential":
                recommendations["information_gaps"].extend(analysis["not_covered"])
        
        # Abordagem sugerida
        if recommendations["confidence_level"] == "alta":
            recommendations["suggested_approach"] = "Use os documentos perfeitos como base principal"
        elif recommendations["confidence_level"] in ["média-alta", "média"]:
            recommendations["suggested_approach"] = "Combine documentos disponíveis com busca externa para gaps"
        else:
            recommendations["suggested_approach"] = "Priorize busca externa, use base local como complemento"
        
        # Ações adicionais
        if recommendations["information_gaps"]:
            recommendations["additional_actions"].append(
                f"Buscar externamente: {', '.join(recommendations['information_gaps'][:3])}"
            )
        
        if total_matches == 0:
            recommendations["additional_actions"].append(
                "Considere adicionar documentos relevantes à base"
            )
        
        return recommendations
    
    async def extract_specific_information(self, document_ids: List[str], query: str) -> Dict:
        """Extrai informações específicas de documentos selecionados"""
        
        extracted_info = {
            "documents_analyzed": [],
            "combined_insights": "",
            "specific_data": {},
            "quotes": [],
            "limitations": []
        }
        
        for doc_id in document_ids[:5]:  # Limita a 5 documentos
            if doc_id not in self.registry["documents"]:
                continue
            
            doc_info = self.registry["documents"][doc_id]
            
            # Carrega conteúdo do documento
            content = await self._load_document_content(doc_id)
            
            if content:
                # Extração específica
                extraction_prompt = f"""Extraia informações relevantes do documento para responder:

QUERY: {query}

DOCUMENTO: {doc_info.get('name', doc_id)}
TIPO: {doc_info.get('extension', 'unknown')}
CATEGORIAS: {doc_info.get('categories', [])}

CONTEÚDO (parcial):
{content[:8000]}

Retorne um JSON com:
{{
    "relevant_information": ["lista de informações relevantes extraídas"],
    "specific_data": {{"dados específicos": "valores"}},
    "key_quotes": ["citações importantes do documento"],
    "context": "contexto importante para entender as informações",
    "limitations": ["limitações ou informações que faltam"]
}}"""
                
                try:
                    response = await self.llm.acomplete(extraction_prompt)
                    extraction = json.loads(response.text)
                    
                    extracted_info["documents_analyzed"].append({
                        "document": doc_info.get('name', doc_id),
                        "extraction": extraction
                    })
                    
                    # Adiciona dados específicos
                    extracted_info["specific_data"].update(extraction.get("specific_data", {}))
                    extracted_info["quotes"].extend(extraction.get("key_quotes", []))
                    extracted_info["limitations"].extend(extraction.get("limitations", []))
                    
                except Exception as e:
                    extracted_info["limitations"].append(
                        f"Erro ao processar {doc_info.get('name', doc_id)}: {str(e)}"
                    )
        
        # Sintetiza insights combinados
        if extracted_info["documents_analyzed"]:
            synthesis_prompt = f"""Sintetize as informações extraídas em uma resposta coerente:

QUERY ORIGINAL: {query}

INFORMAÇÕES EXTRAÍDAS:
{json.dumps(extracted_info["documents_analyzed"], ensure_ascii=False, indent=2)}

Crie uma síntese que:
1. Responda diretamente à query
2. Combine insights de múltiplos documentos
3. Destaque dados importantes
4. Indique limitações ou gaps"""
            
            try:
                synthesis = await self.llm.acomplete(synthesis_prompt)
                extracted_info["combined_insights"] = synthesis.text
            except:
                extracted_info["combined_insights"] = "Erro na síntese das informações"
        
        return extracted_info
    
    async def _load_document_content(self, doc_id: str) -> Optional[str]:
        """Carrega conteúdo de um documento"""
        doc_info = self.registry["documents"].get(doc_id, {})
        
        # Tenta diferentes caminhos
        possible_paths = [
            Path(doc_info.get("txt_path", "")),
            self.base_path / "documentos/extratos" / f"{Path(doc_id).stem}.txt",
            self.base_path / "documentos/resumos" / f"r_{Path(doc_id).stem}.txt"
        ]
        
        for path in possible_paths:
            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        return f.read()
                except:
                    continue
        
        return None
    
    async def process_intelligent_request(self, request: Dict) -> Dict:
        """Processa requisição inteligente do research agent"""
        
        try:
            query = request.get("query", "")
            context = request.get("context", {})
            specific_needs = request.get("specific_needs", {})
            
            # 1. Snapshot da base
            kb_snapshot = await self.get_knowledge_base_snapshot()
            
            # 2. Análise de necessidades
            needs_analysis = await self.analyze_query_needs(query, context)
            
            # 3. Busca documentos relevantes
            found_documents = await self.find_relevant_documents(needs_analysis)
            
            # 4. Gera recomendações
            recommendations = await self.generate_recommendations(needs_analysis, found_documents)
            
            # 5. Se solicitado, extrai informações específicas
            extracted_info = None
            if specific_needs.get("extract_information"):
                # Pega IDs dos documentos mais relevantes
                doc_ids = [doc["document_id"] for doc in found_documents["perfect_matches"][:3]]
                doc_ids.extend([doc["document_id"] for doc in found_documents["good_matches"][:2]])
                
                if doc_ids:
                    extracted_info = await self.extract_specific_information(doc_ids, query)
            
            # Monta resposta estruturada
            response_data = {
                "knowledge_base_overview": kb_snapshot,
                "query_analysis": needs_analysis,
                "documents_found": found_documents,
                "recommendations": recommendations,
                "extracted_information": extracted_info,
                "metadata": {
                    "request_id": request.get("request_id"),
                    "processed_at": datetime.now().isoformat(),
                    "confidence": recommendations["confidence_level"]
                }
            }
            
            return {
                "status": "success",
                "data": response_data
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "request_id": request.get("request_id")
            }
    
    def categorize_document(self, filename: str, content_preview: str) -> List[str]:
        """Categoriza documento baseado no conteúdo"""
        categories = []
        content_lower = f"{filename} {content_preview}".lower()
        
        for category, info in self.content_categories.items():
            if any(keyword in content_lower for keyword in info["keywords"]):
                categories.append(category)
        
        if not categories:
            categories.append("general")
        
        return categories
    
    def extract_topics_and_entities(self, content: str) -> Tuple[List[str], List[str]]:
        """Extrai tópicos e entidades do conteúdo"""
        # Implementação simplificada - pode ser melhorada com NLP
        topics = []
        entities = []
        
        # Lista de termos comuns para diferentes áreas
        topic_patterns = {
            "valuation": ["valuation", "avaliação", "múltiplo", "p/l", "ev/ebitda"],
            "earnings": ["lucro", "receita", "earnings", "revenue", "ebitda"],
            "market_analysis": ["mercado", "análise", "tendência", "outlook"],
            "risk": ["risco", "volatilidade", "var", "stress test"],
            "growth": ["crescimento", "growth", "cagr", "expansão"],
            "dividends": ["dividendo", "dividend", "yield", "payout"],
            "debt": ["dívida", "debt", "alavancagem", "leverage"],
            "strategy": ["estratégia", "strategy", "plano", "roadmap"]
        }
        
        content_lower = content.lower()
        
        # Extrai tópicos
        for topic, patterns in topic_patterns.items():
            if any(pattern in content_lower for pattern in patterns):
                topics.append(topic)
        
        # Extrai entidades (simplificado - palavras com inicial maiúscula)
        words = content.split()
        for i, word in enumerate(words):
            if len(word) > 3 and word[0].isupper() and word not in ["The", "This", "That", "These"]:
                # Verifica se pode ser nome de empresa/entidade
                if i > 0 and words[i-1].lower() not in ["de", "da", "do", "e", "ou", "and", "or"]:
                    entities.append(word.strip(".,;:()[]{}"))
        
        # Remove duplicatas mantendo ordem
        topics = list(dict.fromkeys(topics))
        entities = list(dict.fromkeys(entities))[:20]  # Limita a 20 entidades
        
        return topics, entities
    
    async def scan_documents(self) -> Dict:
        """Escaneia e indexa documentos"""
        documents_found = {}
        
        for file_path in self.base_path.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith('.'):
                rel_path = str(file_path.relative_to(self.base_path))
                
                # Lê preview do conteúdo
                content_preview = ""
                try:
                    if file_path.suffix.lower() in ['.txt', '.md', '.csv']:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content_preview = f.read(2000)
                except:
                    pass
                
                # Categoriza documento
                categories = self.categorize_document(file_path.name, content_preview)
                
                # Extrai tópicos e entidades
                topics, entities = self.extract_topics_and_entities(content_preview)
                
                file_info = {
                    "path": rel_path,
                    "name": file_path.name,
                    "size": file_path.stat().st_size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    "extension": file_path.suffix.lower(),
                    "categories": categories,
                    "topics": topics,
                    "entities": entities,
                    "summary_preview": content_preview[:200] + "..." if content_preview else "",
                    "processed_at": datetime.now().isoformat()
                }
                
                documents_found[rel_path] = file_info
                
                # Atualiza índices
                for category in categories:
                    if category not in self.registry["categories"]:
                        self.registry["categories"][category] = []
                    self.registry["categories"][category].append(rel_path)
                
                for topic in topics:
                    if topic not in self.registry["topics_index"]:
                        self.registry["topics_index"][topic] = []
                    self.registry["topics_index"][topic].append(rel_path)
                
                for entity in entities:
                    if entity not in self.registry["entities_index"]:
                        self.registry["entities_index"][entity] = []
                    self.registry["entities_index"][entity].append(rel_path)
        
        self.registry["documents"] = documents_found
        self.registry["last_scan"] = datetime.now().isoformat()
        self.save_registry()
        
        return {
            "total_documents": len(documents_found),
            "categories": dict(self.registry["categories"]),
            "topics_indexed": len(self.registry["topics_index"]),
            "entities_indexed": len(self.registry["entities_index"]),
            "last_scan": self.registry["last_scan"]
        }
    
    def _count_types(self, documents: Dict) -> Dict:
        """Conta documentos por tipo (compatibilidade)"""
        types = {}
        for doc in documents.values():
            ext = doc.get("extension", "unknown")
            types[ext] = types.get(ext, 0) + 1
        return types

    async def scan_documents(self) -> Dict:
        """Escaneia e indexa documentos"""
        documents_found = {}
        
        for file_path in self.base_path.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith('.'):
                rel_path = str(file_path.relative_to(self.base_path))
                
                # Lê preview do conteúdo
                content_preview = ""
                try:
                    if file_path.suffix.lower() in ['.txt', '.md', '.csv']:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content_preview = f.read(2000)
                except:
                    pass
                
                # Categoriza documento
                categories = self.categorize_document(file_path.name, content_preview)
                
                # Extrai tópicos e entidades
                topics, entities = self.extract_topics_and_entities(content_preview)
                
                file_info = {
                    "path": rel_path,
                    "name": file_path.name,
                    "size": file_path.stat().st_size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    "extension": file_path.suffix.lower(),
                    "categories": categories,
                    "topics": topics,
                    "entities": entities,
                    "summary_preview": content_preview[:200] + "..." if content_preview else "",
                    "processed_at": datetime.now().isoformat()
                }
                
                documents_found[rel_path] = file_info
                
                # Atualiza índices
                for category in categories:
                    if category not in self.registry["categories"]:
                        self.registry["categories"][category] = []
                    self.registry["categories"][category].append(rel_path)
                
                for topic in topics:
                    if topic not in self.registry["topics_index"]:
                        self.registry["topics_index"][topic] = []
                    self.registry["topics_index"][topic].append(rel_path)
                
                for entity in entities:
                    if entity not in self.registry["entities_index"]:
                        self.registry["entities_index"][entity] = []
                    self.registry["entities_index"][entity].append(rel_path)
        
        self.registry["documents"] = documents_found
        self.registry["last_scan"] = datetime.now().isoformat()
        self.save_registry()
        
        # ADICIONE ESTA LINHA PARA COMPATIBILIDADE
        types_count = self._count_types(documents_found)
        
        return {
            "total_documents": len(documents_found),
            "types": types_count,  # ADICIONE ESTA LINHA
            "categories": dict(self.registry["categories"]),
            "topics_indexed": len(self.registry["topics_index"]),
            "entities_indexed": len(self.registry["entities_index"]),
            "last_scan": self.registry["last_scan"]
        }
    
    def processar_novos_documentos(self, llm, destino="knowledge_base/documentos/relatorios/"):
    """
    Versão simplificada do processamento de documentos
    Compatível com o código antigo mas sem LlamaParse
    """
    NOVOS_DOCS = self.base_path / "novos_docs"
    DOCS_PROCESSADOS = self.base_path / "docs_processados"
    
    # Garante que as pastas existam
    NOVOS_DOCS.mkdir(parents=True, exist_ok=True)
    DOCS_PROCESSADOS.mkdir(parents=True, exist_ok=True)
    Path(destino).mkdir(parents=True, exist_ok=True)
    
    # Verifica se há arquivos para processar
    arquivos = list(NOVOS_DOCS.glob("*"))
    if not arquivos:
        print("Nenhum documento novo para processar.")
        return
    
    print(f"Processando {len(arquivos)} documentos...")
    
    for file_path in arquivos:
        if not file_path.is_file():
            continue
            
        filename = file_path.name
        ext = file_path.suffix.lower()
        base_name = file_path.stem
        
        print(f"\nProcessando: {filename}")
        print(f"  Tamanho: {file_path.stat().st_size / 1024:.1f} KB")
        
        try:
            # 1. Lê o conteúdo do arquivo
            texto = ""
            
            if ext in ['.txt', '.md']:
                # Arquivos de texto simples
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        texto = f.read()
                except UnicodeDecodeError:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        texto = f.read()
                        
            elif ext == '.pdf':
                # Para PDFs, apenas notifica que precisa de processamento manual
                print(f"  ⚠️  PDF detectado. Processamento básico aplicado.")
                texto = f"[Documento PDF: {filename}]\n\nEste documento precisa ser processado manualmente ou com ferramentas específicas para PDFs."
                
            elif ext in ['.xlsx', '.xls', '.csv']:
                # Para planilhas
                print(f"  ⚠️  Planilha detectada. Processamento básico aplicado.")
                texto = f"[Planilha: {filename}]\n\nEste arquivo contém dados tabulares que precisam ser processados com ferramentas específicas."
                
            else:
                # Outros formatos
                texto = f"[Arquivo: {filename}]\n\nFormato {ext} detectado."
            
            if not texto:
                print(f"  ❌ Não foi possível ler o arquivo")
                continue
                
            # 2. Salva texto extraído
            out_txt = Path(destino) / f"{base_name}.txt"
            with open(out_txt, "w", encoding="utf-8") as f:
                f.write(texto)
            print(f"  ✓ Texto salvo ({len(texto)} caracteres)")
            
            # 3. Gera resumo usando o LLM
            print("  Gerando resumo...")
            
            # Limita texto para o resumo
            texto_para_resumo = texto[:5000] if len(texto) > 5000 else texto
            
            resumo_prompt = f"""Crie um resumo do seguinte documento "{filename}":

{texto_para_resumo}

Crie um resumo estruturado incluindo:
1. TIPO DE DOCUMENTO E CONTEXTO
2. PRINCIPAIS PONTOS
3. INFORMAÇÕES RELEVANTES
4. CONCLUSÕES

Seja conciso mas informativo."""

            try:
                response = self.llm.complete(resumo_prompt)
                resumo = response.text.strip()
            except Exception as e:
                resumo = f"Erro ao gerar resumo: {str(e)}"
            
            # Salva resumo
            out_resumo = Path(destino) / f"r_{base_name}.txt"
            with open(out_resumo, "w", encoding="utf-8") as f:
                f.write(resumo)
            print(f"  ✓ Resumo salvo ({len(resumo)} caracteres)")
            
            # 4. Atualiza registro
            self.registry["documents"][filename] = {
                "original_path": str(file_path),
                "txt_path": str(out_txt),
                "resumo_path": str(out_resumo),
                "processed_at": datetime.now().isoformat(),
                "size": file_path.stat().st_size,
                "type": ext,
                "text_length": len(texto),
                "summary_length": len(resumo)
            }
            
            # Adiciona preview do resumo
            if "resumos" not in self.registry:
                self.registry["resumos"] = {}
            self.registry["resumos"][base_name] = resumo[:300] + "..."
            
            self.save_registry()
            
            # 5. Move o original para docs_processados
            destino_final = DOCS_PROCESSADOS / filename
            shutil.move(str(file_path), str(destino_final))
            print(f"  ✓ Original movido para docs_processados")
            
        except Exception as e:
            print(f"  ❌ Erro ao processar {filename}: {str(e)}")
            continue
    
    print("\nProcessamento concluído!")
    print(f"Total processado: {len(arquivos)} arquivos")
    
    # Re-escaneia para atualizar índices
    import asyncio
    asyncio.create_task(self.scan_documents())