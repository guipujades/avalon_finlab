"""
Base de conhecimento financeiro do mercado brasileiro
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class IndicatorCategory(Enum):
    """Categorias de indicadores"""
    MACROECONOMIC = "macroeconômico"
    MARKET = "mercado"
    COMPANY = "empresa"
    SECTOR = "setor"


class FinancialKnowledge:
    """
    Base de conhecimento sobre o mercado financeiro brasileiro
    """
    
    def __init__(self):
        self.indicators = self._build_indicators_database()
        self.glossary = self._build_glossary()
        self.formulas = self._build_formulas_database()
        self.benchmarks = self._build_benchmarks()
        
    def _build_indicators_database(self) -> Dict[str, Dict[str, Any]]:
        """Constrói base de indicadores brasileiros"""
        return {
            # Indicadores Macroeconômicos
            'SELIC': {
                'name': 'Taxa SELIC',
                'description': 'Sistema Especial de Liquidação e de Custódia - taxa básica de juros',
                'category': IndicatorCategory.MACROECONOMIC,
                'unit': '% a.a.',
                'source': 'BCB - Banco Central do Brasil',
                'frequency': 'COPOM meetings (8x/year)',
                'impact': 'Afeta custo de capital, valuations e decisões de investimento'
            },
            'IPCA': {
                'name': 'Índice Nacional de Preços ao Consumidor Amplo',
                'description': 'Inflação oficial do Brasil',
                'category': IndicatorCategory.MACROECONOMIC,
                'unit': '% mensal/anual',
                'source': 'IBGE',
                'frequency': 'Mensal',
                'impact': 'Indexador de títulos públicos (NTN-B) e contratos'
            },
            'IGP-M': {
                'name': 'Índice Geral de Preços - Mercado',
                'description': 'Inflação com peso maior no atacado',
                'category': IndicatorCategory.MACROECONOMIC,
                'unit': '% mensal/anual',
                'source': 'FGV',
                'frequency': 'Mensal',
                'impact': 'Usado em contratos de aluguel e concessões'
            },
            'CDI': {
                'name': 'Certificado de Depósito Interbancário',
                'description': 'Taxa de juros entre bancos',
                'category': IndicatorCategory.MACROECONOMIC,
                'unit': '% a.a.',
                'source': 'B3',
                'frequency': 'Diária',
                'impact': 'Benchmark para renda fixa e custo de funding'
            },
            'PIB': {
                'name': 'Produto Interno Bruto',
                'description': 'Soma de todos os bens e serviços produzidos',
                'category': IndicatorCategory.MACROECONOMIC,
                'unit': '% trimestral/anual',
                'source': 'IBGE',
                'frequency': 'Trimestral',
                'impact': 'Indicador de crescimento econômico'
            },
            'PTAX': {
                'name': 'Taxa de Câmbio PTAX',
                'description': 'Taxa média de câmbio R$/US$ do dia',
                'category': IndicatorCategory.MACROECONOMIC,
                'unit': 'R$/US$',
                'source': 'BCB',
                'frequency': 'Diária',
                'impact': 'Referência para contratos de câmbio'
            },
            
            # Índices de Mercado
            'IBOVESPA': {
                'name': 'Índice Bovespa',
                'description': 'Principal índice de ações do Brasil',
                'category': IndicatorCategory.MARKET,
                'unit': 'pontos',
                'source': 'B3',
                'frequency': 'Tempo real',
                'composition': 'Ações mais líquidas, revisão quadrimestral'
            },
            'IBRX100': {
                'name': 'Índice Brasil 100',
                'description': '100 ações mais negociadas',
                'category': IndicatorCategory.MARKET,
                'unit': 'pontos',
                'source': 'B3',
                'frequency': 'Tempo real',
                'composition': 'Ponderado por valor de mercado'
            },
            'IFIX': {
                'name': 'Índice de Fundos Imobiliários',
                'description': 'Índice de FIIs listados',
                'category': IndicatorCategory.MARKET,
                'unit': 'pontos',
                'source': 'B3',
                'frequency': 'Tempo real',
                'composition': 'FIIs mais líquidos'
            },
            'IDIV': {
                'name': 'Índice Dividendos',
                'description': 'Empresas com maiores dividend yields',
                'category': IndicatorCategory.MARKET,
                'unit': 'pontos',
                'source': 'B3',
                'frequency': 'Tempo real',
                'composition': 'Maiores pagadoras de dividendos'
            },
            'SMLL': {
                'name': 'Índice Small Cap',
                'description': 'Empresas de menor capitalização',
                'category': IndicatorCategory.MARKET,
                'unit': 'pontos',
                'source': 'B3',
                'frequency': 'Tempo real',
                'composition': 'Small caps com liquidez'
            }
        }
    
    def _build_glossary(self) -> Dict[str, Dict[str, str]]:
        """Constrói glossário PT-BR/EN"""
        return {
            # Demonstrações Financeiras
            'balanço_patrimonial': {
                'en': 'Balance Sheet',
                'description': 'Demonstra a posição patrimonial e financeira'
            },
            'demonstração_resultado': {
                'en': 'Income Statement',
                'acronym': 'DRE',
                'description': 'Resultado das operações no período'
            },
            'fluxo_caixa': {
                'en': 'Cash Flow Statement',
                'acronym': 'DFC',
                'description': 'Entradas e saídas de caixa'
            },
            'demonstração_valor_adicionado': {
                'en': 'Value Added Statement',
                'acronym': 'DVA',
                'description': 'Riqueza gerada e sua distribuição'
            },
            
            # Contas do Balanço
            'ativo': {
                'en': 'Assets',
                'description': 'Bens e direitos'
            },
            'ativo_circulante': {
                'en': 'Current Assets',
                'description': 'Realizável em até 12 meses'
            },
            'ativo_não_circulante': {
                'en': 'Non-current Assets',
                'description': 'Realizável após 12 meses'
            },
            'caixa_equivalentes': {
                'en': 'Cash and Cash Equivalents',
                'description': 'Dinheiro e aplicações de liquidez imediata'
            },
            'contas_receber': {
                'en': 'Accounts Receivable',
                'description': 'Valores a receber de clientes'
            },
            'estoques': {
                'en': 'Inventories',
                'description': 'Produtos para venda ou produção'
            },
            'imobilizado': {
                'en': 'Property, Plant and Equipment (PP&E)',
                'description': 'Ativos tangíveis de uso'
            },
            'intangível': {
                'en': 'Intangible Assets',
                'description': 'Ativos sem substância física'
            },
            'passivo': {
                'en': 'Liabilities',
                'description': 'Obrigações'
            },
            'passivo_circulante': {
                'en': 'Current Liabilities',
                'description': 'Exigível em até 12 meses'
            },
            'passivo_não_circulante': {
                'en': 'Non-current Liabilities',
                'description': 'Exigível após 12 meses'
            },
            'patrimônio_líquido': {
                'en': 'Shareholders\' Equity',
                'description': 'Capital próprio'
            },
            
            # Contas de Resultado
            'receita_líquida': {
                'en': 'Net Revenue',
                'description': 'Receita bruta menos deduções'
            },
            'custo_produtos_vendidos': {
                'en': 'Cost of Goods Sold (COGS)',
                'acronym': 'CPV',
                'description': 'Custo direto dos produtos/serviços'
            },
            'lucro_bruto': {
                'en': 'Gross Profit',
                'description': 'Receita líquida menos CPV'
            },
            'despesas_operacionais': {
                'en': 'Operating Expenses',
                'description': 'Despesas administrativas, vendas, etc'
            },
            'ebitda': {
                'en': 'EBITDA',
                'description': 'Earnings Before Interest, Taxes, Depreciation and Amortization'
            },
            'ebit': {
                'en': 'EBIT',
                'description': 'Earnings Before Interest and Taxes'
            },
            'resultado_financeiro': {
                'en': 'Financial Result',
                'description': 'Receitas menos despesas financeiras'
            },
            'lucro_antes_impostos': {
                'en': 'Earnings Before Taxes (EBT)',
                'description': 'EBIT + resultado financeiro'
            },
            'lucro_líquido': {
                'en': 'Net Income',
                'description': 'Resultado final após impostos'
            },
            
            # Indicadores
            'roe': {
                'en': 'Return on Equity',
                'description': 'Retorno sobre Patrimônio Líquido'
            },
            'roa': {
                'en': 'Return on Assets',
                'description': 'Retorno sobre Ativos'
            },
            'roic': {
                'en': 'Return on Invested Capital',
                'description': 'Retorno sobre Capital Investido'
            },
            'margem_bruta': {
                'en': 'Gross Margin',
                'description': 'Lucro bruto / Receita líquida'
            },
            'margem_ebitda': {
                'en': 'EBITDA Margin',
                'description': 'EBITDA / Receita líquida'
            },
            'margem_líquida': {
                'en': 'Net Margin',
                'description': 'Lucro líquido / Receita líquida'
            },
            'liquidez_corrente': {
                'en': 'Current Ratio',
                'description': 'Ativo circulante / Passivo circulante'
            },
            'liquidez_seca': {
                'en': 'Quick Ratio',
                'description': '(AC - Estoques) / PC'
            },
            'dívida_líquida': {
                'en': 'Net Debt',
                'description': 'Dívida total - Caixa'
            },
            'alavancagem': {
                'en': 'Leverage',
                'description': 'Dívida líquida / EBITDA'
            },
            
            # Múltiplos
            'p_l': {
                'en': 'P/E Ratio',
                'description': 'Preço / Lucro por ação'
            },
            'p_vpa': {
                'en': 'P/B Ratio',
                'description': 'Preço / Valor patrimonial por ação'
            },
            'ev_ebitda': {
                'en': 'EV/EBITDA',
                'description': 'Enterprise Value / EBITDA'
            },
            'dividend_yield': {
                'en': 'Dividend Yield',
                'description': 'Dividendos / Preço da ação'
            },
            'payout': {
                'en': 'Payout Ratio',
                'description': 'Dividendos / Lucro líquido'
            },
            
            # Termos de Mercado
            'ipo': {
                'en': 'Initial Public Offering',
                'description': 'Oferta pública inicial de ações'
            },
            'follow_on': {
                'en': 'Follow-on',
                'description': 'Oferta subsequente de ações'
            },
            'tag_along': {
                'en': 'Tag Along',
                'description': 'Direito de venda conjunta'
            },
            'free_float': {
                'en': 'Free Float',
                'description': 'Ações em circulação no mercado'
            },
            'market_cap': {
                'en': 'Market Capitalization',
                'description': 'Valor de mercado da empresa'
            },
            'guidance': {
                'en': 'Guidance',
                'description': 'Projeções da administração'
            },
            'covenant': {
                'en': 'Covenant',
                'description': 'Cláusula restritiva em contratos'
            }
        }
    
    def _build_formulas_database(self) -> Dict[str, Dict[str, Any]]:
        """Constrói base de fórmulas financeiras"""
        return {
            # Indicadores de Rentabilidade
            'roe': {
                'formula': 'Lucro Líquido / Patrimônio Líquido Médio',
                'interpretation': 'Quanto maior, melhor. Benchmark: > 15% a.a.',
                'adjustments': ['Excluir itens não recorrentes', 'Usar PL médio do período']
            },
            'roa': {
                'formula': 'Lucro Líquido / Ativo Total Médio',
                'interpretation': 'Eficiência no uso dos ativos. Benchmark: > 5%',
                'adjustments': ['Considerar ativos operacionais']
            },
            'roic': {
                'formula': 'NOPAT / Capital Investido',
                'components': {
                    'NOPAT': 'EBIT * (1 - taxa de imposto)',
                    'Capital Investido': 'Patrimônio Líquido + Dívida Líquida'
                },
                'interpretation': 'Deve superar o WACC'
            },
            
            # Indicadores de Liquidez
            'liquidez_corrente': {
                'formula': 'Ativo Circulante / Passivo Circulante',
                'interpretation': 'Ideal > 1,5. Varia por setor',
                'limitations': ['Não considera qualidade dos ativos']
            },
            'liquidez_seca': {
                'formula': '(Ativo Circulante - Estoques) / Passivo Circulante',
                'interpretation': 'Ideal > 1,0. Mais conservador',
                'limitations': ['Ignora prazos de recebimento']
            },
            'liquidez_imediata': {
                'formula': 'Disponibilidades / Passivo Circulante',
                'interpretation': 'Capacidade imediata de pagamento',
                'limitations': ['Muito conservador']
            },
            
            # Indicadores de Endividamento
            'divida_liquida_ebitda': {
                'formula': 'Dívida Líquida / EBITDA',
                'interpretation': 'Ideal < 3,0x. Covenant comum',
                'adjustments': ['EBITDA últimos 12 meses']
            },
            'divida_pl': {
                'formula': 'Dívida Total / Patrimônio Líquido',
                'interpretation': 'Alavancagem financeira',
                'sector_variance': 'Varia muito por setor'
            },
            'cobertura_juros': {
                'formula': 'EBIT / Despesas Financeiras',
                'interpretation': 'Ideal > 2,0x',
                'risk': '< 1,0x indica alto risco'
            },
            
            # Múltiplos de Valuation
            'p_l': {
                'formula': 'Preço da Ação / Lucro por Ação',
                'interpretation': 'Comparar com setor e crescimento',
                'variations': ['P/L trailing', 'P/L forward']
            },
            'ev_ebitda': {
                'formula': 'Enterprise Value / EBITDA',
                'components': {
                    'EV': 'Market Cap + Dívida Líquida'
                },
                'interpretation': 'Menos afetado por estrutura de capital'
            },
            'peg_ratio': {
                'formula': 'P/L / Taxa de Crescimento',
                'interpretation': 'PEG < 1 pode indicar subvalorização',
                'limitations': ['Assume crescimento linear']
            },
            
            # Análise DuPont
            'dupont_roe': {
                'formula': 'Margem Líquida × Giro do Ativo × Alavancagem',
                'components': {
                    'Margem Líquida': 'Lucro Líquido / Receita',
                    'Giro do Ativo': 'Receita / Ativo Total',
                    'Alavancagem': 'Ativo Total / Patrimônio Líquido'
                },
                'interpretation': 'Decompõe drivers do ROE'
            },
            
            # Métricas de Eficiência
            'giro_estoque': {
                'formula': 'CPV / Estoque Médio',
                'interpretation': 'Quantas vezes o estoque gira no ano',
                'days_formula': '365 / Giro do Estoque'
            },
            'prazo_medio_recebimento': {
                'formula': '(Contas a Receber / Receita) × 365',
                'interpretation': 'Dias para receber vendas',
                'trend': 'Menor é melhor'
            },
            'ciclo_conversao_caixa': {
                'formula': 'PME + PMR - PMP',
                'components': {
                    'PME': 'Prazo Médio Estoques',
                    'PMR': 'Prazo Médio Recebimento',
                    'PMP': 'Prazo Médio Pagamento'
                },
                'interpretation': 'Dias entre pagar fornecedores e receber clientes'
            }
        }
    
    def _build_benchmarks(self) -> Dict[str, Dict[str, Any]]:
        """Constrói benchmarks por setor"""
        return {
            'varejo': {
                'margem_ebitda': {'min': 5, 'max': 15, 'ideal': 10},
                'liquidez_corrente': {'min': 1.0, 'max': 2.0, 'ideal': 1.5},
                'giro_estoque': {'min': 4, 'max': 12, 'ideal': 8},
                'divida_liquida_ebitda': {'min': 0, 'max': 3, 'ideal': 2}
            },
            'industria': {
                'margem_ebitda': {'min': 10, 'max': 25, 'ideal': 18},
                'liquidez_corrente': {'min': 1.2, 'max': 2.5, 'ideal': 1.8},
                'giro_estoque': {'min': 3, 'max': 8, 'ideal': 5},
                'divida_liquida_ebitda': {'min': 0, 'max': 4, 'ideal': 2.5}
            },
            'servicos': {
                'margem_ebitda': {'min': 15, 'max': 35, 'ideal': 25},
                'liquidez_corrente': {'min': 0.8, 'max': 1.5, 'ideal': 1.2},
                'giro_estoque': {'min': None, 'max': None, 'ideal': None},
                'divida_liquida_ebitda': {'min': 0, 'max': 2.5, 'ideal': 1.5}
            },
            'utilities': {
                'margem_ebitda': {'min': 25, 'max': 45, 'ideal': 35},
                'liquidez_corrente': {'min': 0.8, 'max': 1.5, 'ideal': 1.1},
                'giro_estoque': {'min': None, 'max': None, 'ideal': None},
                'divida_liquida_ebitda': {'min': 2, 'max': 5, 'ideal': 3.5}
            },
            'financeiro': {
                'roe': {'min': 10, 'max': 20, 'ideal': 15},
                'roa': {'min': 0.8, 'max': 2, 'ideal': 1.5},
                'eficiencia': {'min': 40, 'max': 60, 'ideal': 50},
                'basileia': {'min': 11, 'max': 20, 'ideal': 15}
            }
        }
    
    def get_indicator_info(self, indicator_code: str) -> Optional[Dict[str, Any]]:
        """Retorna informações sobre um indicador"""
        return self.indicators.get(indicator_code.upper())
    
    def translate_term(self, term: str, to_english: bool = True) -> Optional[str]:
        """Traduz termo financeiro PT-BR <-> EN"""
        term_lower = term.lower().replace(' ', '_')
        
        if term_lower in self.glossary:
            if to_english and 'en' in self.glossary[term_lower]:
                return self.glossary[term_lower]['en']
            elif not to_english:
                # Busca reversa
                for pt_term, info in self.glossary.items():
                    if info.get('en', '').lower() == term_lower:
                        return pt_term.replace('_', ' ').title()
        
        return None
    
    def get_formula(self, metric: str) -> Optional[Dict[str, Any]]:
        """Retorna fórmula e interpretação de uma métrica"""
        metric_key = metric.lower().replace(' ', '_')
        return self.formulas.get(metric_key)
    
    def get_sector_benchmark(self, sector: str, metric: str) -> Optional[Dict[str, float]]:
        """Retorna benchmark de uma métrica para um setor"""
        sector_lower = sector.lower()
        metric_lower = metric.lower().replace(' ', '_')
        
        if sector_lower in self.benchmarks:
            return self.benchmarks[sector_lower].get(metric_lower)
            
        return None
    
    def explain_metric(self, metric: str, value: float, 
                      sector: Optional[str] = None) -> Dict[str, Any]:
        """
        Explica uma métrica e avalia o valor
        
        Args:
            metric: Nome da métrica
            value: Valor da métrica
            sector: Setor da empresa (opcional)
            
        Returns:
            Explicação e avaliação
        """
        explanation = {
            'metric': metric,
            'value': value,
            'formula': None,
            'interpretation': None,
            'evaluation': None,
            'benchmark': None
        }
        
        # Busca fórmula
        formula_info = self.get_formula(metric)
        if formula_info:
            explanation['formula'] = formula_info.get('formula')
            explanation['interpretation'] = formula_info.get('interpretation')
        
        # Busca benchmark do setor
        if sector:
            benchmark = self.get_sector_benchmark(sector, metric)
            if benchmark:
                explanation['benchmark'] = benchmark
                
                # Avalia valor
                if benchmark.get('ideal') is not None:
                    ideal = benchmark['ideal']
                    min_val = benchmark.get('min', 0)
                    max_val = benchmark.get('max', ideal * 2)
                    
                    if value < min_val:
                        explanation['evaluation'] = 'Abaixo do mínimo'
                    elif value > max_val:
                        explanation['evaluation'] = 'Acima do máximo'
                    elif abs(value - ideal) / ideal < 0.1:
                        explanation['evaluation'] = 'Próximo ao ideal'
                    elif value < ideal:
                        explanation['evaluation'] = 'Abaixo do ideal'
                    else:
                        explanation['evaluation'] = 'Acima do ideal'
                        
        return explanation