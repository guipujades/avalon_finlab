#!/usr/bin/env python3
"""
PDF Processor Real
==================
Processador de PDFs usando ferramentas disponíveis no sistema.
"""

import os
import re
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib


class PDFProcessor:
    """
    Processador real de PDFs para análise financeira.
    """
    
    def __init__(self):
        self.cache_dir = Path("cache_pdfs")
        self.cache_dir.mkdir(exist_ok=True)
        
    def process_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Processa um PDF e extrai informações estruturadas.
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF não encontrado: {pdf_path}")
        
        # Verificar cache
        cache_file = self._get_cache_path(pdf_path)
        if cache_file.exists():
            print("📂 Usando cache do PDF...")
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        print(f"📄 Processando PDF: {pdf_path.name}")
        
        # Extrair texto
        text = self._extract_text(pdf_path)
        
        # Processar conteúdo
        result = {
            'file_name': pdf_path.name,
            'file_size': pdf_path.stat().st_size,
            'processed_at': datetime.now().isoformat(),
            'text_content': text,
            'sections': self._extract_sections(text),
            'financial_data': self._extract_financial_data(text),
            'metrics': self._extract_metrics(text),
            'dates': self._extract_dates(text)
        }
        
        # Salvar no cache
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return result
    
    def _get_cache_path(self, pdf_path: Path) -> Path:
        """Gera caminho do cache baseado no hash do arquivo."""
        file_hash = hashlib.md5(pdf_path.read_bytes()).hexdigest()
        return self.cache_dir / f"{pdf_path.stem}_{file_hash}.json"
    
    def _extract_text(self, pdf_path: Path) -> str:
        """
        Extrai texto do PDF usando ferramentas disponíveis.
        """
        # Método 1: pdftotext (mais rápido e confiável)
        try:
            result = subprocess.run(
                ['pdftotext', '-layout', str(pdf_path), '-'],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Método 2: Python libraries
        text = self._extract_with_python_libs(pdf_path)
        if text:
            return text
        
        # Método 3: OCR como último recurso
        print("⚠️  Tentando OCR (pode demorar)...")
        return self._extract_with_ocr(pdf_path)
    
    def _extract_with_python_libs(self, pdf_path: Path) -> str:
        """Extrai texto usando bibliotecas Python."""
        try:
            # Tentar PyPDF2
            import PyPDF2
            text = ""
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except:
            pass
        
        try:
            # Tentar pdfplumber
            import pdfplumber
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    
                    # Extrair tabelas
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            text += " | ".join(str(cell) for cell in row if cell) + "\n"
            return text
        except:
            pass
        
        return ""
    
    def _extract_with_ocr(self, pdf_path: Path) -> str:
        """Usa OCR para extrair texto de PDFs escaneados."""
        try:
            # Converter PDF para imagens
            result = subprocess.run(
                ['pdftoppm', '-png', str(pdf_path), str(self.cache_dir / 'page')],
                capture_output=True,
                timeout=60
            )
            
            if result.returncode == 0:
                # Aplicar OCR nas imagens
                text = ""
                for img_path in sorted(self.cache_dir.glob('page-*.png')):
                    ocr_result = subprocess.run(
                        ['tesseract', str(img_path), '-', '-l', 'por'],
                        capture_output=True,
                        text=True
                    )
                    if ocr_result.returncode == 0:
                        text += ocr_result.stdout + "\n"
                    img_path.unlink()  # Limpar imagem
                return text
        except:
            pass
        
        return ""
    
    def _extract_sections(self, text: str) -> Dict[str, str]:
        """Extrai seções do documento."""
        sections = {}
        
        # Padrões de seções comuns em releases
        section_patterns = {
            'destaques': r'(?:destaques|highlights|principais indicadores)',
            'receita': r'(?:receita|revenue|faturamento)',
            'ebitda': r'(?:ebitda|ebit)',
            'lucro': r'(?:lucro líquido|net income|resultado)',
            'divida': r'(?:endividamento|dívida|debt)',
            'fluxo_caixa': r'(?:fluxo de caixa|cash flow)',
            'guidance': r'(?:guidance|projeções|perspectivas)'
        }
        
        lines = text.split('\n')
        current_section = None
        section_content = []
        
        for line in lines:
            line_lower = line.lower()
            
            # Verificar se é início de nova seção
            for section_name, pattern in section_patterns.items():
                if re.search(pattern, line_lower):
                    # Salvar seção anterior
                    if current_section and section_content:
                        sections[current_section] = '\n'.join(section_content)
                    
                    current_section = section_name
                    section_content = [line]
                    break
            else:
                # Adicionar linha à seção atual
                if current_section:
                    section_content.append(line)
        
        # Salvar última seção
        if current_section and section_content:
            sections[current_section] = '\n'.join(section_content)
        
        return sections
    
    def _extract_financial_data(self, text: str) -> Dict[str, Any]:
        """Extrai dados financeiros do texto."""
        data = {}
        
        # Padrões para valores monetários
        patterns = {
            'receita': r'receita.*?(?:R\$|BRL)?\s*([\d.,]+)\s*(?:bilhões|milhões|bi|mi)',
            'ebitda': r'ebitda.*?(?:R\$|BRL)?\s*([\d.,]+)\s*(?:bilhões|milhões|bi|mi)',
            'lucro': r'lucro líquido.*?(?:R\$|BRL)?\s*([\d.,]+)\s*(?:bilhões|milhões|bi|mi)',
            'divida': r'dívida.*?(?:R\$|BRL)?\s*([\d.,]+)\s*(?:bilhões|milhões|bi|mi)',
            'caixa': r'caixa.*?(?:R\$|BRL)?\s*([\d.,]+)\s*(?:bilhões|milhões|bi|mi)'
        }
        
        for key, pattern in patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            values = []
            
            for match in matches:
                value_str = match.group(1).replace('.', '').replace(',', '.')
                try:
                    value = float(value_str)
                    # Converter para milhões
                    if 'bilhões' in match.group(0).lower() or 'bi' in match.group(0).lower():
                        value *= 1000
                    values.append(value)
                except:
                    pass
            
            if values:
                data[key] = {
                    'valor': values[0],  # Primeiro valor encontrado
                    'todos_valores': values,
                    'unidade': 'milhões'
                }
        
        return data
    
    def _extract_metrics(self, text: str) -> Dict[str, Any]:
        """Extrai métricas e percentuais."""
        metrics = {}
        
        # Padrões para percentuais
        percent_patterns = {
            'margem_ebitda': r'margem\s+(?:de\s+)?ebitda.*?([\d.,]+)\s*%',
            'margem_liquida': r'margem\s+líquida.*?([\d.,]+)\s*%',
            'roe': r'ro[ea].*?([\d.,]+)\s*%',
            'roic': r'roic.*?([\d.,]+)\s*%',
            'crescimento_receita': r'(?:crescimento|aumento).*?receita.*?([\d.,]+)\s*%',
            'alavancagem': r'alavancagem.*?([\d.,]+)x'
        }
        
        for key, pattern in percent_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value_str = match.group(1).replace(',', '.')
                try:
                    metrics[key] = float(value_str)
                except:
                    pass
        
        return metrics
    
    def _extract_dates(self, text: str) -> Dict[str, str]:
        """Extrai datas importantes do documento."""
        dates = {}
        
        # Padrões de data
        date_patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
            r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})',
            r'(\d{1,2})T(\d{2})[/-](\d{4})'
        ]
        
        # Procurar trimestre
        trimestre_match = re.search(r'([1-4])[ºo]?\s*(?:trimestre|T)\s*(?:de\s*)?(\d{4})', text, re.IGNORECASE)
        if trimestre_match:
            dates['trimestre'] = f"{trimestre_match.group(1)}T{trimestre_match.group(2)}"
        
        # Procurar ano
        ano_match = re.search(r'(?:exercício|ano)\s+(?:de\s+)?(\d{4})', text, re.IGNORECASE)
        if ano_match:
            dates['ano'] = ano_match.group(1)
        
        return dates


