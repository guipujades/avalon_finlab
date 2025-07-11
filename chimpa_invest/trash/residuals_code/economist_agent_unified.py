#!/usr/bin/env python3
"""
Agente Economista Unificado
============================
Analisa releases financeiros já processados e gera resumos executivos de 1 minuto.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import re


class EconomistAgent:
    """
    Agente especializado em análise financeira de empresas brasileiras.
    Trabalha com documentos já processados pelo document_agent.
    """
    
    def __init__(self):
        self.parsed_dir = Path("documents/parsed")
        self.registry_dir = Path("documents/registry")
        self.summaries_dir = Path("summaries")
        self.summaries_dir.mkdir(exist_ok=True)
        
    def get_latest_document(self, company_name: Optional[str] = None) -> Optional[Path]:
        """
        Encontra o documento mais recente na pasta parsed.
        
        Args:
            company_name: Nome da empresa (opcional) para filtrar
            
        Returns:
            Path do arquivo JSON mais recente ou None
        """
        if not self.parsed_dir.exists():
            print("❌ Pasta 'documents/parsed' não encontrada")
            return None
            
        # Buscar todos os JSONs
        json_files = list(self.parsed_dir.glob("*.json"))
        
        if not json_files:
            print("❌ Nenhum documento processado encontrado em 'documents/parsed'")
            return None
        
        # Filtrar por empresa se especificado
        if company_name:
            company_upper = company_name.upper()
            json_files = [f for f in json_files if company_upper in f.name.upper()]
            
        if not json_files:
            print(f"❌ Nenhum documento encontrado para {company_name}")
            return None
        
        # Ordenar por data de modificação (mais recente primeiro)
        json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        latest_file = json_files[0]
        print(f"📄 Documento mais recente: {latest_file.name}")
        
        return latest_file
    
    def get_historical_documents(self, company_name: str, limit: int = 4) -> List[Path]:
        """
        Busca documentos históricos da empresa para comparação.
        
        Args:
            company_name: Nome da empresa
            limit: Número máximo de documentos históricos
            
        Returns:
            Lista de Paths dos documentos históricos
        """
        if not self.parsed_dir.exists():
            return []
        
        company_upper = company_name.upper()
        json_files = [f for f in self.parsed_dir.glob("*.json") if company_upper in f.name.upper()]
        
        # Ordenar por data (mais recente primeiro)
        json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Pular o primeiro (mais recente) e pegar os próximos
        historical = json_files[1:limit+1] if len(json_files) > 1 else []
        
        print(f"📚 Encontrados {len(historical)} documentos históricos para comparação")
        
        return historical
    
    def get_company_registry(self, company_name: str) -> Optional[Dict[str, Any]]:
        """
        Busca informações da empresa no registro.
        
        Args:
            company_name: Nome da empresa
            
        Returns:
            Dicionário com informações da empresa ou None
        """
        if not self.registry_dir.exists():
            return None
        
        # Buscar arquivo de registro da empresa
        registry_files = list(self.registry_dir.glob(f"*{company_name.upper()}*.json"))
        
        if registry_files:
            with open(registry_files[0], 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Tentar buscar no IPE se existir
        ipe_files = list(Path(".").glob("ipe_cia_aberta_*.csv"))
        if ipe_files:
            try:
                import pandas as pd
                df = pd.read_csv(ipe_files[0], sep=';', encoding='latin-1')
                company_data = df[df['Nome_Companhia'].str.contains(company_name, case=False, na=False)]
                
                if not company_data.empty:
                    row = company_data.iloc[0]
                    return {
                        "nome": row.get('Nome_Companhia', company_name),
                        "cnpj": row.get('CNPJ_Companhia', ''),
                        "codigo_cvm": row.get('Codigo_CVM', ''),
                        "setor": row.get('Setor_Atividade', ''),
                        "situacao": row.get('Situacao', '')
                    }
            except:
                pass
        
        return None
    
    def analyze_document(self, doc_path: Path) -> Dict[str, Any]:
        """
        Analisa um documento processado.
        
        Args:
            doc_path: Caminho do documento JSON
            
        Returns:
            Dicionário com análise estruturada
        """
        with open(doc_path, 'r', encoding='utf-8') as f:
            doc = json.load(f)
        
        # Extrair informações básicas
        metadata = doc.get('metadata', {})
        content = doc.get('content', {})
        
        # Identificar empresa
        company_name = self._extract_company_name(doc_path.name, metadata, content)
        
        # Buscar informações históricas
        historical_docs = self.get_historical_documents(company_name)
        registry_info = self.get_company_registry(company_name)
        
        # Realizar análise
        analysis = {
            'company': company_name,
            'document': doc_path.name,
            'date': metadata.get('date', datetime.now().isoformat()),
            'period': self._extract_period(content),
            'financial_metrics': self._extract_financial_metrics(content),
            'highlights': self._extract_highlights(content),
            'risks': self._extract_risks(content),
            'comparison': self._compare_with_history(content, historical_docs),
            'registry_info': registry_info
        }
        
        return analysis
    
    def generate_executive_summary(self, analysis: Dict[str, Any]) -> str:
        """
        Gera resumo executivo de 1 minuto de leitura (~250 palavras).
        
        Args:
            analysis: Dicionário com análise do documento
            
        Returns:
            Resumo executivo formatado
        """
        company = analysis['company']
        period = analysis['period']
        metrics = analysis['financial_metrics']
        highlights = analysis['highlights']
        risks = analysis['risks']
        comparison = analysis['comparison']
        
        # Construir resumo
        summary_parts = []
        
        # Título e introdução
        summary_parts.append(f"# 📊 {company} - Resultados {period}\n")
        
        # Resumo de uma linha
        trend = comparison.get('revenue_trend', 'estável')
        summary_parts.append(f"**Resumo:** Resultados {trend} com {self._get_main_highlight(highlights, metrics)}\n")
        
        # Métricas principais (3-4 linhas)
        summary_parts.append("## 💰 Números-Chave")
        
        if metrics.get('revenue'):
            rev_var = metrics['revenue'].get('yoy_change', 0)
            summary_parts.append(f"- **Receita:** R$ {metrics['revenue']['value']:,.0f}M ({rev_var:+.1f}% a/a)")
        
        if metrics.get('ebitda'):
            ebitda_margin = metrics['ebitda'].get('margin', 0)
            summary_parts.append(f"- **EBITDA:** R$ {metrics['ebitda']['value']:,.0f}M (margem {ebitda_margin:.1f}%)")
        
        if metrics.get('net_income'):
            ni_var = metrics['net_income'].get('yoy_change', 0)
            summary_parts.append(f"- **Lucro Líquido:** R$ {metrics['net_income']['value']:,.0f}M ({ni_var:+.1f}% a/a)")
        
        # Destaques (2-3 pontos)
        if highlights:
            summary_parts.append("\n## ✨ Destaques")
            for highlight in highlights[:3]:
                summary_parts.append(f"- {highlight}")
        
        # Riscos/Atenção (1-2 pontos)
        if risks:
            summary_parts.append("\n## ⚠️ Pontos de Atenção")
            for risk in risks[:2]:
                summary_parts.append(f"- {risk}")
        
        # Contexto histórico (1-2 linhas)
        if comparison.get('performance_vs_history'):
            summary_parts.append("\n## 📈 Tendência")
            summary_parts.append(comparison['performance_vs_history'])
        
        # Perspectiva (1 linha)
        outlook = self._generate_outlook(metrics, comparison, risks)
        if outlook:
            summary_parts.append(f"\n**Perspectiva:** {outlook}")
        
        # Juntar tudo
        summary = "\n".join(summary_parts)
        
        # Adicionar tempo estimado de leitura
        word_count = len(summary.split())
        read_time = max(1, round(word_count / 250))  # 250 palavras por minuto
        
        summary = f"*⏱️ Tempo de leitura: {read_time} minuto{'s' if read_time > 1 else ''}*\n\n" + summary
        
        return summary
    
    def _extract_company_name(self, filename: str, metadata: Dict, content: Dict) -> str:
        """Extrai nome da empresa do documento."""
        # Tentar do nome do arquivo
        if "VALE" in filename.upper():
            return "VALE"
        elif "PETRO" in filename.upper():
            return "PETROBRAS"
        
        # Tentar do metadata
        if metadata.get('company'):
            return metadata['company']
        
        # Tentar do conteúdo
        text = str(content).upper()
        if "VALE S.A." in text:
            return "VALE"
        elif "PETROBRAS" in text or "PETRÓLEO BRASILEIRO" in text:
            return "PETROBRAS"
        
        # Extrair do nome do arquivo
        parts = filename.split('_')
        if parts:
            return parts[0]
        
        return "EMPRESA"
    
    def _extract_period(self, content: Dict) -> str:
        """Extrai período do relatório."""
        text = str(content)
        
        # Buscar padrões de trimestre
        patterns = [
            r'([1-4])[ºo]?\s*[Tt]rimestre\s*(?:de\s*)?(\d{4})',
            r'([1-4])T(\d{2,4})',
            r'(\d)[ºo]?\s*tri\w*\s*(?:de\s*)?(\d{4})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                quarter = match.group(1)
                year = match.group(2)
                if len(year) == 2:
                    year = "20" + year
                return f"{quarter}T{year}"
        
        return "Período"
    
    def _extract_financial_metrics(self, content: Dict) -> Dict[str, Any]:
        """Extrai métricas financeiras do conteúdo."""
        # Primeiro, verificar se já temos métricas estruturadas
        if isinstance(content, dict) and 'financial_metrics' in content:
            return content['financial_metrics']
        
        # Se não, tentar extrair do texto
        metrics = {}
        text = str(content)
        
        # Padrões para valores
        value_patterns = {
            'revenue': [
                r'[Rr]eceita.*?R\$\s*([\d.,]+)\s*(?:bilhões|milhões)',
                r'[Rr]evenue.*?R\$\s*([\d.,]+)\s*(?:billion|million)'
            ],
            'ebitda': [
                r'EBITDA.*?R\$\s*([\d.,]+)\s*(?:bilhões|milhões)',
                r'[Ee]bitda.*?R\$\s*([\d.,]+)\s*(?:bilhões|milhões)'
            ],
            'net_income': [
                r'[Ll]ucro\s*[Ll]íquido.*?R\$\s*([\d.,]+)\s*(?:bilhões|milhões)',
                r'[Nn]et\s*[Ii]ncome.*?R\$\s*([\d.,]+)\s*(?:billion|million)'
            ]
        }
        
        for metric, patterns in value_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value_str = match.group(1).replace('.', '').replace(',', '.')
                    value = float(value_str)
                    
                    # Converter bilhões para milhões
                    if 'bilhões' in match.group(0).lower() or 'billion' in match.group(0).lower():
                        value *= 1000
                    
                    metrics[metric] = {'value': value}
                    
                    # Buscar variação percentual
                    var_pattern = rf'{pattern}.*?([\+\-]?\d+[,.]?\d*)\s*%'
                    var_match = re.search(var_pattern, text, re.IGNORECASE)
                    if var_match:
                        metrics[metric]['yoy_change'] = float(var_match.group(2).replace(',', '.'))
                    
                    break
        
        # Buscar margens
        margin_patterns = {
            'ebitda': r'[Mm]argem\s*EBITDA.*?([\d,]+)\s*%',
            'net_income': r'[Mm]argem\s*[Ll]íquida.*?([\d,]+)\s*%'
        }
        
        for metric, pattern in margin_patterns.items():
            if metric in metrics:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    metrics[metric]['margin'] = float(match.group(1).replace(',', '.'))
        
        return metrics
    
    def _extract_highlights(self, content: Dict) -> List[str]:
        """Extrai principais destaques positivos."""
        # Verificar se já temos highlights estruturados
        if isinstance(content, dict) and 'highlights' in content:
            return content['highlights'][:3]
        
        highlights = []
        text = str(content)
        
        # Palavras-chave positivas
        positive_keywords = [
            'recorde', 'crescimento', 'aumento', 'melhora', 'expansão',
            'alta', 'superior', 'positivo', 'forte', 'robusto'
        ]
        
        sentences = text.split('.')
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in positive_keywords):
                # Limpar e formatar
                highlight = sentence.strip()
                if 20 < len(highlight) < 150:
                    highlights.append(highlight)
                    if len(highlights) >= 5:
                        break
        
        return highlights[:3]  # Máximo 3 destaques
    
    def _extract_risks(self, content: Dict) -> List[str]:
        """Extrai principais riscos ou desafios."""
        risks = []
        text = str(content)
        
        # Palavras-chave de risco
        risk_keywords = [
            'risco', 'desafio', 'pressão', 'queda', 'redução',
            'impacto', 'volatilidade', 'incerteza', 'preocupa'
        ]
        
        sentences = text.split('.')
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in risk_keywords):
                risk = sentence.strip()
                if 20 < len(risk) < 150:
                    risks.append(risk)
                    if len(risks) >= 3:
                        break
        
        return risks[:2]  # Máximo 2 riscos
    
    def _compare_with_history(self, current_content: Dict, historical_docs: List[Path]) -> Dict[str, Any]:
        """Compara com documentos históricos."""
        comparison = {}
        
        if not historical_docs:
            return comparison
        
        # Análise simplificada de tendência
        current_metrics = self._extract_financial_metrics(current_content)
        
        if current_metrics.get('revenue', {}).get('yoy_change', 0) > 5:
            comparison['revenue_trend'] = 'em crescimento'
        elif current_metrics.get('revenue', {}).get('yoy_change', 0) < -5:
            comparison['revenue_trend'] = 'em queda'
        else:
            comparison['revenue_trend'] = 'estável'
        
        # Performance vs histórico
        if len(historical_docs) >= 2:
            comparison['performance_vs_history'] = "Mantém trajetória consistente dos últimos trimestres"
        
        return comparison
    
    def _get_main_highlight(self, highlights: List[str], metrics: Dict[str, Any]) -> str:
        """Identifica o principal destaque para o resumo."""
        if highlights:
            return highlights[0].lower()
        
        # Baseado em métricas
        if metrics.get('revenue', {}).get('yoy_change', 0) > 10:
            return "forte crescimento de receita"
        elif metrics.get('ebitda', {}).get('margin', 0) > 40:
            return "margens robustas"
        else:
            return "resultados sólidos"
    
    def _generate_outlook(self, metrics: Dict[str, Any], comparison: Dict[str, Any], risks: List[str]) -> str:
        """Gera perspectiva baseada na análise."""
        if len(risks) > 1:
            return "Cenário desafiador requer monitoramento dos riscos identificados"
        elif comparison.get('revenue_trend') == 'em crescimento':
            return "Momentum positivo deve continuar com fundamentos sólidos"
        else:
            return "Estabilidade operacional em meio a ambiente competitivo"
    
    def save_summary(self, summary: str, company: str):
        """Salva o resumo gerado."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"summary_{company}_{timestamp}.md"
        filepath = self.summaries_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        print(f"💾 Resumo salvo em: {filepath}")
        
        return filepath
    
    def process_latest_release(self, company_name: Optional[str] = None):
        """
        Processa o release mais recente e gera resumo executivo.
        
        Args:
            company_name: Nome da empresa (opcional)
        """
        print("\n🤖 AGENTE ECONOMISTA - Análise de Release")
        print("="*50)
        
        # Buscar documento mais recente
        latest_doc = self.get_latest_document(company_name)
        
        if not latest_doc:
            return None
        
        # Analisar documento
        print("\n📊 Analisando documento...")
        analysis = self.analyze_document(latest_doc)
        
        # Gerar resumo
        print("✍️ Gerando resumo executivo...")
        summary = self.generate_executive_summary(analysis)
        
        # Salvar resumo
        summary_path = self.save_summary(summary, analysis['company'])
        
        # Exibir resumo
        print("\n" + "="*50)
        print(summary)
        print("="*50)
        
        return {
            'analysis': analysis,
            'summary': summary,
            'summary_path': str(summary_path)
        }


def main():
    """Função principal para teste."""
    agent = EconomistAgent()
    
    # Processar o release mais recente
    result = agent.process_latest_release()
    
    if result:
        print(f"\n✅ Análise concluída com sucesso!")
    else:
        print("\n❌ Não foi possível realizar a análise")


if __name__ == "__main__":
    main()