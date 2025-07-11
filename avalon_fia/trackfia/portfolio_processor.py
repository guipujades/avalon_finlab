#!/usr/bin/env python3
"""
Processador de portfolio que trabalha diretamente com dados da API BTG
Sem dependências de pandas/numpy para evitar problemas de NaN
"""

import pickle as pkl
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

def process_portfolio_from_api():
    """
    Processa portfolio diretamente dos dados salvos da API BTG
    Retorna dados limpos sem NaN
    """
    try:
        current_date = datetime.now().strftime('%Y-%m-%d')
        pickle_dir = Path('/mnt/c/Users/guilh/Documents/GitHub/database/dados_api')
        
        # Caminhos dos arquivos
        df_xml_path = pickle_dir / f'df_xml_{current_date}.pkl'
        data_xml_path = pickle_dir / f'data_xml_{current_date}.pkl'
        header_path = pickle_dir / f'header_{current_date}.pkl'
        
        # Verificar se os arquivos existem
        if not all(p.exists() for p in [df_xml_path, data_xml_path, header_path]):
            logger.warning("Arquivos de dados não encontrados. Execute a atualização primeiro.")
            return {}, {}
        
        # Carregar dados
        with open(df_xml_path, 'rb') as f:
            df_xml = pkl.load(f)
        with open(header_path, 'rb') as f:
            header = pkl.load(f)
        
        logger.info(f"Dados carregados: {len(df_xml)} ativos")
        
        # Processar ações
        stocks = {}
        options = {}
        positions = {}
        
        for idx, row in df_xml.iterrows():
            try:
                # Extrair dados básicos
                codigo = str(row.get('codigo', '')).strip()
                tipo = str(row.get('tipo', '')).strip()
                
                if not codigo:
                    continue
                
                # Converter valores, tratando NaN
                quantidade = safe_float(row.get('quantidade', 0))
                preco_medio = safe_float(row.get('precomedio', 0))
                valor_atual = safe_float(row.get('valorfindisp', 0))
                
                # Se não tiver preço médio mas tiver valor e quantidade
                if preco_medio == 0 and quantidade > 0 and valor_atual > 0:
                    preco_medio = valor_atual / quantidade
                
                # Criar entrada do ativo
                asset_data = {
                    'quantity': quantidade,
                    'average_price': preco_medio,
                    'current_value': valor_atual,
                    'current_price': preco_medio,  # Será atualizado pelo MT5 se disponível
                    'initial_value': preco_medio * quantidade,
                    'profit_loss': 0,  # Será calculado com preços atuais
                    'percentage_change': 0,
                    'pcts_port': 0,  # Será calculado depois
                    'type': 'stock' if tipo == 'ACOES' else 'option' if tipo == 'OPCOES' else 'other'
                }
                
                # Adicionar aos dicionários apropriados
                positions[codigo] = asset_data
                
                if tipo == 'ACOES':
                    stocks[codigo] = asset_data
                elif tipo == 'OPCOES':
                    options[codigo] = asset_data
                
            except Exception as e:
                logger.warning(f"Erro ao processar ativo {codigo}: {e}")
                continue
        
        # Calcular percentuais do portfolio
        total_value = sum(pos['current_value'] for pos in positions.values())
        if total_value > 0:
            for pos in positions.values():
                pos['pcts_port'] = (pos['current_value'] / total_value) * 100
        
        logger.info(f"Portfolio processado: {len(stocks)} ações, {len(options)} opções")
        
        return {
            'positions': positions,
            'stocks': stocks,
            'options': options,
            'header': header,
            'total_assets': len(positions)
        }
        
    except Exception as e:
        logger.error(f"Erro ao processar portfolio: {e}")
        return {}, {}

def safe_float(value):
    """
    Converte valor para float de forma segura, tratando NaN e valores inválidos
    """
    try:
        if value is None:
            return 0.0
        
        # Se for string
        if isinstance(value, str):
            value = value.strip().replace(',', '.')
            if value == '' or value.lower() in ['nan', 'none', 'null']:
                return 0.0
        
        # Converter para float
        float_val = float(value)
        
        # Verificar se é NaN ou infinito
        if str(float_val).lower() in ['nan', 'inf', '-inf']:
            return 0.0
            
        return float_val
        
    except (ValueError, TypeError):
        return 0.0

def update_with_mt5_prices(portfolio_data):
    """
    Atualiza preços do portfolio com dados do MT5 se disponível
    """
    try:
        # Importar MT5 se disponível
        from mt5_connect import prepare_symbol, get_prices_mt5
        import MetaTrader5 as mt5
        
        updated_count = 0
        
        for ticker, data in portfolio_data['positions'].items():
            if data['quantity'] != 0:
                try:
                    prepare_symbol(ticker)
                    df_prices = get_prices_mt5(symbol=ticker, n=5, timeframe=mt5.TIMEFRAME_D1)
                    
                    if df_prices is not None and len(df_prices) > 0:
                        current_price = df_prices.iloc[-1]['Fechamento']
                        data['current_price'] = current_price
                        data['current_value'] = current_price * data['quantity']
                        data['profit_loss'] = data['current_value'] - data['initial_value']
                        
                        if data['initial_value'] > 0:
                            data['percentage_change'] = (data['profit_loss'] / data['initial_value']) * 100
                        
                        updated_count += 1
                        
                except Exception as e:
                    logger.warning(f"Erro ao atualizar preço de {ticker}: {e}")
                    continue
        
        logger.info(f"Preços atualizados para {updated_count} ativos")
        
        # Recalcular percentuais
        total_value = sum(pos['current_value'] for pos in portfolio_data['positions'].values())
        if total_value > 0:
            for pos in portfolio_data['positions'].values():
                pos['pcts_port'] = (pos['current_value'] / total_value) * 100
        
    except ImportError:
        logger.info("MT5 não disponível, usando preços médios")
    except Exception as e:
        logger.error(f"Erro ao atualizar com MT5: {e}")
    
    return portfolio_data