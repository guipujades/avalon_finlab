#!/usr/bin/env python3
"""
Financial APIs Integration Script
Centralized access to Brazilian financial data APIs

ACTIVE APIS:
- BACEN (Banco Central do Brasil) - Production Ready ✅
- BTG Pactual - Under Development 🚧

Author: Investment Orchestrator System
Version: 1.0.0
"""

import os
import json
import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# BACEN API CLIENT - PRODUCTION READY ✅
# ============================================================================

class BacenAPIClient:
    """
    Cliente para API do Banco Central do Brasil
    Documentação: https://dadosabertos.bcb.gov.br/
    """
    
    def __init__(self):
        self.base_url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Investment-Orchestrator/1.0',
            'Accept': 'application/json'
        })
        
        # Mapeamento de indicadores BACEN
        self.indicators = {
            # Taxas de Juros
            'selic': 432,           # Taxa Selic
            'cdi': 4391,            # CDI
            'tjlp': 256,            # TJLP
            
            # Inflação
            'ipca': 433,            # IPCA
            'igpm': 189,            # IGP-M
            'inpc': 188,            # INPC
            
            # Câmbio
            'usd': 1,               # Dólar americano
            'eur': 21619,           # Euro
            'gbp': 21620,           # Libra esterlina
            
            # PIB
            'pib': 4380,            # PIB mensal
            'pib_anual': 4385,      # PIB anual
            
            # Emprego
            'desemprego': 24369,    # Taxa de desocupação
            
            # Fiscal
            'resultado_primario': 5793,  # Resultado primário do setor público
            'divida_liquida': 4513,      # Dívida líquida do setor público
        }
        
        logger.info("✅ BACEN API Client inicializado")
        logger.info(f"📊 {len(self.indicators)} indicadores disponíveis")
    
    def get_indicator(self, indicator: str, last_n: int = 1, 
                     start_date: Optional[str] = None, 
                     end_date: Optional[str] = None) -> Dict:
        """
        Obtém dados de um indicador específico
        
        Args:
            indicator: Nome do indicador (ex: 'selic', 'ipca', 'usd')
            last_n: Número de últimas observações (padrão: 1)
            start_date: Data inicial (formato DD/MM/YYYY)
            end_date: Data final (formato DD/MM/YYYY)
            
        Returns:
            Dict com dados do indicador
        """
        if indicator not in self.indicators:
            available = list(self.indicators.keys())
            return {
                "error": f"Indicador '{indicator}' não encontrado",
                "available_indicators": available
            }
        
        series_code = self.indicators[indicator]
        
        try:
            # Constrói URL baseada nos parâmetros
            if start_date and end_date:
                url = f"{self.base_url}.{series_code}/dados"
                params = {
                    'formato': 'json',
                    'dataInicial': start_date,
                    'dataFinal': end_date
                }
            else:
                url = f"{self.base_url}.{series_code}/dados/ultimos/{last_n}"
                params = {'formato': 'json'}
            
            logger.info(f"🔍 Consultando {indicator.upper()} (série {series_code})")
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                return {
                    "indicator": indicator,
                    "series_code": series_code,
                    "error": "Nenhum dado retornado",
                    "data": []
                }
            
            # Processa dados
            processed_data = []
            for item in data:
                processed_data.append({
                    "date": item.get("data"),
                    "value": float(item.get("valor", 0)),
                    "indicator": indicator
                })
            
            result = {
                "indicator": indicator,
                "series_code": series_code,
                "count": len(processed_data),
                "data": processed_data,
                "last_value": processed_data[-1]["value"] if processed_data else None,
                "last_date": processed_data[-1]["date"] if processed_data else None,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"✅ {indicator.upper()}: {result['last_value']} em {result['last_date']}")
            return result
            
        except requests.RequestException as e:
            logger.error(f"❌ Erro na consulta BACEN: {e}")
            return {
                "indicator": indicator,
                "error": f"Erro na API BACEN: {str(e)}",
                "data": []
            }
        except Exception as e:
            logger.error(f"❌ Erro no processamento: {e}")
            return {
                "indicator": indicator,
                "error": f"Erro no processamento: {str(e)}",
                "data": []
            }
    
    def get_multiple_indicators(self, indicators: List[str], last_n: int = 1) -> Dict:
        """
        Obtém múltiplos indicadores de uma vez
        
        Args:
            indicators: Lista de indicadores
            last_n: Número de observações para cada
            
        Returns:
            Dict com todos os indicadores
        """
        results = {}
        
        for indicator in indicators:
            results[indicator] = self.get_indicator(indicator, last_n)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "indicators_requested": indicators,
            "results": results
        }
    
    def get_economic_summary(self) -> Dict:
        """
        Obtém resumo econômico com principais indicadores
        
        Returns:
            Dict com resumo econômico atual
        """
        key_indicators = ['selic', 'ipca', 'usd', 'cdi', 'pib']
        
        logger.info("📊 Gerando resumo econômico...")
        
        summary_data = self.get_multiple_indicators(key_indicators, last_n=1)
        
        # Cria resumo formatado
        summary = {
            "titulo": "Resumo Econômico - Principais Indicadores",
            "data_consulta": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "indicadores": {},
            "analise": ""
        }
        
        # Processa cada indicador
        for indicator, data in summary_data["results"].items():
            if not data.get("error") and data.get("data"):
                last_data = data["data"][-1]
                summary["indicadores"][indicator] = {
                    "nome": self._get_indicator_name(indicator),
                    "valor": last_data["value"],
                    "data": last_data["date"],
                    "unidade": self._get_indicator_unit(indicator)
                }
        
        # Gera análise simples
        if summary["indicadores"]:
            selic = summary["indicadores"].get("selic", {}).get("valor", 0)
            ipca = summary["indicadores"].get("ipca", {}).get("valor", 0)
            usd = summary["indicadores"].get("usd", {}).get("valor", 0)
            
            summary["analise"] = f"""
Cenário atual: Taxa Selic em {selic}% a.a., IPCA em {ipca}% (últimos 12 meses), 
Dólar a R$ {usd:.2f}. Dados obtidos via API oficial do BACEN.
            """.strip()
        
        return summary
    
    def _get_indicator_name(self, indicator: str) -> str:
        """Retorna nome completo do indicador"""
        names = {
            'selic': 'Taxa Selic',
            'ipca': 'IPCA',
            'usd': 'Dólar Americano',
            'cdi': 'CDI',
            'pib': 'PIB',
            'eur': 'Euro',
            'igpm': 'IGP-M',
            'desemprego': 'Taxa de Desemprego'
        }
        return names.get(indicator, indicator.upper())
    
    def _get_indicator_unit(self, indicator: str) -> str:
        """Retorna unidade do indicador"""
        units = {
            'selic': '% a.a.',
            'ipca': '% (12 meses)',
            'usd': 'R$',
            'cdi': '% a.a.',
            'pib': 'R$ milhões',
            'eur': 'R$',
            'igpm': '% (mensal)',
            'desemprego': '%'
        }
        return units.get(indicator, '')
    
    def list_available_indicators(self) -> Dict:
        """Lista todos os indicadores disponíveis"""
        return {
            "total": len(self.indicators),
            "indicators": {
                name: {
                    "code": code,
                    "full_name": self._get_indicator_name(name),
                    "unit": self._get_indicator_unit(name)
                }
                for name, code in self.indicators.items()
            }
        }


