import os
import asyncio
import shutil
import json
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

try:
    from llama_parse import LlamaParse
    LLAMA_PARSE_AVAILABLE = True
except ImportError:
    LLAMA_PARSE_AVAILABLE = False

DOCUMENTS_PATH = "documents"

class DocumentAgent:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("LLAMA_CLOUD_API_KEY")
        self.parser = None
        self.documents_dir = Path(DOCUMENTS_PATH)
        
        self.pending_dir = self.documents_dir / "pending"
        self.processed_dir = self.documents_dir / "processed"
        self.parsed_dir = self.documents_dir / "parsed"
        self.summaries_dir = self.documents_dir / "summaries"
        
        for dir_path in [self.pending_dir, self.processed_dir, self.parsed_dir, self.summaries_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        self.registry_file = self.documents_dir / "processing_registry.json"
        self.registry = self._load_registry()
        
        self._setup_parser()
    
    def _load_registry(self) -> Dict:
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"processed": {}, "last_check": None}
    
    def _save_registry(self):
        with open(self.registry_file, 'w', encoding='utf-8') as f:
            json.dump(self.registry, f, indent=2, ensure_ascii=False)
    
    def _setup_parser(self):
        if LLAMA_PARSE_AVAILABLE and self.api_key:
            try:
                self.parser = LlamaParse(
                    api_key=self.api_key,
                    result_type="text",
                    verbose=True,
                    language="pt"
                )
            except Exception as e:
                self.parser = None
    
    def check_pending_documents(self) -> List[Path]:
        pending_files = []
        supported_extensions = ['.pdf', '.PDF']
        
        for ext in supported_extensions:
            pending_files.extend(self.pending_dir.glob(f"*{ext}"))
        
        unprocessed = []
        for file in pending_files:
            file_key = file.name
            if file_key not in self.registry["processed"]:
                unprocessed.append(file)
        
        return unprocessed
    
    async def parse_pdf(self, pdf_path: str, auto_move: bool = True) -> Dict:
        pdf_file = Path(pdf_path)
        
        if not pdf_file.exists():
            return {
                "status": "error",
                "error": f"Arquivo não encontrado: {pdf_path}"
            }
        
        if not self.parser:
            return {
                "status": "error",
                "error": "LlamaParse não está configurado"
            }
        
        try:
            documents = await self.parser.aload_data(str(pdf_file))
            
            full_text = "\n\n".join([doc.text for doc in documents])
            
            output_file = self.parsed_dir / f"{pdf_file.stem}_parsed.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(full_text)
            
            analysis = self._analyze_content(full_text)
            
            summary_file = self.summaries_dir / f"{pdf_file.stem}_summary.md"
            self._create_summary_file(pdf_file, full_text, analysis, summary_file)
            
            result = {
                "status": "success",
                "file": str(pdf_file),
                "output_file": str(output_file),
                "summary_file": str(summary_file),
                "pages": len(documents),
                "characters": len(full_text),
                "words": len(full_text.split()),
                "analysis": analysis,
                "timestamp": datetime.now().isoformat()
            }
            
            self.registry["processed"][pdf_file.name] = result
            self._save_registry()
            
            if auto_move and pdf_file.parent == self.pending_dir:
                dest_file = self.processed_dir / pdf_file.name
                shutil.move(str(pdf_file), str(dest_file))
                result["moved_to"] = str(dest_file)
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Erro ao processar PDF: {str(e)}"
            }
    
    def parse_pdf_sync(self, pdf_path: str, auto_move: bool = True) -> Dict:
        try:
            loop = asyncio.get_running_loop()
            return asyncio.create_task(self.parse_pdf(pdf_path, auto_move))
        except RuntimeError:
            return asyncio.run(self.parse_pdf(pdf_path, auto_move))
    
    async def process_all_pending(self) -> Dict:
        pending_docs = self.check_pending_documents()
        
        if not pending_docs:
            return {
                "status": "complete",
                "message": "Nenhum documento para processar",
                "total": 0,
                "success": 0,
                "failed": 0
            }
        
        results = {
            "total": len(pending_docs),
            "success": 0,
            "failed": 0,
            "documents": []
        }
        
        for pdf_file in pending_docs:
            result = await self.parse_pdf(str(pdf_file), auto_move=True)
            results["documents"].append(result)
            
            if result["status"] == "success":
                results["success"] += 1
            else:
                results["failed"] += 1
        
        self.registry["last_check"] = datetime.now().isoformat()
        self._save_registry()
        
        return results
    
    def process_all_pending_sync(self) -> Dict:
        try:
            loop = asyncio.get_running_loop()
            return asyncio.create_task(self.process_all_pending())
        except RuntimeError:
            return asyncio.run(self.process_all_pending())
    
    def _analyze_content(self, content: str) -> Dict:
        lines = content.split('\n')
        
        analysis = {
            "has_equations": False,
            "has_code": False,
            "has_tables": False,
            "sections": [],
            "keywords": []
        }
        
        equation_indicators = ['=', '∫', '∑', 'π', 'σ', 'μ', 'Δ', '∂']
        for indicator in equation_indicators:
            if indicator in content:
                analysis["has_equations"] = True
                break
        
        code_indicators = ['def ', 'function', 'import ', '{', '}', '();', 'var ']
        for indicator in code_indicators:
            if indicator in content:
                analysis["has_code"] = True
                break
        
        if content.count('|') > 10 or 'TABLE' in content.upper():
            analysis["has_tables"] = True
        
        for line in lines[:100]:
            line = line.strip()
            if line and (line.isupper() or line.startswith('#')):
                if len(line) < 100 and len(line.split()) < 10:
                    analysis["sections"].append(line)
        
        financial_keywords = [
            'volatility', 'option', 'pricing', 'heston', 'black-scholes',
            'calibration', 'strike', 'maturity', 'implied', 'stochastic'
        ]
        
        content_lower = content.lower()
        for keyword in financial_keywords:
            if keyword in content_lower:
                analysis["keywords"].append(keyword)
        
        return analysis
    
    def _create_summary_file(self, pdf_file: Path, content: str, analysis: Dict, output_file: Path):
        summary = f"""# Resumo do Documento: {pdf_file.stem}

                ## Informações Gerais
                - Arquivo original: {pdf_file.name}
                - Tamanho: {len(content):,} caracteres
                - Palavras: {len(content.split()):,}
                - Processado em: {datetime.now().strftime('%Y-%m-%d %H:%M')}
                
                ## Análise de Conteúdo
                - Contém equações: {'Sim' if analysis['has_equations'] else 'Não'}
                - Contém código: {'Sim' if analysis['has_code'] else 'Não'}
                - Contém tabelas: {'Sim' if analysis['has_tables'] else 'Não'}
                
                ## Seções Identificadas
                """
        
        for section in analysis['sections'][:10]:
            summary += f"- {section}\n"
        
        if analysis['keywords']:
            summary += f"\n## Palavras-chave Encontradas\n"
            summary += ", ".join(analysis['keywords'])
        
        summary += f"\n\n## Preview (primeiras 500 palavras)\n"
        preview = ' '.join(content.split()[:500])
        summary += preview + "..."
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(summary)
    
    def get_processing_status(self) -> Dict:
        pending = self.check_pending_documents()
        
        return {
            "pending_documents": len(pending),
            "pending_files": [f.name for f in pending],
            "total_processed": len(self.registry["processed"]),
            "last_check": self.registry.get("last_check", "Nunca"),
            "processed_files": list(self.registry["processed"].keys())
        }

def main():
    if not LLAMA_PARSE_AVAILABLE:
        return
    
    agent = DocumentAgent()
    
    if not agent.parser:
        return
    
    status = agent.get_processing_status()
    
    if status['pending_documents'] > 0:
        results = agent.process_all_pending_sync()
    else:
        pass

if __name__ == "__main__":
    main()