def analyze_pdf_with_claude(pdf_path: Path, prompt: str) -> Dict[str, Any]:
    """
    Analisa um PDF usando o Claude diretamente.
    
    Esta função usa a capacidade nativa do Claude de ler PDFs
    quando fornecidos como parte da conversa.
    """
    print(f"\n🤖 Analisando PDF com Claude: {pdf_path.name}")
    
    # O Claude pode ler o PDF diretamente se fornecido o caminho
    analysis_prompt = f"""
    Por favor, analise o PDF financeiro em {pdf_path} e extraia:
    
    1. Principais métricas financeiras (receita, EBITDA, lucro, etc)
    2. Variações percentuais comparadas ao período anterior
    3. Destaques operacionais
    4. Riscos mencionados
    5. Guidance/projeções se houver
    
    {prompt}
    
    Formate a resposta em JSON estruturado.
    """
    
    # Aqui o Claude processaria o PDF diretamente
    # Por enquanto, vamos usar o processador local
    processor = PDFProcessor()
    data = processor.process_pdf(pdf_path)
    
    return {
        'status': 'processed',
        'file': str(pdf_path),
        'extracted_data': data,
        'analysis_prompt': analysis_prompt,
        'note': 'Para análise completa com Claude, forneça o PDF na conversa'
    }


if __name__ == "__main__":
    # Teste
    test_pdf = Path("documents/pending/VALE_release_3T24.pdf")
    if test_pdf.exists():
        processor = PDFProcessor()
        result = processor.process_pdf(test_pdf)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("⚠️  Nenhum PDF de teste encontrado")