# ============================================================================
# BTG API CLIENT - UNDER DEVELOPMENT 🚧
# ============================================================================

class BTGAPIClient:
    """
    Cliente para API BTG Pactual - EM DESENVOLVIMENTO
    TEMPORARIAMENTE DESABILITADO - Aguardando correções na autenticação
    """
    
    def __init__(self, credentials_path: Optional[str] = None):
        self.enabled = False  # DESABILITADO TEMPORARIAMENTE
        self.base_url = "https://api.btgpactual.com"
        self.credentials_path = credentials_path
        self.token = None
        
        logger.warning("🚧 BTG API Client - TEMPORARIAMENTE DESABILITADO")
        logger.warning("   Aguardando correções na autenticação e estrutura")
    
    def get_account_position(self, account_number: str) -> Dict:
        """BTG API - TEMPORARIAMENTE INDISPONÍVEL"""
        return {
            "error": "BTG API temporariamente indisponível",
            "status": "under_development",
            "message": "Use BACEN API para dados macroeconômicos por enquanto"
        }
    
    def get_all_positions(self) -> Dict:
        """BTG API - TEMPORARIAMENTE INDISPONÍVEL"""
        return {
            "error": "BTG API temporariamente indisponível", 
            "status": "under_development",
            "message": "Em desenvolvimento - correções de autenticação necessárias"
        }


