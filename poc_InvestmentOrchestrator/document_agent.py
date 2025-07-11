import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from llama_index.llms.openai import OpenAI
import os

# LlamaParse integration
try:
    from llama_parse import LlamaParse
    LLAMA_PARSE_AVAILABLE = True
except ImportError:
    LLAMA_PARSE_AVAILABLE = False

DOCUMENTS_PATH = "knowledge_base"

class DocumentParsingEngine:
    """Enhanced document parsing with LlamaParse integration"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("LLAMA_CLOUD_API_KEY")
        self.parser = None
        self._setup_parser()
    
    def _setup_parser(self):
        """Setup LlamaParse parser"""
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
    
    async def parse_document(self, file_path: Path) -> Dict:
        """Parse document with LlamaParse or fallback methods"""
        if not self.parser or file_path.suffix.lower() not in ['.pdf', '.docx', '.doc']:
            return await self._basic_parse(file_path)
        
        try:
            documents = await self.parser.aload_data(str(file_path))
            
            content = "\n\n".join([doc.text for doc in documents])
            summary = self._analyze_content(content)
            
            return {
                "status": "success",
                "content": content,
                "summary": summary,
                "metadata": {
                    "parser": "llama_parse",
                    "pages": len(documents),
                    "file_path": str(file_path)
                }
            }
            
        except Exception:
            return await self._basic_parse(file_path)
    
    async def _basic_parse(self, file_path: Path) -> Dict:
        """Basic parsing fallback"""
        if file_path.suffix.lower() in ['.txt', '.md']:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                return {
                    "status": "success",
                    "content": content,
                    "summary": self._analyze_content(content),
                    "metadata": {"parser": "basic_text", "file_path": str(file_path)}
                }
            except Exception as e:
                return {"status": "error", "error": str(e)}
        
        return {
            "status": "partial",
            "content": f"Arquivo detectado: {file_path.name}",
            "summary": {"file_type": file_path.suffix, "requires_processing": True},
            "metadata": {"parser": "metadata_only", "file_path": str(file_path)}
        }
    
    def _analyze_content(self, content: str) -> Dict:
        """Analyze content structure"""
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        # Detect sections
        sections = []
        entities = []
        
        for line in lines[:50]:
            if line.startswith('#') or (line.isupper() and len(line) < 60):
                sections.append(line)
        
        # Extract common financial entities
        content_lower = content.lower()
        known_entities = [
            "petrobras", "vale", "itaú", "bradesco", "ambev", "b3",
            "selic", "ipca", "bovespa", "dólar"
        ]
        
        for entity in known_entities:
            if entity in content_lower:
                entities.append(entity)
        
        return {
            "word_count": len(content.split()),
            "sections": sections[:5],
            "entities": entities[:10],
            "has_tables": content.count('|') > 10,
            "has_numbers": sum(1 for char in content if char.isdigit()) > 50,
            "preview": content[:300] + "..." if len(content) > 300 else content
        }

class EnhancedDocumentAgent:
    """Enhanced Document Agent with comprehensive functionality"""
    
    def __init__(self, llm, base_path: str = DOCUMENTS_PATH):
        self.llm = llm
        self.base_path = Path(base_path)
        self.registry_path = Path("document_registry.json")
        self.registry = self._load_registry()
        self.parser = DocumentParsingEngine()
        
        self.categories = {
            "financial_reports": ["earnings", "resultado", "balanço", "dre", "dfp"],
            "market_data": ["cotação", "preço", "ticker", "trading", "mercado"],
            "research_analysis": ["análise", "research", "recomendação", "rating"],
            "macroeconomic": ["macro", "economia", "inflação", "pib", "selic"],
            "news_updates": ["notícia", "news", "atualização", "fato relevante"],
            "company_specific": ["empresa", "company", "corporate", "perfil"],
            "regulatory": ["regulação", "compliance", "lei", "cvm", "bacen"]
        }
        
        self._setup_folders()
    
    def _setup_folders(self):
        """Create folder structure"""
        folders = [
            "novos_docs", "docs_processados", "documentos/resumos",
            "documentos/extratos", "indices"
        ]
        for folder in folders:
            (self.base_path / folder).mkdir(parents=True, exist_ok=True)
    
    def _load_registry(self) -> Dict:
        """Load document registry"""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r', encoding='utf-8') as f:
                    registry = json.load(f)
                    # Ensure all required keys exist
                    for key in ["documents", "categories", "topics_index", "entities_index"]:
                        registry.setdefault(key, {})
                    return registry
            except Exception:
                pass
        
        return {
            "documents": {},
            "categories": {},
            "topics_index": {},
            "entities_index": {},
            "last_scan": None,
            "version": "2.0"
        }
    
    def save_registry(self):
        """Save registry to file"""
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(self.registry, f, ensure_ascii=False, indent=2)
    
    async def scan_documents(self) -> Dict:
        """Scan and process all documents"""
        documents_found = {}
        processed_count = 0
        
        for file_path in self.base_path.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith('.'):
                rel_path = str(file_path.relative_to(self.base_path))
                
                # Check if processing needed
                existing = self.registry["documents"].get(rel_path)
                file_modified = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                needs_processing = True
                if existing:
                    try:
                        last_processed = datetime.fromisoformat(existing.get("processed_at", ""))
                        needs_processing = file_modified > last_processed
                    except Exception:
                        pass
                
                # Basic file info
                file_info = {
                    "path": rel_path,
                    "name": file_path.name,
                    "size": file_path.stat().st_size,
                    "modified": file_modified.isoformat(),
                    "extension": file_path.suffix.lower(),
                    "processed_at": datetime.now().isoformat()
                }
                
                # Process if needed
                if needs_processing:
                    parsing_result = await self.parser.parse_document(file_path)
                    
                    if parsing_result["status"] in ["success", "partial"]:
                        categories = self._categorize_document(
                            file_path.name, 
                            parsing_result["summary"].get("preview", "")
                        )
                        
                        entities = parsing_result["summary"].get("entities", [])
                        
                        file_info.update({
                            "categories": categories,
                            "entities": entities,
                            "summary": parsing_result["summary"],
                            "relevance_score": self._calculate_relevance(categories, entities)
                        })
                        
                        # Save summary for quick access
                        if parsing_result["status"] == "success":
                            await self._save_summary(rel_path, parsing_result)
                        
                        processed_count += 1
                
                documents_found[rel_path] = file_info
        
        # Update registry
        self.registry["documents"] = documents_found
        self.registry["last_scan"] = datetime.now().isoformat()
        self._update_indices()
        self.save_registry()
        
        return {
            "total_documents": len(documents_found),
            "processed_this_scan": processed_count,
            "types": self._count_types(documents_found),
            "last_scan": self.registry["last_scan"]
        }
    
    def _categorize_document(self, filename: str, content: str) -> List[str]:
        """Categorize document based on content"""
        categories = []
        text = f"{filename} {content}".lower()
        
        for category, keywords in self.categories.items():
            if any(kw in text for kw in keywords):
                categories.append(category)
        
        return categories if categories else ["general"]
    
    def _calculate_relevance(self, categories: List[str], entities: List[str]) -> float:
        """Calculate document relevance score"""
        score = 0.0
        
        # High-priority categories get more weight
        high_priority = ["financial_reports", "market_data", "research_analysis"]
        for cat in categories:
            score += 0.3 if cat in high_priority else 0.2
        
        # Entities boost relevance
        score += len(entities) * 0.05
        
        return min(score, 1.0)
    
    async def _save_summary(self, doc_path: str, parsing_result: Dict):
        """Save document summary"""
        summary_dir = self.base_path / "documentos/resumos"
        summary_file = summary_dir / f"{Path(doc_path).stem}_summary.json"
        
        summary_data = {
            "document_path": doc_path,
            "parsing_result": parsing_result,
            "created_at": datetime.now().isoformat(),
            "content_preview": parsing_result.get("content", "")[:1000]
        }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)
    
    def _update_indices(self):
        """Update search indices"""
        categories_idx = defaultdict(list)
        entities_idx = defaultdict(list)
        
        for doc_id, doc_info in self.registry["documents"].items():
            for category in doc_info.get("categories", []):
                categories_idx[category].append(doc_id)
            
            for entity in doc_info.get("entities", []):
                entities_idx[entity].append(doc_id)
        
        self.registry["categories"] = dict(categories_idx)
        self.registry["entities_index"] = dict(entities_idx)
    
    def _count_types(self, documents: Dict) -> Dict:
        """Count documents by type"""
        types = defaultdict(int)
        for doc in documents.values():
            types[doc["extension"]] += 1
        return dict(types)
    
    async def get_knowledge_base_snapshot(self) -> Dict:
        """Get comprehensive KB snapshot"""
        return {
            "summary": {
                "total_documents": len(self.registry["documents"]),
                "last_update": self.registry.get("last_scan", "Never"),
                "categories": dict(self.registry.get("categories", {})),
                "llama_parse_available": LLAMA_PARSE_AVAILABLE
            },
            "catalog": [
                {
                    "id": doc_id,
                    "filename": info.get("name", doc_id),
                    "type": info.get("extension", "unknown"),
                    "categories": info.get("categories", []),
                    "entities": info.get("entities", []),
                    "relevance": info.get("relevance_score", 0),
                    "size": info.get("size", 0)
                }
                for doc_id, info in self.registry["documents"].items()
            ],
            "entities_coverage": dict(self.registry.get("entities_index", {})),
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate KB recommendations"""
        recommendations = []
        total = len(self.registry["documents"])
        
        if total == 0:
            recommendations.append("Base vazia - adicione documentos")
        elif total < 5:
            recommendations.append("Poucos documentos - adicione mais para melhor cobertura")
        
        if not LLAMA_PARSE_AVAILABLE:
            recommendations.append("LlamaParse não disponível - instale para PDF avançado")
        
        categories = len(self.registry.get("categories", {}))
        if categories < 3:
            recommendations.append("Baixa diversidade - adicione documentos variados")
        
        return recommendations
    
    async def analyze_query_needs(self, query: str, context: Dict = None) -> Dict:
        """Analyze query information needs"""
        kb_snapshot = await self.get_knowledge_base_snapshot()
        
        prompt = f"""Analise esta query e determine necessidades de informação.

QUERY: {query}
CONTEXTO: {json.dumps(context or {}, ensure_ascii=False)}

BASE DISPONÍVEL:
- {kb_snapshot['summary']['total_documents']} documentos
- Categorias: {list(kb_snapshot['summary']['categories'].keys())}

Retorne JSON:
{{
    "query_intent": {{
        "primary_goal": "objetivo principal",
        "information_type": "tipo de informação",
        "temporal_scope": "escopo temporal"
    }},
    "information_needs": {{
        "essential": ["informações essenciais"],
        "complementary": ["informações complementares"]
    }},
    "relevant_categories": ["categorias relevantes"],
    "search_strategy": {{
        "keywords": ["palavras-chave"],
        "entities": ["entidades específicas"]
    }}
}}"""
        
        try:
            response = await self.llm.acomplete(prompt)
            return json.loads(response.text)
        except Exception:
            return self._basic_analysis(query)
    
    def _basic_analysis(self, query: str) -> Dict:
        """Basic query analysis fallback"""
        query_lower = query.lower()
        
        # Detect primary category
        primary_cat = "general"
        for cat, keywords in self.categories.items():
            if any(kw in query_lower for kw in keywords):
                primary_cat = cat
                break
        
        return {
            "query_intent": {
                "primary_goal": "information_retrieval",
                "information_type": "mixed",
                "temporal_scope": "current"
            },
            "information_needs": {
                "essential": ["documentos relacionados"],
                "complementary": ["contexto adicional"]
            },
            "relevant_categories": [primary_cat],
            "search_strategy": {
                "keywords": query.split()[:5],
                "entities": []
            }
        }
    
    async def find_relevant_documents(self, needs_analysis: Dict) -> Dict:
        """Find documents relevant to needs analysis"""
        results = {
            "perfect_matches": [],
            "good_matches": [],
            "partial_matches": [],
            "metadata": {
                "search_time": datetime.now().isoformat(),
                "total_scanned": len(self.registry["documents"])
            }
        }
        
        keywords = set(needs_analysis["search_strategy"]["keywords"])
        relevant_cats = set(needs_analysis.get("relevant_categories", []))
        
        for doc_id, doc_info in self.registry["documents"].items():
            score = 0
            reasons = []
            
            # Category match
            doc_cats = set(doc_info.get("categories", []))
            if doc_cats & relevant_cats:
                score += 3
                reasons.append(f"Categoria: {doc_cats & relevant_cats}")
            
            # Keyword match
            doc_text = f"{doc_info.get('name', '')} {doc_info.get('summary', {}).get('preview', '')}".lower()
            for keyword in keywords:
                if keyword.lower() in doc_text:
                    score += 2
                    reasons.append(f"Keyword: {keyword}")
            
            # Entity match
            doc_entities = set(doc_info.get("entities", []))
            target_entities = set(needs_analysis["search_strategy"].get("entities", []))
            if doc_entities & target_entities:
                score += 2
                reasons.append(f"Entity: {doc_entities & target_entities}")
            
            # Base relevance boost
            score += doc_info.get("relevance_score", 0) * 2
            
            if score > 0:
                match = {
                    "document_id": doc_id,
                    "filename": doc_info.get("name", doc_id),
                    "type": doc_info.get("extension", "unknown"),
                    "categories": doc_info.get("categories", []),
                    "relevance_score": score,
                    "match_reasons": reasons,
                    "processed_date": doc_info.get("processed_at", "")
                }
                
                if score >= 5:
                    results["perfect_matches"].append(match)
                elif score >= 3:
                    results["good_matches"].append(match)
                else:
                    results["partial_matches"].append(match)
        
        # Sort by relevance
        for category in results:
            if isinstance(results[category], list):
                results[category].sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return results
    
    async def extract_specific_information(self, document_ids: List[str], query: str) -> Dict:
        """Extract information from specific documents"""
        results = {
            "documents_analyzed": [],
            "combined_insights": "",
            "confidence_assessment": "baixa",
            "metadata": {"query": query, "extraction_time": datetime.now().isoformat()}
        }
        
        contents = []
        for doc_id in document_ids[:5]:
            content = await self._load_document_content(doc_id)
            if content:
                doc_info = self.registry["documents"].get(doc_id, {})
                contents.append({
                    "document": doc_id,
                    "filename": doc_info.get("name", doc_id),
                    "content": content[:2000],  # Limit for processing
                    "categories": doc_info.get("categories", [])
                })
        
        if contents:
            prompt = f"""Extraia informações específicas para responder:

QUERY: {query}

DOCUMENTOS:
{json.dumps(contents, ensure_ascii=False, indent=2)}

Combine as informações relevantes de forma estruturada."""
            
            try:
                response = await self.llm.acomplete(prompt)
                results["combined_insights"] = response.text
                results["documents_analyzed"] = [
                    {"document": doc["document"], "filename": doc["filename"]} 
                    for doc in contents
                ]
                results["confidence_assessment"] = "alta" if len(contents) >= 2 else "média"
            except Exception as e:
                results["combined_insights"] = f"Erro na extração: {str(e)}"
        else:
            results["combined_insights"] = "Nenhum documento válido encontrado."
        
        return results
    
    async def _load_document_content(self, doc_id: str) -> Optional[str]:
        """Load document content"""
        # Try summary first
        summary_path = self.base_path / "documentos/resumos" / f"{Path(doc_id).stem}_summary.json"
        if summary_path.exists():
            try:
                with open(summary_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data.get("content_preview", "")
            except Exception:
                pass
        
        # Try direct parsing
        file_path = self.base_path / doc_id
        if file_path.exists():
            result = await self.parser.parse_document(file_path)
            if result["status"] == "success":
                return result["content"]
        
        return None
    
    async def process_intelligent_request(self, request: Dict) -> Dict:
        """Process intelligent request from research agent"""
        query = request.get("query", "")
        context = request.get("context", {})
        
        # CORRIGIDO: Garantir que sempre retorna um dicionário válido
        if not query:
            return {
                "status": "error",
                "error": "Query vazia fornecida",
                "metadata": {"request_id": request.get("request_id", "unknown")}
            }
        
        try:
            # Analyze needs
            needs = await self.analyze_query_needs(query, context)
            
            # Find documents  
            documents = await self.find_relevant_documents(needs)
            
            # Generate recommendations
            recommendations = await self._generate_search_recommendations(needs, documents)
            
            # Extract if requested or if we have good matches
            extracted = None
            if documents["perfect_matches"] or documents["good_matches"]:
                # Sempre tenta extrair se há documentos relevantes
                doc_ids = [doc["document_id"] for doc in (documents["perfect_matches"] + documents["good_matches"])[:3]]
                if doc_ids:
                    try:
                        extracted = await self.extract_specific_information(doc_ids, query)
                    except Exception as e:
                        # Se falha na extração, continua sem ela
                        extracted = {
                            "documents_analyzed": [],
                            "combined_insights": f"Erro na extração de informações: {str(e)}",
                            "confidence_assessment": "baixa",
                            "metadata": {"extraction_error": str(e)}
                        }
            
            return {
                "status": "success",
                "data": {
                    "needs_analysis": needs,
                    "documents_found": documents,
                    "recommendations": recommendations,
                    "extracted_information": extracted,
                    "metadata": {
                        "processing_time": datetime.now().isoformat(),
                        "request_id": request.get("request_id", "unknown"),
                        "total_documents_found": len(documents["perfect_matches"]) + len(documents["good_matches"]) + len(documents["partial_matches"])
                    }
                }
            }
            
        except Exception as e:
            # CORRIGIDO: Sempre retorna estrutura válida mesmo em erro
            return {
                "status": "error",
                "error": f"Erro no processamento: {str(e)}",
                "metadata": {
                    "request_id": request.get("request_id", "unknown"),
                    "error_time": datetime.now().isoformat(),
                    "query": query
                }
            }
    
    async def _generate_search_recommendations(self, needs: Dict, documents: Dict) -> Dict:
        """Generate search recommendations"""
        perfect = len(documents["perfect_matches"])
        good = len(documents["good_matches"])
        total = perfect + good + len(documents["partial_matches"])
        
        if perfect >= 3:
            return {
                "assessment": "Excelente cobertura na base local",
                "confidence_level": "alta",
                "suggested_approach": "Usar documentos locais como fonte principal",
                "information_gaps": []
            }
        elif perfect > 0 or good >= 2:
            return {
                "assessment": "Boa cobertura com documentos relevantes",
                "confidence_level": "média-alta", 
                "suggested_approach": "Combinar base local com busca web",
                "information_gaps": ["Dados complementares", "Informações atuais"]
            }
        elif total > 0:
            return {
                "assessment": "Cobertura limitada na base",
                "confidence_level": "média",
                "suggested_approach": "Priorizar busca web",
                "information_gaps": ["Dados sobre o tópico", "Análises relevantes"]
            }
        else:
            return {
                "assessment": "Pouca informação relevante na base",
                "confidence_level": "baixa",
                "suggested_approach": "Focar em busca web externa",
                "information_gaps": ["Dados sobre o tópico solicitado", "Análises especializadas"]
            }

# ===== COMPATIBILITY LAYER =====
class DocumentAgentCompat(EnhancedDocumentAgent):
    """Compatibility wrapper for legacy code"""
    
    async def process_query(self, request: Dict) -> Dict:
        """Legacy method - redirect to new implementation"""
        return await self.process_intelligent_request(request)
    
    def processar_novos_documentos(self, llm, destino=None):
        """Legacy method stub"""
        import asyncio
        return asyncio.create_task(self.scan_documents())
    
    async def process_media_file(self, file_name: str) -> Dict:
        """Legacy media processing stub"""
        return {
            "status": "not_supported",
            "message": "Use scan_documents() para processar documentos"
        }

# ===== FACTORY AND UTILITIES =====
def create_enhanced_document_agent(llm, base_path: str = DOCUMENTS_PATH):
    """Factory function"""
    return EnhancedDocumentAgent(llm, base_path)

def setup_knowledge_base_structure():
    """Setup KB folder structure"""
    base = Path(DOCUMENTS_PATH)
    folders = ["novos_docs", "docs_processados", "documentos/resumos", "documentos/extratos", "indices"]
    
    for folder in folders:
        (base / folder).mkdir(parents=True, exist_ok=True)

# Legacy compatibility
DocumentAgent = DocumentAgentCompat