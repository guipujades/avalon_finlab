#!/usr/bin/env python3
"""
Manager simplificado que usa apenas dados da API XML
Não depende de arquivos Excel externos
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def run_manager_xml_simple(df_xml=None):
    """
    Processa portfolio diretamente do XML da API BTG
    Retorna portfolio e operações vazias (sem dependência de Excel)
    """
    try:
        portfolio = {}
        
        if df_xml is not None and not df_xml.empty:
            # Processar ações (tipo ACOES)
            df_stocks = df_xml[df_xml['tipo'] == 'ACOES'].copy()
            
            for idx, row in df_stocks.iterrows():
                ticker = row.get('codigo', '').strip()
                if ticker:
                    quantity = float(row.get('quantidade', 0))
                    avg_price = float(row.get('preco_medio', 0))
                    
                    # Se não tiver preço médio, usar valor financeiro / quantidade
                    if avg_price == 0 and quantity > 0:
                        valor_fin = float(row.get('valorfindisp', 0))
                        avg_price = valor_fin / quantity if quantity > 0 else 0
                    
                    portfolio[ticker] = {
                        'quantity': quantity,
                        'average_price': avg_price,
                        'type': 'stock'
                    }
            
            # Processar opções (tipo OPCOES)
            df_options = df_xml[df_xml['tipo'] == 'OPCOES'].copy()
            
            for idx, row in df_options.iterrows():
                ticker = row.get('codigo', '').strip()
                if ticker:
                    quantity = float(row.get('quantidade', 0))
                    avg_price = float(row.get('preco_medio', 0))
                    
                    # Para opções, o preço pode estar em centavos
                    if avg_price < 1 and avg_price > 0:
                        avg_price = avg_price * 100
                    
                    portfolio[ticker] = {
                        'quantity': quantity,
                        'average_price': avg_price,
                        'type': 'option'
                    }
        
        # Retornar portfolio e DataFrame vazio de operações
        df_operations = pd.DataFrame()
        
        logger.info(f"Portfolio processado: {len(portfolio)} ativos")
        return portfolio, df_operations
        
    except Exception as e:
        logger.error(f"Erro ao processar portfolio: {e}")
        return {}, pd.DataFrame()