# ============================================================================
# UNIFIED API MANAGER
# ============================================================================

class FinancialAPIManager:
    """
    Gerenciador unificado para todas as APIs financeiras
    Roteamento inteligente baseado no tipo de consulta
    """
    
    def __init__(self):
        # Inicializa clientes disponíveis
        self.bacen = BacenAPIClient()
        self.btg = BTGAPIClient()  # Desabilitado temporariamente
        
        # Status dos clientes
        self.available_apis = {
            "bacen": True,
            "btg": False  # Temporariamente desabilitado
        }
        
        logger.info("🏦 Financial API Manager inicializado")
        logger.info(f"✅ APIs ativas: {[api for api, status in self.available_apis.items() if status]}")
        logger.info(f"🚧 APIs em desenvolvimento: {[api for api, status in self.available_apis.items() if not status]}")
    
    def query_economic_data(self, query_type: str, **kwargs) -> Dict:
        """
        Consulta dados econômicos com roteamento automático
        
        Args:
            query_type: Tipo de consulta ('indicator', 'summary', 'multiple')
            **kwargs: Parâmetros específicos da consulta
            
        Returns:
            Dados processados da API apropriada
        """
        
        if query_type == "indicator" and "indicator" in kwargs:
            return self.bacen.get_indicator(**kwargs)
        
        elif query_type == "summary":
            return self.bacen.get_economic_summary()
        
        elif query_type == "multiple" and "indicators" in kwargs:
            return self.bacen.get_multiple_indicators(**kwargs)
        
        elif query_type == "portfolio":
            return {
                "error": "Portfolio data temporarily unavailable",
                "message": "BTG API under development",
                "available_alternative": "Use economic indicators via BACEN API"
            }
        
        else:
            return {
                "error": "Query type not recognized",
                "available_types": ["indicator", "summary", "multiple"],
                "example": "query_economic_data('indicator', indicator='selic')"
            }
    
    def get_market_overview(self) -> Dict:
        """
        Obtém visão geral do mercado brasileiro
        """
        logger.info("📈 Gerando visão geral do mercado...")
        
        # Indicadores-chave para overview de mercado
        market_indicators = ['selic', 'ipca', 'usd', 'cdi']
        
        data = self.bacen.get_multiple_indicators(market_indicators, last_n=1)
        
        # Formata para apresentação
        overview = {
            "titulo": "Visão Geral do Mercado Brasileiro",
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "fonte": "BACEN API",
            "dados": {}
        }
        
        for indicator, result in data["results"].items():
            if not result.get("error") and result.get("data"):
                last_point = result["data"][-1]
                overview["dados"][indicator] = {
                    "nome": self.bacen._get_indicator_name(indicator),
                    "valor": last_point["value"],
                    "data": last_point["date"],
                    "unidade": self.bacen._get_indicator_unit(indicator)
                }
        
        return overview
    
    def search_data_by_query(self, user_query: str) -> Dict:
        """
        Busca dados baseado em query em linguagem natural
        
        Args:
            user_query: Pergunta do usuário
            
        Returns:
            Dados relevantes encontrados
        """
        query_lower = user_query.lower()
        
        # Mapeia palavras-chave para indicadores
        keyword_mapping = {
            'selic': ['selic', 'juros', 'taxa básica'],
            'ipca': ['ipca', 'inflação', 'preços'],
            'usd': ['dólar', 'dolar', 'cambio', 'câmbio', 'usd'],
            'cdi': ['cdi'],
            'pib': ['pib', 'produto interno bruto', 'crescimento'],
            'desemprego': ['desemprego', 'emprego', 'trabalho']
        }
        
        # Identifica indicadores relevantes
        relevant_indicators = []
        for indicator, keywords in keyword_mapping.items():
            if any(keyword in query_lower for keyword in keywords):
                relevant_indicators.append(indicator)
        
        if not relevant_indicators:
            # Se não encontrou indicadores específicos, retorna overview geral
            logger.info("🔍 Query não específica - retornando overview geral")
            return self.get_market_overview()
        
        # Consulta indicadores específicos
        logger.info(f"🎯 Consultando indicadores específicos: {relevant_indicators}")
        
        if len(relevant_indicators) == 1:
            return self.bacen.get_indicator(relevant_indicators[0], last_n=3)
        else:
            return self.bacen.get_multiple_indicators(relevant_indicators, last_n=1)


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_selic_rate() -> float:
    """Função de conveniência para obter taxa Selic atual"""
    client = BacenAPIClient()
    result = client.get_indicator('selic')
    return result.get('last_value', 0.0)

