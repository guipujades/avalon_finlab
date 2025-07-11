#!/usr/bin/env python3
"""
Análise Real de PDFs - Sistema Completo
=======================================
Este sistema processa PDFs financeiros de duas formas:
1. Extração local de texto (PyPDF2, pdfplumber)
2. Análise do conteúdo extraído
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import re


class PDFAnalyzerReal:
    """
    Analisador real de PDFs financeiros.
    """
    
    def __init__(self):
        self.cache_dir = Path("cache_analises")
        self.cache_dir.mkdir(exist_ok=True)
        
    def analyze_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Analisa um PDF financeiro completamente.
        """
        
        if not pdf_path.exists():
            return {"error": f"PDF não encontrado: {pdf_path}"}
        
        print(f"\n Analisando: {pdf_path.name}")
        print("="*60)
        
        # 1. Extrair texto
        print("📝 Extraindo texto do PDF...")
        text_content = self._extract_text(pdf_path)
        
        if not text_content:
            return {"error": "Não foi possível extrair texto do PDF"}
        
        print(f" Texto extraído: {len(text_content)} caracteres")
        
        # 2. Analisar conteúdo
        print(" Analisando conteúdo...")
        analysis = self._analyze_content(text_content, pdf_path.name)
        
        # 3. Salvar resultado
        self._save_analysis(analysis, pdf_path.stem)
        
        return analysis
    
    def _extract_text(self, pdf_path: Path) -> str:
        """
        Extrai texto do PDF usando múltiplos métodos.
        """
        
        # Método 1: pdftotext (mais confiável)
        try:
            result = subprocess.run(
                ['pdftotext', '-layout', str(pdf_path), '-'],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout
        except:
            pass
        
        # Método 2: PyPDF2
        try:
            import PyPDF2
            text = ""
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            if text.strip():
                return text
        except:
            pass
        
        # Método 3: pdfplumber
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            if text.strip():
                return text
        except:
            pass
        
        return ""
    
    def _analyze_content(self, text: str, filename: str) -> Dict[str, Any]:
        """
        Analisa o conteúdo extraído do PDF.
        """
        
        analysis = {
            "arquivo": filename,
            "data_analise": datetime.now().isoformat(),
            "tamanho_texto": len(text),
            "empresa": self._extract_company_info(text, filename),
            "periodo": self._extract_period(text),
            "metricas_financeiras": self._extract_financial_metrics(text),
            "destaques": self._extract_highlights(text),
            "riscos": self._extract_risks(text)
        }
        
        return analysis
    
    def _extract_company_info(self, text: str, filename: str) -> Dict[str, str]:
        """
        Extrai informações da empresa.
        """
        
        # Tentar identificar pelo nome do arquivo
        company_name = "VALE S.A." if "VALE" in filename.upper() else "Empresa"
        
        # Buscar CNPJ
        cnpj_pattern = r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}'
        cnpj_match = re.search(cnpj_pattern, text)
        
        return {
            "nome": company_name,
            "cnpj": cnpj_match.group(0) if cnpj_match else "",
            "setor": "Mineração" if "VALE" in filename.upper() else ""
        }
    
    def _extract_period(self, text: str) -> Dict[str, Any]:
        """
        Extrai período do relatório.
        """
        
        period = {}
        
        # Buscar trimestre
        trimestre_patterns = [
            r'([1-4])[ºo]?\s*trimestre\s*(?:de\s*)?(\d{4})',
            r'([1-4])T(\d{2,4})',
            r'(\d)[ºo]?\s*tri\w*\s*(?:de\s*)?(\d{4})'
        ]
        
        for pattern in trimestre_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                period["trimestre"] = f"{match.group(1)}T"
                year = match.group(2)
                if len(year) == 2:
                    year = "20" + year
                period["ano"] = int(year)
                break
        
        # Buscar datas
        date_pattern = r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})'
        date_matches = re.findall(date_pattern, text)
        if date_matches:
            period["datas_encontradas"] = [f"{d[0]}/{d[1]}/{d[2]}" for d in date_matches[:3]]
        
        return period
    
    def _extract_financial_metrics(self, text: str) -> Dict[str, Any]:
        """
        Extrai métricas financeiras do texto.
        """
        
        metrics = {}
        text_lower = text.lower()
        
        # Padrões para valores monetários
        value_patterns = [
            (r'receita.*?(?:r\$|usd|us\$)?\s*([\d.,]+)\s*(?:bilhões|bilhão|bi|milhões|mi)', 'receita'),
            (r'ebitda.*?(?:r\$|usd|us\$)?\s*([\d.,]+)\s*(?:bilhões|bilhão|bi|milhões|mi)', 'ebitda'),
            (r'lucro\s*líquido.*?(?:r\$|usd|us\$)?\s*([\d.,]+)\s*(?:bilhões|bilhão|bi|milhões|mi)', 'lucro_liquido'),
            (r'dívida\s*líquida.*?(?:r\$|usd|us\$)?\s*([\d.,]+)\s*(?:bilhões|bilhão|bi|milhões|mi)', 'divida_liquida'),
            (r'caixa.*?(?:r\$|usd|us\$)?\s*([\d.,]+)\s*(?:bilhões|bilhão|bi|milhões|mi)', 'caixa')
        ]
        
        for pattern, metric_name in value_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                value_str = match.group(1).replace('.', '').replace(',', '.')
                try:
                    value = float(value_str)
                    # Converter para milhões
                    if 'bilhões' in match.group(0) or 'bilhão' in match.group(0) or ' bi' in match.group(0):
                        value *= 1000
                    
                    # Determinar moeda
                    currency = "USD" if "usd" in match.group(0) or "us$" in match.group(0) else "BRL"
                    
                    metrics[metric_name] = {
                        "valor": value,
                        "moeda": currency,
                        "unidade": "milhões"
                    }
                    break  # Pegar apenas o primeiro valor encontrado
                except:
                    pass
        
        # Buscar percentuais
        percent_patterns = [
            (r'margem\s*(?:de\s*)?ebitda.*?([\d.,]+)\s*%', 'margem_ebitda'),
            (r'margem\s*líquida.*?([\d.,]+)\s*%', 'margem_liquida'),
            (r'crescimento.*?receita.*?([\d.,]+)\s*%', 'crescimento_receita'),
            (r'roe.*?([\d.,]+)\s*%', 'roe'),
            (r'roic.*?([\d.,]+)\s*%', 'roic')
        ]
        
        for pattern, metric_name in percent_patterns:
            match = re.search(pattern, text_lower)
            if match:
                value_str = match.group(1).replace(',', '.')
                try:
                    metrics[metric_name] = float(value_str)
                except:
                    pass
        
        return metrics
    
    def _extract_highlights(self, text: str) -> list:
        """
        Extrai destaques do relatório.
        """
        
        highlights = []
        
        # Buscar seções de destaques
        highlight_sections = [
            r'destaques[:\s]*(.*?)(?:\n\n|\npágina)',
            r'highlights[:\s]*(.*?)(?:\n\n|\npage)',
            r'principais\s*(?:indicadores|resultados)[:\s]*(.*?)(?:\n\n)'
        ]
        
        for pattern in highlight_sections:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                section_text = match.group(1)
                # Extrair bullets
                bullets = re.findall(r'[•▪◦-]\s*(.+)', section_text)
                highlights.extend(bullets[:5])  # Máximo 5 destaques
                break
        
        # Se não encontrou seção específica, buscar padrões
        if not highlights:
            positive_patterns = [
                r'(record[e]?\s+(?:de\s+)?(?:produção|vendas|receita|ebitda))',
                r'(crescimento\s+de\s+[\d.,]+%)',
                r'(aumento\s+de\s+[\d.,]+%)',
                r'(melhora?\s+(?:de\s+)?[\d.,]+%)'
            ]
            
            for pattern in positive_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                highlights.extend(matches[:2])
        
        return highlights[:5]  # Retornar no máximo 5 destaques
    
    def _extract_risks(self, text: str) -> list:
        """
        Extrai riscos mencionados.
        """
        
        risks = []
        
        # Palavras-chave de risco
        risk_keywords = [
            'risco', 'desafio', 'pressão', 'volatilidade', 'incerteza',
            'queda', 'redução', 'impacto negativo', 'adverso'
        ]
        
        # Buscar sentenças com palavras de risco
        sentences = text.split('.')
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in risk_keywords):
                # Limpar e adicionar
                risk = sentence.strip()
                if 20 < len(risk) < 200:  # Tamanho razoável
                    risks.append(risk)
                    if len(risks) >= 3:
                        break
        
        return risks
    
    def _save_analysis(self, analysis: Dict[str, Any], base_name: str):
        """
        Salva análise em arquivo JSON.
        """
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.cache_dir / f"analise_{base_name}_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        print(f" Análise salva em: {output_file}")
    
    def display_analysis(self, analysis: Dict[str, Any]):
        """
        Exibe análise formatada.
        """
        
        print("\n" + "="*60)
        print(" RESULTADO DA ANÁLISE")
        print("="*60)
        
        # Empresa e período
        empresa = analysis.get('empresa', {})
        periodo = analysis.get('periodo', {})
        
        print(f"\n EMPRESA: {empresa.get('nome', 'N/A')}")
        if empresa.get('cnpj'):
            print(f"   CNPJ: {empresa['cnpj']}")
        if periodo.get('trimestre'):
            print(f"   Período: {periodo.get('trimestre')}{periodo.get('ano', '')}")
        
        # Métricas financeiras
        metricas = analysis.get('metricas_financeiras', {})
        if metricas:
            print("\n💰 MÉTRICAS FINANCEIRAS:")
            for nome, dados in metricas.items():
                if isinstance(dados, dict):
                    valor = dados.get('valor', 0)
                    moeda = dados.get('moeda', 'BRL')
                    unidade = dados.get('unidade', '')
                    print(f"   {nome}: {moeda} {valor:,.1f} {unidade}")
                else:
                    print(f"   {nome}: {dados}%")
        
        # Destaques
        destaques = analysis.get('destaques', [])
        if destaques:
            print("\n✨ DESTAQUES:")
            for destaque in destaques:
                print(f"   • {destaque}")
        
        # Riscos
        riscos = analysis.get('riscos', [])
        if riscos:
            print("\n RISCOS:")
            for risco in riscos[:3]:
                print(f"   • {risco[:100]}...")


