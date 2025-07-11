#!/usr/bin/env python3
"""
Agente de Documentos Simplificado
Converte PDFs para texto usando bibliotecas Python padrão
"""
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import re

# Tentar importar bibliotecas para PDF
PDF_LIBRARIES = []
try:
    import PyPDF2
    PDF_LIBRARIES.append('PyPDF2')
except ImportError:
    pass

try:
    import fitz  # PyMuPDF
    PDF_LIBRARIES.append('PyMuPDF')
except ImportError:
    pass

try:
    import pdfplumber
    PDF_LIBRARIES.append('pdfplumber')
except ImportError:
    pass

class DocumentAgentSimples:
    def __init__(self, documents_path: str = None):
        if documents_path is None:
            # Usar pasta documents dentro de poc
            script_dir = Path(__file__).parent
            documents_path = script_dir / "documents"
        self.documents_dir = Path(documents_path)
        
        # Criar estrutura de pastas
        self.pending_dir = self.documents_dir / "pending"
        self.processed_dir = self.documents_dir / "processed"
        self.parsed_dir = self.documents_dir / "parsed"
        self.summaries_dir = self.documents_dir / "summaries"
        
        for dir_path in [self.pending_dir, self.processed_dir, self.parsed_dir, self.summaries_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Registro de processamento
        self.registry_file = self.documents_dir / "processing_registry.json"
        self.registry = self._load_registry()
        
        print(f"Bibliotecas PDF disponíveis: {', '.join(PDF_LIBRARIES) if PDF_LIBRARIES else 'Nenhuma'}")
    
    def _load_registry(self) -> Dict:
        """Carrega registro de documentos processados"""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"processed": {}, "last_check": None}
    
    def _save_registry(self):
        """Salva registro de processamento"""
        with open(self.registry_file, 'w', encoding='utf-8') as f:
            json.dump(self.registry, f, indent=2, ensure_ascii=False)
    
    def check_pending_documents(self) -> List[Path]:
        """Verifica documentos pendentes de processamento"""
        pending_files = []
        supported_extensions = ['.pdf', '.PDF']
        
        for ext in supported_extensions:
            pending_files.extend(self.pending_dir.glob(f"*{ext}"))
        
        # Filtrar apenas não processados
        unprocessed = []
        for file in pending_files:
            file_key = file.name
            if file_key not in self.registry["processed"]:
                unprocessed.append(file)
        
        return unprocessed
    
    def extract_text_pypdf2(self, pdf_path: Path) -> str:
        """Extrai texto usando PyPDF2"""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Erro PyPDF2: {e}")
        return text
    
    def extract_text_pymupdf(self, pdf_path: Path) -> str:
        """Extrai texto usando PyMuPDF (fitz)"""
        text = ""
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
        except Exception as e:
            print(f"Erro PyMuPDF: {e}")
        return text
    
    def extract_text_pdfplumber(self, pdf_path: Path) -> str:
        """Extrai texto usando pdfplumber"""
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"Erro pdfplumber: {e}")
        return text
    
    def extract_text_from_pdf(self, pdf_path: Path) -> tuple[str, str]:
        """Extrai texto do PDF usando a melhor biblioteca disponível"""
        text = ""
        method_used = "none"
        
        # Tentar bibliotecas em ordem de preferência
        for library in ['pdfplumber', 'PyMuPDF', 'PyPDF2']:
            if library in PDF_LIBRARIES:
                try:
                    if library == 'pdfplumber':
                        text = self.extract_text_pdfplumber(pdf_path)
                        method_used = 'pdfplumber'
                    elif library == 'PyMuPDF':
                        text = self.extract_text_pymupdf(pdf_path)
                        method_used = 'PyMuPDF'
                    elif library == 'PyPDF2':
                        text = self.extract_text_pypdf2(pdf_path)
                        method_used = 'PyPDF2'
                    
                    if text.strip():  # Se conseguiu extrair texto
                        break
                except Exception as e:
                    print(f"Erro com {library}: {e}")
                    continue
        
        return text, method_used
    
    def parse_pdf(self, pdf_path: str, auto_move: bool = True) -> Dict:
        """Processa um PDF e converte para texto"""
        pdf_file = Path(pdf_path)
        
        if not pdf_file.exists():
            return {
                "status": "error",
                "error": f"Arquivo não encontrado: {pdf_path}"
            }
        
        if not PDF_LIBRARIES:
            return {
                "status": "error",
                "error": "Nenhuma biblioteca PDF disponível. Instale: pip install PyPDF2 ou pdfplumber"
            }
        
        print(f"\nProcessando: {pdf_file.name}")
        
        try:
            # Extrair texto
            full_text, method_used = self.extract_text_from_pdf(pdf_file)
            
            if not full_text.strip():
                return {
                    "status": "error",
                    "error": "Não foi possível extrair texto do PDF"
                }
            
            # Salvar texto extraído
            output_file = self.parsed_dir / f"{pdf_file.stem}_parsed.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(full_text)
            
            # Analisar conteúdo
            analysis = self._analyze_financial_content(full_text)
            
            # Criar arquivo de resumo
            summary_file = self.summaries_dir / f"{pdf_file.stem}_summary.md"
            self._create_summary_file(pdf_file, full_text, analysis, summary_file, method_used)
            
            # Salvar JSON com dados estruturados
            json_file = self.parsed_dir / f"{pdf_file.stem}_parsed.json"
            self._save_structured_data(pdf_file, full_text, analysis, json_file, method_used)
            
            result = {
                "status": "success",
                "file": str(pdf_file),
                "output_file": str(output_file),
                "json_file": str(json_file),
                "summary_file": str(summary_file),
                "characters": len(full_text),
                "words": len(full_text.split()),
                "method_used": method_used,
                "analysis": analysis,
                "timestamp": datetime.now().isoformat()
            }
            
            # Registrar processamento
            self.registry["processed"][pdf_file.name] = result
            self._save_registry()
            
            # Mover arquivo para processed
            if auto_move and pdf_file.parent == self.pending_dir:
                dest_file = self.processed_dir / pdf_file.name
                shutil.move(str(pdf_file), str(dest_file))
                result["moved_to"] = str(dest_file)
                print(f"✓ Arquivo movido para: {dest_file}")
            
            print(f"✓ Processamento concluído:")
            print(f"  - Texto: {len(full_text):,} caracteres")
            print(f"  - Método: {method_used}")
            print(f"  - Análise: {len(analysis.get('financial_indicators', []))} indicadores encontrados")
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Erro ao processar PDF: {str(e)}"
            }
    
    def _analyze_financial_content(self, content: str) -> Dict:
        """Analisa conteúdo financeiro do texto"""
        content_upper = content.upper()
        content_lower = content.lower()
        
        analysis = {
            "has_tables": False,
            "has_numbers": False,
            "financial_indicators": [],
            "sections": [],
            "company_info": {},
            "period_info": {},
            "metrics": {}
        }
        
        # Verificar tabelas
        if content.count('|') > 10 or any(word in content_upper for word in ['TABELA', 'TABLE']):
            analysis["has_tables"] = True
        
        # Verificar números
        if re.search(r'\d+[.,]\d+', content):
            analysis["has_numbers"] = True
        
        # Indicadores financeiros comuns
        financial_terms = {
            'receita': ['receita', 'faturamento', 'vendas'],
            'lucro': ['lucro', 'resultado', 'profit'],
            'ebitda': ['ebitda', 'lajida'],
            'margem': ['margem'],
            'divida': ['dívida', 'endividamento', 'debt'],
            'investimento': ['investimento', 'capex'],
            'patrimonio': ['patrimônio', 'equity'],
            'acao': ['ação', 'share', 'stock'],
            'trimestre': ['trimestre', 'quarter', '1t', '2t', '3t', '4t'],
            'crescimento': ['crescimento', 'growth', 'aumento']
        }
        
        for categoria, termos in financial_terms.items():
            for termo in termos:
                if termo in content_lower:
                    analysis["financial_indicators"].append(categoria)
                    break
        
        # Extrair seções/títulos
        lines = content.split('\n')
        for line in lines[:50]:  # Primeiras 50 linhas
            line = line.strip()
            if line and (line.isupper() or line.startswith('#')):
                if 5 < len(line) < 100 and len(line.split()) < 15:
                    analysis["sections"].append(line)
        
        # Tentar extrair informações da empresa
        # Buscar por padrões como "2024", "1T25", etc.
        period_patterns = [
            r'(\d{4})',  # Ano
            r'([1-4][TQ]\d{2,4})',  # Trimestre
            r'(primeiro|segundo|terceiro|quarto)\s+trimestre',
            r'(janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\s+(\d{4})'
        ]
        
        periods_found = []
        for pattern in period_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            periods_found.extend([match if isinstance(match, str) else match[0] for match in matches])
        
        analysis["period_info"] = {"periods_mentioned": list(set(periods_found))}
        
        # Buscar valores monetários
        money_patterns = [
            r'R\$\s*(\d+(?:[.,]\d+)*)',
            r'(\d+(?:[.,]\d+)*)\s*milhões?',
            r'(\d+(?:[.,]\d+)*)\s*bilhões?'
        ]
        
        monetary_values = []
        for pattern in money_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            monetary_values.extend(matches)
        
        analysis["metrics"] = {"monetary_values_found": len(monetary_values)}
        
        return analysis
    
    def _create_summary_file(self, pdf_file: Path, content: str, analysis: Dict, output_file: Path, method_used: str):
        """Cria arquivo de resumo em Markdown"""
        summary = f"""# Resumo do Release: {pdf_file.stem}

## Informações Gerais
- **Arquivo original**: {pdf_file.name}
- **Tamanho**: {len(content):,} caracteres
- **Palavras**: {len(content.split()):,}
- **Processado em**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
- **Método de extração**: {method_used}

## Análise de Conteúdo
- **Contém tabelas**: {'Sim' if analysis['has_tables'] else 'Não'}
- **Contém números**: {'Sim' if analysis['has_numbers'] else 'Não'}
- **Indicadores financeiros**: {len(analysis['financial_indicators'])}
- **Valores monetários encontrados**: {analysis['metrics'].get('monetary_values_found', 0)}

## Indicadores Financeiros Identificados
"""
        
        if analysis['financial_indicators']:
            for indicator in analysis['financial_indicators']:
                summary += f"- {indicator.title()}\n"
        else:
            summary += "- Nenhum indicador específico identificado\n"
        
        if analysis['sections']:
            summary += f"\n## Seções Identificadas\n"
            for section in analysis['sections'][:10]:
                summary += f"- {section}\n"
        
        if analysis['period_info'].get('periods_mentioned'):
            summary += f"\n## Períodos Mencionados\n"
            unique_periods = list(set(analysis['period_info']['periods_mentioned']))[:10]
            for period in unique_periods:
                summary += f"- {period}\n"
        
        summary += f"\n## Preview (primeiras 500 palavras)\n```\n"
        preview = ' '.join(content.split()[:500])
        summary += preview + "...\n```\n"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(summary)
    
    def _save_structured_data(self, pdf_file: Path, content: str, analysis: Dict, output_file: Path, method_used: str):
        """Salva dados estruturados em JSON"""
        data = {
            "file_info": {
                "original_name": pdf_file.name,
                "processed_at": datetime.now().isoformat(),
                "extraction_method": method_used,
                "file_size_chars": len(content),
                "file_size_words": len(content.split())
            },
            "analysis": analysis,
            "full_text": content
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def process_all_pending(self) -> Dict:
        """Processa todos os documentos pendentes"""
        pending_docs = self.check_pending_documents()
        
        if not pending_docs:
            return {
                "status": "complete",
                "message": "Nenhum documento para processar",
                "total": 0,
                "success": 0,
                "failed": 0
            }
        
        print(f"\nEncontrados {len(pending_docs)} documentos para processar:")
        for doc in pending_docs:
            print(f"  - {doc.name}")
        
        results = {
            "total": len(pending_docs),
            "success": 0,
            "failed": 0,
            "documents": []
        }
        
        for pdf_file in pending_docs:
            print(f"\n{'='*60}")
            result = self.parse_pdf(str(pdf_file), auto_move=True)
            results["documents"].append(result)
            
            if result["status"] == "success":
                results["success"] += 1
                print(f"✓ Sucesso: {pdf_file.name}")
            else:
                results["failed"] += 1
                print(f"✗ Erro: {pdf_file.name} - {result.get('error', 'Erro desconhecido')}")
        
        self.registry["last_check"] = datetime.now().isoformat()
        self._save_registry()
        
        print(f"\n{'='*60}")
        print(f"Processamento concluído:")
        print(f"  Total: {results['total']}")
        print(f"  Sucesso: {results['success']}")
        print(f"  Falhas: {results['failed']}")
        
        return results
    
    def get_processing_status(self) -> Dict:
        """Obtém status do processamento"""
        pending = self.check_pending_documents()
        
        return {
            "pending_documents": len(pending),
            "pending_files": [f.name for f in pending],
            "total_processed": len(self.registry["processed"]),
            "last_check": self.registry.get("last_check", "Nunca"),
            "processed_files": list(self.registry["processed"].keys()),
            "pdf_libraries": PDF_LIBRARIES
        }


def main():
    """Função principal"""
    print("=== Agente de Documentos Simplificado ===")
    
    agent = DocumentAgentSimples()
    
    if not PDF_LIBRARIES:
        print("\n[ERRO] Nenhuma biblioteca PDF encontrada!")
        print("Para usar este script, instale uma das seguintes:")
        print("  pip install PyPDF2")
        print("  pip install pdfplumber") 
        print("  pip install PyMuPDF")
        return
    
    # Verificar status
    status = agent.get_processing_status()
    
    print(f"\nStatus:")
    print(f"  Documentos pendentes: {status['pending_documents']}")
    print(f"  Documentos processados: {status['total_processed']}")
    print(f"  Última verificação: {status['last_check']}")
    print(f"  Bibliotecas PDF: {', '.join(status['pdf_libraries'])}")
    
    if status['pending_documents'] > 0:
        print(f"\nArquivos pendentes:")
        for file in status['pending_files']:
            print(f"  - {file}")
        
        confirmar = input("\nProcessar todos os documentos? (S/n): ").strip().lower()
        if confirmar != 'n':
            results = agent.process_all_pending()
        else:
            print("Processamento cancelado.")
    else:
        print("\nNenhum documento pendente para processar.")


if __name__ == "__main__":
    main()