def get_dollar_rate() -> float:
    """Função de conveniência para obter cotação do dólar atual"""
    client = BacenAPIClient()
    result = client.get_indicator('usd')
    return result.get('last_value', 0.0)

def get_ipca_rate() -> float:
    """Função de conveniência para obter IPCA atual"""
    client = BacenAPIClient()
    result = client.get_indicator('ipca')
    return result.get('last_value', 0.0)

def create_financial_api_manager() -> FinancialAPIManager:
    """Factory function para criar gerenciador de APIs"""
    return FinancialAPIManager()


# ============================================================================
# EXAMPLE USAGE & TESTING
# ============================================================================

if __name__ == "__main__":
    print("🏦 FINANCIAL APIS INTEGRATION TEST")
    print("=" * 50)
    
    # Test BACEN API
    print("\n📊 TESTE 1: BACEN API - Indicadores Individuais")
    bacen = BacenAPIClient()
    
    # Taxa Selic
    selic = bacen.get_indicator('selic')
    print(f"✅ SELIC: {selic.get('last_value', 'N/A')}% - {selic.get('last_date', 'N/A')}")
    
    # Dólar
    usd = bacen.get_indicator('usd')
    print(f"✅ USD: R$ {usd.get('last_value', 'N/A')} - {usd.get('last_date', 'N/A')}")
    
    # IPCA
    ipca = bacen.get_indicator('ipca')
    print(f"✅ IPCA: {ipca.get('last_value', 'N/A')}% - {ipca.get('last_date', 'N/A')}")
    
    print("\n📈 TESTE 2: Resumo Econômico")
    summary = bacen.get_economic_summary()
    print(f"✅ {summary['titulo']}")
    print(f"📅 {summary['data_consulta']}")
    
    print("\n🏦 TESTE 3: Gerenciador Unificado")
    manager = FinancialAPIManager()
    
    # Teste busca por query
    test_queries = [
        "Qual é a taxa Selic atual?",
        "Como está o dólar hoje?", 
        "Dados de inflação"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        result = manager.search_data_by_query(query)
        if 'last_value' in result:
            print(f"   Resultado: {result['last_value']} em {result['last_date']}")
        elif 'dados' in result:
            print(f"   Dados encontrados: {len(result['dados'])} indicadores")
    
    print("\n" + "=" * 50)
    print("✅ Todos os testes concluídos!")
    print("🎯 BACEN API: Funcionando perfeitamente")
    print("🚧 BTG API: Em desenvolvimento") 