def main():
    """
    Função principal para demonstração.
    """
    
    print(" ANÁLISE REAL DE PDFs FINANCEIROS")
    print("="*60)
    
    analyzer = PDFAnalyzerReal()
    
    # Buscar PDFs disponíveis
    pdfs = []
    for folder in ["documents/pending", "documents/processed", "documents"]:
        folder_path = Path(folder)
        if folder_path.exists():
            pdfs.extend(folder_path.glob("*.pdf"))
    
    if not pdfs:
        print("\n Nenhum PDF encontrado!")
        print("   Execute primeiro: python cvm_download_principal.py")
        return
    
    print(f"\n PDFs disponíveis: {len(pdfs)}")
    
    # Analisar o primeiro PDF da VALE encontrado
    vale_pdf = None
    for pdf in pdfs:
        if "VALE" in pdf.name.upper():
            vale_pdf = pdf
            break
    
    if vale_pdf:
        print(f"\n Analisando PDF da VALE: {vale_pdf.name}")
        
        # Verificar se temos as ferramentas necessárias
        print("\n🔧 Verificando ferramentas...")
        
        # Testar pdftotext
        try:
            subprocess.run(['pdftotext', '-v'], capture_output=True, check=False)
            print(" pdftotext disponível")
        except:
            print(" pdftotext não encontrado (instale com: apt-get install poppler-utils)")
        
        # Testar PyPDF2
        try:
            import PyPDF2
            print(" PyPDF2 disponível")
        except:
            print(" PyPDF2 não encontrado (instale com: pip install PyPDF2)")
        
        # Analisar
        result = analyzer.analyze_pdf(vale_pdf)
        
        if 'error' not in result:
            analyzer.display_analysis(result)
        else:
            print(f"\n Erro: {result['error']}")
    else:
        # Analisar primeiro PDF disponível
        print(f"\n Analisando: {pdfs[0].name}")
        result = analyzer.analyze_pdf(pdfs[0])
        
        if 'error' not in result:
            analyzer.display_analysis(result)


if __name__ == "__main__":
    main()