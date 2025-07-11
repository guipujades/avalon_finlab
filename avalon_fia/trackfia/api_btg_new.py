"""
Adaptador para integrar a nova API BTG com o código existente
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import logging
import zipfile
import tempfile
import requests
from typing import Optional, Dict, Tuple

from btg_api_client import BTGAPIClient, create_btg_client

logger = logging.getLogger(__name__)


def fund_data_new(find_type='positions', account_number: Optional[str] = None):
    """
    Versão atualizada da função fund_data usando a nova API BTG
    
    Args:
        find_type: 'positions' para posições ou 'info' para informações
        account_number: Número da conta (opcional)
        
    Returns:
        Dados da conta ou posições
    """
    try:
        # Criar cliente BTG
        client = create_btg_client()
        
        if find_type == 'positions':
            if account_number:
                # Posição de uma conta específica
                logger.info(f"Obtendo posição da conta {account_number}")
                position_data = client.get_account_position(account_number)
                
                # Converter para DataFrame se necessário
                df = process_position_data(position_data)
                
                # Extrair informações do header
                header = {
                    'dtposicao': datetime.now().strftime('%Y-%m-%d'),
                    'patliq': position_data.get('TotalAmount', 0),
                    'nome': f'Conta {account_number}'
                }
                
                return df, position_data, header
            else:
                # Todas as posições
                logger.info("Obtendo posições de todas as contas")
                all_positions = client.get_all_accounts_positions()
                
                # Processar resposta
                return process_all_positions(all_positions)
                
        elif find_type == 'info':
            if account_number:
                # Informações de conta específica
                info = client.get_account_info(account_number)
                return info
            else:
                logger.warning("Número da conta necessário para obter informações")
                return None
                
        else:
            logger.error(f"Tipo {find_type} não suportado")
            return None
            
    except Exception as e:
        logger.error(f"Erro ao obter dados: {e}")
        raise


def process_position_data(position_data: Dict) -> pd.DataFrame:
    """
    Processa dados de posição para DataFrame
    
    Args:
        position_data: Dados brutos da API
        
    Returns:
        DataFrame processado
    """
    records = []
    
    # Processar diferentes tipos de ativos
    if 'InvestmentFund' in position_data:
        for fund in position_data['InvestmentFund']:
            fund_info = fund.get('Fund', {})
            for acquisition in fund.get('Acquisition', []):
                records.append({
                    'tipo': 'Fundo',
                    'nome': fund_info.get('FundName', ''),
                    'cnpj': fund_info.get('CNPJFund', ''),
                    'quantidade': acquisition.get('Quantity', 0),
                    'valor': acquisition.get('GrossAssetValue', 0),
                    'data': acquisition.get('AcquisitionDate', '')
                })
    
    if 'Equities' in position_data:
        for equity in position_data['Equities']:
            for stock in equity.get('StockPositions', []):
                records.append({
                    'tipo': 'Ação',
                    'nome': stock.get('Ticker', ''),
                    'quantidade': stock.get('Quantity', 0),
                    'valor': stock.get('GrossValue', 0),
                    'preco_medio': stock.get('AveragePrice', 0)
                })
    
    if 'FixedIncome' in position_data:
        for bond in position_data['FixedIncome']:
            records.append({
                'tipo': 'Renda Fixa',
                'nome': bond.get('Issuer', ''),
                'valor': bond.get('GrossValue', 0),
                'vencimento': bond.get('MaturityDate', '')
            })
    
    return pd.DataFrame(records)


def process_all_positions(all_positions_response: Dict) -> Tuple[pd.DataFrame, list, dict]:
    """
    Processa resposta de todas as posições
    
    Args:
        all_positions_response: Resposta da API
        
    Returns:
        Tuple com DataFrame, lista de dados e header
    """
    # A resposta contém URLs para download
    download_url = all_positions_response.get('downloadUrl')
    
    if download_url:
        logger.info(f"Baixando arquivo de posições de {download_url}")
        
        # Fazer download do arquivo
        response = requests.get(download_url)
        
        if response.status_code == 200:
            # Salvar temporariamente
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
                tmp_file.write(response.content)
                tmp_path = tmp_file.name
            
            # Processar ZIP
            df, data_list, header = process_positions_zip(tmp_path)
            
            # Limpar arquivo temporário
            Path(tmp_path).unlink()
            
            return df, data_list, header
    
    logger.warning("URL de download não encontrada")
    return pd.DataFrame(), [], {}


def process_positions_zip(zip_path: str) -> Tuple[pd.DataFrame, list, dict]:
    """
    Processa arquivo ZIP de posições
    
    Args:
        zip_path: Caminho do arquivo ZIP
        
    Returns:
        Tuple com DataFrame, lista de dados e header
    """
    all_records = []
    header = {
        'dtposicao': datetime.now().strftime('%Y-%m-%d'),
        'patliq': 0,
        'nome': 'Consolidado Avalon'
    }
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Extrair para diretório temporário
        with tempfile.TemporaryDirectory() as tmp_dir:
            zip_ref.extractall(tmp_dir)
            
            # Processar cada arquivo
            for file_name in zip_ref.namelist():
                file_path = Path(tmp_dir) / file_name
                
                if file_path.suffix.lower() in ['.json', '.xml', '.csv']:
                    # Processar arquivo baseado no tipo
                    records = process_position_file(file_path)
                    all_records.extend(records)
    
    # Criar DataFrame consolidado
    df = pd.DataFrame(all_records)
    
    # Calcular patrimônio total
    if 'valor' in df.columns:
        header['patliq'] = df['valor'].sum()
    
    return df, all_records, header


def process_position_file(file_path: Path) -> list:
    """
    Processa arquivo individual de posição
    
    Args:
        file_path: Caminho do arquivo
        
    Returns:
        Lista de registros
    """
    records = []
    
    try:
        if file_path.suffix.lower() == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Processar JSON (adaptar conforme estrutura real)
                df = process_position_data(data)
                records = df.to_dict('records')
                
        elif file_path.suffix.lower() == '.csv':
            df = pd.read_csv(file_path)
            records = df.to_dict('records')
            
        # Adicionar outros formatos conforme necessário
        
    except Exception as e:
        logger.error(f"Erro ao processar {file_path}: {e}")
    
    return records


def get_account_movements_df(account_number: str, days_back: int = 30) -> pd.DataFrame:
    """
    Obtém movimentações de conta como DataFrame
    
    Args:
        account_number: Número da conta
        days_back: Dias para voltar no histórico
        
    Returns:
        DataFrame com movimentações
    """
    try:
        client = create_btg_client()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        movements = client.get_account_movements(
            account_number,
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        
        # Converter para DataFrame
        # Nota: A resposta real virá via webhook
        df = pd.DataFrame()  # Placeholder
        
        return df
        
    except Exception as e:
        logger.error(f"Erro ao obter movimentações: {e}")
        return pd.DataFrame()


# Funções de compatibilidade com código antigo
def auth_apiBTG(config):
    """Compatibilidade com função antiga"""
    try:
        client = BTGAPIClient(
            client_id=config.get('client_id'),
            client_secret=config.get('client_secret')
        )
        token = client.get_access_token()
        return token, config
    except Exception as e:
        logger.error(f"Erro na autenticação: {e}")
        raise


def fia_main_info(token, data):
    """Compatibilidade com função antiga - retorna informações mockadas"""
    return {
        'fundName': 'AVALON FIA',
        'cnpj': '47.952.345/0001-09',
        'type': 'FIA',
        'status': 'Ativo',
        'api_version': 'Nova API BTG'
    }


if __name__ == "__main__":
    # Teste básico
    print("🧪 Teste do adaptador da nova API")
    
    try:
        # Testar autenticação
        client = create_btg_client()
        if client.test_connection():
            print("✅ Conexão estabelecida!")
            
            # Testar obtenção de dados
            # Nota: Precisa de um número de conta válido
            # df, data, header = fund_data_new('positions', account_number='12345')
            
    except Exception as e:
        print(f"❌ Erro: {e}")