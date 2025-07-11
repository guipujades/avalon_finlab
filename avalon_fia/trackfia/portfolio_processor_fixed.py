#!/usr/bin/env python3
"""
Processador de portfolio corrigido que trabalha com dados da lista XML
Sem dependências de pandas/numpy
"""

import pickle as pkl
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

def process_portfolio_from_api_fixed():
    """
    Processa portfolio diretamente dos dados da lista XML da API BTG
    Retorna dados limpos sem NaN
    """
    try:
        current_date = datetime.now().strftime('%Y-%m-%d')
        # Detectar se está no Windows ou WSL
        import platform
        if platform.system() == 'Windows':
            pickle_dir = Path('C:/Users/guilh/Documents/GitHub/database/dados_api')
        else:
            pickle_dir = Path('/mnt/c/Users/guilh/Documents/GitHub/database/dados_api')
        
        # Buscar arquivos mais recentes
        data_files = sorted(pickle_dir.glob('data_xml_*.pkl'), reverse=True)
        header_files = sorted(pickle_dir.glob('header_*.pkl'), reverse=True)
        
        if not data_files or not header_files:
            logger.warning("Arquivos de dados não encontrados")
            return {}
        
        # Carregar dados
        with open(data_files[0], 'rb') as f:
            data_xml = pkl.load(f)
        
        with open(header_files[0], 'rb') as f:
            header = pkl.load(f)
        
        logger.info(f"Dados carregados: {len(data_xml)} ativos")
        
        # Processar ativos
        stocks = {}
        options = {}
        positions = {}
        other_assets = {}
        
        # Separar por tipo
        acoes_count = 0
        opcoes_count = 0
        outros_count = 0
        
        for asset in data_xml:
            try:
                tipo = asset.get('tipo', '').lower()
                
                # Identificar ações e opções
                if tipo == 'acoes':
                    codigo = (safe_get_string(asset, 'codigo') or 
                             safe_get_string(asset, 'cusip') or
                             safe_get_string(asset, 'codativo'))
                    if codigo:
                        stocks[codigo] = process_stock_asset(asset)
                        positions[codigo] = stocks[codigo]
                        acoes_count += 1
                        
                elif tipo == 'opcoes':
                    codigo = (safe_get_string(asset, 'codigo') or 
                             safe_get_string(asset, 'cusip') or
                             safe_get_string(asset, 'codativo'))
                    if codigo:
                        options[codigo] = process_option_asset(asset)
                        positions[codigo] = options[codigo]
                        opcoes_count += 1
                        
                else:
                    # Outros tipos (títulos públicos, etc.)
                    codigo = safe_get_string(asset, 'cusip') or safe_get_string(asset, 'isin') or safe_get_string(asset, 'codativo')
                    if codigo:
                        other_assets[codigo] = process_other_asset(asset)
                        outros_count += 1
                
            except Exception as e:
                logger.warning(f"Erro ao processar ativo {asset.get('codigo', 'N/A')}: {e}")
                continue
        
        # Calcular percentuais do portfolio
        total_value = sum(pos.get('current_value', 0) for pos in positions.values())
        if total_value > 0:
            for pos in positions.values():
                pos['pcts_port'] = (pos.get('current_value', 0) / total_value) * 100
        
        logger.info(f"Portfolio processado: {acoes_count} ações, {opcoes_count} opções, {outros_count} outros")
        
        return {
            'positions': positions,
            'stocks': stocks,
            'options': options,
            'other_assets': other_assets,
            'header': header,
            'total_assets': len(data_xml),
            'summary': {
                'stocks_count': acoes_count,
                'options_count': opcoes_count,
                'other_count': outros_count
            }
        }
        
    except Exception as e:
        logger.error(f"Erro ao processar portfolio: {e}")
        return {}

