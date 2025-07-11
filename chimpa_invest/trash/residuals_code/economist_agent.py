"""
Agente Economista especializado em análise financeira do mercado brasileiro
"""
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import re


@dataclass
class FinancialIndicator:
    """Representa um indicador financeiro"""
    name: str
    value: float
    unit: str
    date: datetime
    source: str


class EconomistAgent:
    """
    Agente especializado em análise financeira brasileira
    """
    
    def __init__(self):
        self.indicators_cache = {}
        self.market_knowledge = self._initialize_market_knowledge()
        self.financial_metrics = self._initialize_financial_metrics()
        
    def _initialize_market_knowledge(self) -> Dict[str, Any]:
        """Inicializa base de conhecimento do mercado brasileiro"""
        return {
            'indices': {
                'SELIC': 'Taxa básica de juros da economia brasileira',
                'IPCA': 'Índice Nacional de Preços ao Consumidor Amplo',
                'IGP-M': 'Índice Geral de Preços - Mercado',
                'CDI': 'Certificado de Depósito Interbancário',
                'IBOVESPA': 'Índice da Bolsa de Valores de São Paulo',
                'IBRX100': 'Índice Brasil 100',
                'PTAX': 'Taxa de câmbio oficial'
            },
            'regulatory_bodies': {
                'CVM': 'Comissão de Valores Mobiliários',
                'BCB': 'Banco Central do Brasil',
                'B3': 'Brasil, Bolsa, Balcão',
                'ANBIMA': 'Associação Brasileira das Entidades dos Mercados Financeiro e de Capitais'
            },
            'financial_statements': {
                'DRE': 'Demonstração do Resultado do Exercício',
                'BP': 'Balanço Patrimonial',
                'DFC': 'Demonstração do Fluxo de Caixa',
                'DMPL': 'Demonstração das Mutações do Patrimônio Líquido',
                'DVA': 'Demonstração do Valor Adicionado',
                'DRA': 'Demonstração do Resultado Abrangente'
            }
        }
    
    def _initialize_financial_metrics(self) -> Dict[str, Dict[str, str]]:
        """Inicializa métricas financeiras padrão"""
        return {
            'profitability': {
                'ROE': 'Return on Equity - Retorno sobre Patrimônio Líquido',
                'ROA': 'Return on Assets - Retorno sobre Ativos',
                'ROIC': 'Return on Invested Capital - Retorno sobre Capital Investido',
                'margem_bruta': 'Lucro Bruto / Receita Líquida',
                'margem_operacional': 'EBIT / Receita Líquida',
                'margem_liquida': 'Lucro Líquido / Receita Líquida'
            },
            'liquidity': {
                'liquidez_corrente': 'Ativo Circulante / Passivo Circulante',
                'liquidez_seca': '(Ativo Circulante - Estoques) / Passivo Circulante',
                'liquidez_imediata': 'Disponibilidades / Passivo Circulante',
                'liquidez_geral': '(AC + RLP) / (PC + PNC)'
            },
            'leverage': {
                'divida_liquida_ebitda': 'Dívida Líquida / EBITDA',
                'divida_pl': 'Dívida Total / Patrimônio Líquido',
                'cobertura_juros': 'EBIT / Despesas Financeiras',
                'alavancagem_financeira': 'Ativo Total / Patrimônio Líquido'
            },
            'valuation': {
                'P/L': 'Preço / Lucro por Ação',
                'P/VPA': 'Preço / Valor Patrimonial por Ação',
                'EV/EBITDA': 'Enterprise Value / EBITDA',
                'PSR': 'Price to Sales Ratio - Preço / Receita',
                'dividend_yield': 'Dividendos por Ação / Preço da Ação'
            }
        }
    
    def analyze_financial_statement(self, statement_data: Dict[str, Any], 
                                  statement_type: str) -> Dict[str, Any]:
        """
        Analisa demonstração financeira
        
        Args:
            statement_data: Dados da demonstração
            statement_type: Tipo (DRE, BP, DFC, etc)
            
        Returns:
            Análise estruturada
        """
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'statement_type': statement_type,
            'key_metrics': {},
            'trends': [],
            'alerts': [],
            'insights': []
        }
        
        if statement_type == 'DRE':
            analysis['key_metrics'] = self._analyze_income_statement(statement_data)
        elif statement_type == 'BP':
            analysis['key_metrics'] = self._analyze_balance_sheet(statement_data)
        elif statement_type == 'DFC':
            analysis['key_metrics'] = self._analyze_cash_flow(statement_data)
            
        return analysis
    
    def _analyze_income_statement(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Analisa DRE e calcula métricas de rentabilidade"""
        metrics = {}
        
        if 'receita_liquida' in data and data['receita_liquida'] > 0:
            if 'lucro_bruto' in data:
                metrics['margem_bruta'] = data['lucro_bruto'] / data['receita_liquida']
            if 'ebit' in data:
                metrics['margem_operacional'] = data['ebit'] / data['receita_liquida']
            if 'lucro_liquido' in data:
                metrics['margem_liquida'] = data['lucro_liquido'] / data['receita_liquida']
                
        return metrics
    
    def _analyze_balance_sheet(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Analisa Balanço Patrimonial e calcula métricas de estrutura"""
        metrics = {}
        
        if 'ativo_circulante' in data and 'passivo_circulante' in data:
            if data['passivo_circulante'] > 0:
                metrics['liquidez_corrente'] = data['ativo_circulante'] / data['passivo_circulante']
                
        if 'patrimonio_liquido' in data and data['patrimonio_liquido'] > 0:
            if 'lucro_liquido' in data:
                metrics['roe'] = data['lucro_liquido'] / data['patrimonio_liquido']
            if 'divida_total' in data:
                metrics['divida_pl'] = data['divida_total'] / data['patrimonio_liquido']
                
        return metrics
    
    def _analyze_cash_flow(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Analisa DFC e avalia geração de caixa"""
        metrics = {}
        
        if 'caixa_operacional' in data:
            metrics['geracao_caixa_operacional'] = data['caixa_operacional']
            
        if 'capex' in data and 'caixa_operacional' in data:
            metrics['fcf'] = data['caixa_operacional'] - abs(data['capex'])
            
        return metrics
    
    def interpret_earnings_release(self, document_content: str, 
                                 company_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Interpreta release de resultados
        
        Args:
            document_content: Conteúdo do release
            company_data: Dados adicionais da empresa
            
        Returns:
            Interpretação estruturada
        """
        interpretation = {
            'summary': '',
            'highlights': [],
            'financial_metrics': {},
            'yoy_comparison': {},
            'guidance': {},
            'risks': [],
            'opportunities': []
        }
        
        # Extrai números e percentuais
        numbers = self._extract_financial_numbers(document_content)
        
        # Identifica seções principais
        sections = self._identify_document_sections(document_content)
        
        # Analisa cada seção
        for section_name, section_content in sections.items():
            if 'resultado' in section_name.lower() or 'ebitda' in section_name.lower():
                interpretation['financial_metrics'].update(
                    self._extract_metrics_from_text(section_content)
                )
            elif 'guidance' in section_name.lower() or 'perspectiva' in section_name.lower():
                interpretation['guidance'] = self._extract_guidance(section_content)
                
        return interpretation
    
    def _extract_financial_numbers(self, text: str) -> List[Dict[str, Any]]:
        """Extrai números financeiros do texto"""
        numbers = []
        
        # Padrões para valores monetários
        money_pattern = r'R\$\s*([\d.,]+)\s*(milhões?|bilhões?|mil)?'
        percentage_pattern = r'([\d.,]+)\s*%'
        
        for match in re.finditer(money_pattern, text):
            value = match.group(1).replace('.', '').replace(',', '.')
            multiplier = match.group(2)
            
            final_value = float(value)
            if multiplier:
                if 'mil' in multiplier:
                    final_value *= 1000
                elif 'milhõ' in multiplier:
                    final_value *= 1000000
                elif 'bilhõ' in multiplier:
                    final_value *= 1000000000
                    
            numbers.append({
                'type': 'monetary',
                'value': final_value,
                'original': match.group(0)
            })
            
        for match in re.finditer(percentage_pattern, text):
            numbers.append({
                'type': 'percentage',
                'value': float(match.group(1).replace(',', '.')),
                'original': match.group(0)
            })
            
        return numbers
    
    def _identify_document_sections(self, text: str) -> Dict[str, str]:
        """Identifica seções do documento"""
        sections = {}
        
        # Padrões comuns de títulos de seção
        section_patterns = [
            r'(?:^|\n)([A-Z][A-Z\s]{3,}):?\n',
            r'(?:^|\n)(\d+\.?\s*[A-Z][a-z\s]+):?\n',
            r'(?:^|\n)([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+)*):?\n'
        ]
        
        lines = text.split('\n')
        current_section = 'intro'
        current_content = []
        
        for line in lines:
            is_header = False
            for pattern in section_patterns:
                if re.match(pattern, line + '\n'):
                    if current_content:
                        sections[current_section] = '\n'.join(current_content)
                    current_section = line.strip().rstrip(':')
                    current_content = []
                    is_header = True
                    break
                    
            if not is_header:
                current_content.append(line)
                
        if current_content:
            sections[current_section] = '\n'.join(current_content)
            
        return sections
    
    def _extract_metrics_from_text(self, text: str) -> Dict[str, float]:
        """Extrai métricas financeiras do texto"""
        metrics = {}
        
        # Padrões para métricas comuns
        metric_patterns = {
            'receita': r'receita.*?R\$\s*([\d.,]+)\s*(milhões?|bilhões?)',
            'ebitda': r'ebitda.*?R\$\s*([\d.,]+)\s*(milhões?|bilhões?)',
            'lucro_liquido': r'lucro\s+líquido.*?R\$\s*([\d.,]+)\s*(milhões?|bilhões?)',
            'margem_ebitda': r'margem\s+ebitda.*?([\d.,]+)\s*%'
        }
        
        for metric_name, pattern in metric_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).replace('.', '').replace(',', '.')
                metrics[metric_name] = float(value)
                
        return metrics
    
    def _extract_guidance(self, text: str) -> Dict[str, Any]:
        """Extrai guidance/perspectivas do texto"""
        guidance = {
            'production': {},
            'sales': {},
            'capex': {},
            'other': []
        }
        
        # Busca por termos relacionados a projeções
        projection_terms = ['espera', 'projeta', 'estima', 'meta', 'objetivo', 'guidance']
        
        sentences = text.split('.')
        for sentence in sentences:
            if any(term in sentence.lower() for term in projection_terms):
                # Extrai números da sentença
                numbers = self._extract_financial_numbers(sentence)
                if numbers:
                    guidance['other'].append({
                        'text': sentence.strip(),
                        'values': numbers
                    })
                    
        return guidance
    
    def compare_with_market(self, company_metrics: Dict[str, float], 
                          sector: str) -> Dict[str, Any]:
        """
        Compara métricas da empresa com médias do setor
        
        Args:
            company_metrics: Métricas da empresa
            sector: Setor de atuação
            
        Returns:
            Comparação com benchmarks
        """
        # Aqui seria integrado com base de dados de mercado
        # Por ora, retorna estrutura exemplo
        return {
            'sector': sector,
            'company_position': {},
            'peer_comparison': {},
            'market_percentile': {}
        }
    
    def generate_investment_thesis(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gera tese de investimento baseada nas análises
        
        Args:
            analysis_data: Dados consolidados das análises
            
        Returns:
            Tese de investimento estruturada
        """
        thesis = {
            'rating': '',  # buy, hold, sell
            'target_price': 0.0,
            'upside_potential': 0.0,
            'key_drivers': [],
            'risks': [],
            'catalysts': [],
            'time_horizon': '',
            'confidence_level': ''
        }
        
        # Lógica de geração da tese seria implementada aqui
        
        return thesis