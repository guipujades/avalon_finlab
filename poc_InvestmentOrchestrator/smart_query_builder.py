import os
import json
from typing import Dict, Set, List, Tuple
from datetime import datetime
from pathlib import Path

class SmartSearchQueryBuilder:
    """Construtor inteligente de queries de busca com base em keywords organizadas"""
    
    def __init__(self, keywords_dir: str = "keywords"):
        self.keywords_dir = keywords_dir
        self.keywords_cache = {}
        self.companies_data = {}
        self.company_names = set()
        self.all_tickers = set()
        self._ensure_keywords_structure()
        self._load_all_keywords()
    
    def _ensure_keywords_structure(self):
        """Garante que a estrutura de diretórios e arquivos existe"""
        os.makedirs(self.keywords_dir, exist_ok=True)
        
        # Cria arquivos básicos se não existirem
        basic_files = {
            "market_keywords.txt": self._get_market_keywords(),
            "financial_companies.txt": self._get_financial_companies(),
            "temporal_keywords.txt": self._get_temporal_keywords(),
            "currency_keywords.txt": self._get_currency_keywords(),
            "economic_indicators.txt": self._get_economic_indicators()
        }
        
        for filename, content in basic_files.items():
            filepath = os.path.join(self.keywords_dir, filename)
            if not os.path.exists(filepath):
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
    
    def _get_market_keywords(self) -> str:
        """Retorna keywords básicas de mercado"""
        return """mercado
bolsa
ações
índice
bovespa
b3
nasdaq
dow jones
s&p
s&p500
nyse
ibovespa
pregão
blue chips
small caps
day trade
mercado futuro
opções
derivativos
commodities
forex
renda fixa
renda variável
fundos imobiliários
fiis
etf
bdr
ipo
home broker
análise técnica
análise fundamentalista
volatilidade
liquidez
dividendos
valuation
market cap"""
    
    def _get_financial_companies(self) -> str:
        """Retorna empresas básicas com tickers"""
        return """# Formato: NOME|TICKER1,TICKER2
petrobras|PETR3,PETR4
vale|VALE3
itaú unibanco|ITUB3,ITUB4
bradesco|BBDC3,BBDC4
banco do brasil|BBAS3
ambev|ABEV3
magazine luiza|MGLU3
via|VIIA3
weg|WEGE3
suzano|SUZB3
jbs|JBSS3
marfrig|MRFG3
brf|BRFS3
mrv|MRVE3
cyrela|CYRE3
gol|GOLL4
azul|AZUL4
tim|TIMS3
telefônica brasil|VIVT3
cemig|CMIG3,CMIG4
copel|CPLE3,CPLE6
eletrobras|ELET3,ELET6
gerdau|GGBR3,GGBR4
usiminas|USIM3,USIM5
csn|CSNA3
natura|NTCO3
lojas renner|LREN3
hapvida|HAPV3
fleury|FLRY3
raia drogasil|RADL3
multiplan|MULT3
localiza|RENT3
rumo|RAIL3
ultrapar|UGPA3
cosan|CSAN3"""
    
    def _get_temporal_keywords(self) -> str:
        """Retorna keywords temporais"""
        return """hoje
agora
atual
atualmente
recente
ontem
amanhã
esta semana
este mês
último
próximo
tempo real
ao vivo
neste momento
últimas notícias
breaking news
urgente
momento atual
data de hoje
abertura do mercado
fechamento do mercado
pré-mercado
pós-mercado"""
    
    def _get_currency_keywords(self) -> str:
        """Retorna keywords de moedas"""
        return """dólar
euro
libra
iene
yuan
peso
real
reais
brl
usd
eur
gbp
jpy
câmbio
cotação
conversão
forex
fx
dólar americano
dólar comercial
dólar turismo
ptax
taxa de câmbio
casa de câmbio"""
    
    def _get_economic_indicators(self) -> str:
        """Retorna indicadores econômicos"""
        return """inflação
ipca
igpm
selic
taxa selic
juros
copom
pib
produto interno bruto
desemprego
taxa de desemprego
balança comercial
exportações
importações
dívida pública
arrecadação
fundamentos econômicos
política monetária
banco central
bacen
ministério da economia"""
    
    def _load_keywords_from_file(self, filename: str) -> Set[str]:
        """Carrega keywords de um arquivo"""
        filepath = os.path.join(self.keywords_dir, filename)
        keywords = set()
        
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                for line in file:
                    keyword = line.strip().lower()
                    if keyword and not keyword.startswith('#'):
                        keywords.add(keyword)
        except FileNotFoundError:
            pass
            
        return keywords
    
    def _load_companies_data(self):
        """Carrega dados de empresas com tickers"""
        self.companies_data = {}
        self.company_names = set()
        self.all_tickers = set()
        
        filepath = os.path.join(self.keywords_dir, 'financial_companies.txt')
        
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split('|')
                        if len(parts) == 2:
                            company_name = parts[0].strip().lower()
                            tickers = [t.strip().upper() for t in parts[1].split(',')]
                            
                            self.companies_data[company_name] = tickers
                            self.company_names.add(company_name)
                            self.all_tickers.update(tickers)
        except FileNotFoundError:
            pass
    
    def _load_all_keywords(self):
        """Carrega todas as keywords"""
        self.keywords_cache['market'] = self._load_keywords_from_file('market_keywords.txt')
        self.keywords_cache['temporal'] = self._load_keywords_from_file('temporal_keywords.txt')
        self.keywords_cache['currency'] = self._load_keywords_from_file('currency_keywords.txt')
        self.keywords_cache['economic'] = self._load_keywords_from_file('economic_indicators.txt')
        self._load_companies_data()
    
    def _check_keywords(self, query_lower: str, keyword_type: str) -> bool:
        """Verifica se a query contém keywords de um tipo"""
        return any(keyword in query_lower for keyword in self.keywords_cache.get(keyword_type, set()))
    
    def _find_companies_in_query(self, query_lower: str) -> List[Tuple[str, List[str]]]:
        """Encontra empresas mencionadas na query"""
        found_companies = []
        
        for company_name, tickers in self.companies_data.items():
            if company_name in query_lower:
                found_companies.append((company_name, tickers))
            else:
                # Verifica pelos tickers
                for ticker in tickers:
                    if ticker.lower() in query_lower:
                        found_companies.append((company_name, tickers))
                        break
        
        return found_companies
    
    def build_smart_search_query(self, original_query: str, analysis: Dict = None) -> str:
        """Constrói query inteligente para busca web"""
        
        query_lower = original_query.lower()
        
        # Detecção de contextos usando keywords
        is_market_query = self._check_keywords(query_lower, 'market')
        is_temporal_query = self._check_keywords(query_lower, 'temporal')
        is_currency_query = self._check_keywords(query_lower, 'currency')
        is_economic_query = self._check_keywords(query_lower, 'economic')
        
        # Busca empresas específicas
        found_companies = self._find_companies_in_query(query_lower)
        
        # Aplica orientações do Maestro se disponíveis
        maestro_guidance = analysis.get("maestro_guidance", {}) if analysis else {}
        if maestro_guidance:
            focus_points = maestro_guidance.get("focus_points", [])
            
            # Se Maestro sugere mercados internacionais
            for focus in focus_points:
                if any(market in focus.lower() for market in ["s&p 500", "nasdaq", "dow jones", "panorama geral"]):
                    if is_market_query and is_temporal_query:
                        return f"{original_query} S&P500 Nasdaq Dow Jones mercados mundiais índices globais"
        
        # Constrói queries baseadas no contexto
        if is_market_query and is_temporal_query:
            if "brasil" in query_lower or "bovespa" in query_lower or "b3" in query_lower:
                return "Bovespa B3 hoje índice ações Brasil mercado financeiro Ibovespa"
            elif "mundo" in query_lower or "global" in query_lower:
                return "stock market today global indices S&P500 Nasdaq Dow Jones world markets"
            else:
                return "mercado ações hoje Brasil Bovespa Ibovespa índices financeiro B3"
        
        # Para empresas específicas
        if found_companies and is_temporal_query:
            company_terms = []
            for company_name, tickers in found_companies[:3]:
                ticker_str = " ".join(tickers[:2])
                company_terms.append(f"{company_name.title()} {ticker_str}")
            
            return f"{' '.join(company_terms)} cotação preço ação hoje B3 bovespa"
        
        # Para câmbio
        if is_currency_query and is_temporal_query:
            currencies = ["dólar", "euro", "libra"]
            found_currencies = [c for c in currencies if c in query_lower]
            
            if found_currencies:
                return f"{' '.join(found_currencies)} hoje cotação real BRL câmbio forex"
            else:
                return "câmbio hoje dólar cotação real BRL forex"
        
        # Para indicadores econômicos
        if is_economic_query and is_temporal_query:
            indicators = []
            if "inflação" in query_lower or "ipca" in query_lower:
                indicators.append("IPCA inflação")
            if "selic" in query_lower or "juros" in query_lower:
                indicators.append("taxa Selic juros")
            if "pib" in query_lower:
                indicators.append("PIB crescimento")
            
            if indicators:
                return f"Brasil {' '.join(indicators)} {datetime.now().year} atual"
        
        # Para queries temporais genéricas
        if is_temporal_query:
            current_year = datetime.now().year
            return f"{original_query} Brasil {current_year}"
        
        # Fallback: query original
        return original_query
    
    def add_company(self, company_name: str, tickers: List[str]):
        """Adiciona nova empresa"""
        filepath = os.path.join(self.keywords_dir, 'financial_companies.txt')
        
        with open(filepath, 'a', encoding='utf-8') as file:
            tickers_str = ",".join(tickers)
            file.write(f"\n{company_name.lower()}|{tickers_str.upper()}")
        
        # Recarrega dados
        self._load_companies_data()
    
    def get_companies_info(self) -> Dict:
        """Retorna informações sobre as empresas carregadas"""
        return {
            "total_companies": len(self.companies_data),
            "total_tickers": len(self.all_tickers),
            "sample_companies": list(self.company_names)[:10]
        } 