def process_stock_asset(asset):
    """Processa um ativo de ações"""
    codigo = (safe_get_string(asset, 'codigo') or 
             safe_get_string(asset, 'cusip') or
             safe_get_string(asset, 'codativo'))
    quantidade = (safe_get_float(asset, 'quantidade') or 
                 safe_get_float(asset, 'qtdisponivel'))
    preco_medio = (safe_get_float(asset, 'precomedio') or
                  safe_get_float(asset, 'puposicao'))
    valor_atual = safe_get_float(asset, 'valorfindisp')
    
    # Se não tiver preço médio mas tiver valor e quantidade
    if preco_medio == 0 and quantidade > 0 and valor_atual > 0:
        preco_medio = valor_atual / quantidade
    
    return {
        'quantity': quantidade,
        'average_price': preco_medio,
        'current_value': valor_atual,
        'current_price': preco_medio,  # Será atualizado pelo MT5 se disponível
        'initial_value': preco_medio * quantidade,
        'profit_loss': 0,  # Será calculado com preços atuais
        'percentage_change': 0,
        'pcts_port': 0,  # Será calculado depois
        'type': 'stock'
    }

def process_option_asset(asset):
    """Processa um ativo de opções"""
    codigo = (safe_get_string(asset, 'codigo') or 
             safe_get_string(asset, 'cusip') or
             safe_get_string(asset, 'codativo'))
    quantidade = (safe_get_float(asset, 'quantidade') or 
                 safe_get_float(asset, 'qtdisponivel'))
    preco_medio = (safe_get_float(asset, 'precomedio') or
                  safe_get_float(asset, 'puposicao'))
    valor_atual = safe_get_float(asset, 'valorfindisp')
    
    # Para opções, o preço pode estar em centavos
    if preco_medio < 1 and preco_medio > 0:
        preco_medio = preco_medio * 100
    
    return {
        'quantity': quantidade,
        'average_price': preco_medio,
        'current_value': valor_atual,
        'current_price': preco_medio,
        'initial_value': preco_medio * quantidade,
        'profit_loss': 0,
        'percentage_change': 0,
        'pcts_port': 0,
        'type': 'option'
    }

def process_other_asset(asset):
    """Processa outros tipos de ativos (títulos, etc.)"""
    codigo = safe_get_string(asset, 'cusip') or safe_get_string(asset, 'isin') or safe_get_string(asset, 'codativo')
    quantidade = safe_get_float(asset, 'qtdisponivel')
    preco_unitario = safe_get_float(asset, 'puposicao')
    valor_atual = safe_get_float(asset, 'valorfindisp')
    
    return {
        'quantity': quantidade,
        'average_price': preco_unitario,
        'current_value': valor_atual,
        'current_price': preco_unitario,
        'initial_value': valor_atual,  # Para títulos, assumir que valor atual = inicial
        'profit_loss': 0,
        'percentage_change': 0,
        'pcts_port': 0,
        'type': 'other',
        'asset_type': asset.get('tipo', 'unknown')
    }

def safe_get_string(data, key):
    """Obtém string de forma segura"""
    value = data.get(key, '')
    if value is None:
        return ''
    return str(value).strip()

def safe_get_float(data, key):
    """Obtém float de forma segura, tratando NaN e valores inválidos"""
    try:
        value = data.get(key, 0)
        
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

def test_processor():
    """Testar o processador"""
    print("🧪 Testando Processador Corrigido")
    print("=" * 50)
    
    portfolio_data = process_portfolio_from_api_fixed()
    
    if portfolio_data:
        positions = portfolio_data.get('positions', {})
        stocks = portfolio_data.get('stocks', {})
        options = portfolio_data.get('options', {})
        summary = portfolio_data.get('summary', {})
        
        print(f"✅ Portfolio processado:")
        print(f"  Total de posições: {len(positions)}")
        print(f"  Ações: {summary.get('stocks_count', 0)}")
        print(f"  Opções: {summary.get('options_count', 0)}")
        print(f"  Outros: {summary.get('other_count', 0)}")
        
        if stocks:
            print(f"\n📈 Ações encontradas:")
            for ticker, data in list(stocks.items())[:5]:
                print(f"  {ticker}:")
                print(f"    Quantidade: {data.get('quantity', 'N/A')}")
                print(f"    Preço Médio: R$ {data.get('average_price', 'N/A'):.2f}")
                print(f"    Valor Atual: R$ {data.get('current_value', 'N/A'):.2f}")
                print(f"    % Portfolio: {data.get('pcts_port', 'N/A'):.2f}%")
        
        if options:
            print(f"\n📉 Opções encontradas:")
            for ticker, data in list(options.items())[:3]:
                print(f"  {ticker}: R$ {data.get('current_value', 'N/A'):.2f}")
        
        return True
    else:
        print("❌ Falha ao processar portfolio")
        return False

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    test_processor()