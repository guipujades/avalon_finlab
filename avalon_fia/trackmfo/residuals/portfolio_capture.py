"""
Módulo para captura de dados de múltiplas carteiras de investimento
Baseado na API BTG para coleta de dados de fundos e carteiras
"""

import json
import os
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Dict, List, Tuple, Optional
import pickle

# Importar módulos do trackfia (pasta irmã)
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / 'trackfia'))

from api_btg_funds import auth_apiBTG_funds, refresh_partner_positions, portfolio_api_with_refresh
from btg_api_client import BTGAPIClient

# Importar módulo local
from api_btg_mfo_utils import process_account_data, get_total_amount

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PortfolioCaptureConfig:
    """Configuração para captura de portfolios"""
    
    def __init__(self):
        self.database_path = Path.home() / 'Documents' / 'GitHub' / 'database' / 'portfolio_data'
        self.database_path.mkdir(parents=True, exist_ok=True)
        
        # Credenciais para diferentes tipos de contas
        self.credentials = {
            'funds': {
                'client_id': 'guilherme magalhães',
                'client_secret': 'Cg21092013PM#'
            },
            'digital': {
                # Carregar de arquivo JSON se existir
                'config_path': Path.home() / 'Desktop' / 'api_btg_info.json'
            }
        }
        
        # Lista de fundos/carteiras para capturar
        self.portfolios = {
            'avalon_fia': {
                'type': 'fund',
                'name': 'AVALON FIA',
                'cnpj': '47952345000109'
            },
            # Adicionar outras carteiras conforme necessário
        }


class PortfolioCapture:
    """Classe principal para captura de dados de portfolios"""
    
    def __init__(self, config: PortfolioCaptureConfig):
        self.config = config
        self.captured_data = {}
        
    def capture_fund_data(self, fund_info: Dict) -> Dict:
        """
        Captura dados de um fundo específico
        
        Args:
            fund_info: Informações do fundo (name, cnpj, etc)
            
        Returns:
            Dict com dados capturados
        """
        logger.info(f"Capturando dados do fundo: {fund_info['name']}")
        
        try:
            # Autenticar
            token, _ = auth_apiBTG_funds(self.config.credentials['funds'])
            
            # Fazer refresh das posições
            refresh_partner_positions(token, fund_info['cnpj'])
            time.sleep(3)
            
            # Definir período
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            # Capturar dados XML
            response = portfolio_api_with_refresh(
                token=token,
                data=None,
                start_date=start_date,
                end_date=end_date,
                type_report=3,  # XML
                page_size=1000
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Processar dados conforme tipo
                processed_data = self._process_fund_xml_data(data)
                
                return {
                    'success': True,
                    'fund_name': fund_info['name'],
                    'capture_date': datetime.now(),
                    'data': processed_data,
                    'raw_data': data
                }
            else:
                logger.error(f"Erro ao capturar dados: {response.status_code}")
                return {
                    'success': False,
                    'fund_name': fund_info['name'],
                    'error': response.text
                }
                
        except Exception as e:
            logger.error(f"Erro na captura: {str(e)}")
            return {
                'success': False,
                'fund_name': fund_info['name'],
                'error': str(e)
            }
    
    def capture_digital_account_data(self, account_info: Dict) -> Dict:
        """
        Captura dados de uma conta digital usando BTGAPIClient
        
        Args:
            account_info: Informações da conta (deve conter account_id ou account_number)
            
        Returns:
            Dict com dados capturados
        """
        logger.info(f"Capturando dados da conta digital: {account_info.get('name', 'Unknown')}")
        
        try:
            # Carregar configuração
            config_path = self.config.credentials['digital']['config_path']
            
            # Criar cliente BTG
            if config_path.exists():
                client = BTGAPIClient(credentials_path=str(config_path))
            else:
                # Tentar usar credenciais padrão se existirem
                logger.warning("Arquivo de configuração não encontrado, tentando credenciais padrão")
                client = BTGAPIClient(
                    client_id=self.config.credentials.get('digital', {}).get('client_id'),
                    client_secret=self.config.credentials.get('digital', {}).get('client_secret')
                )
            
            # Se temos um número de conta específico
            if 'account_number' in account_info or 'account_id' in account_info:
                account_number = account_info.get('account_number', account_info.get('account_id'))
                
                # Obter posição da conta
                positions = client.get_account_position(account_number)
                
                if positions:
                    # Processar dados usando o utilitário MFO
                    processed = process_account_data(json.dumps(positions))
                    
                    return {
                        'success': True,
                        'capture_date': datetime.now(),
                        'account_name': account_info.get('name'),
                        'account_number': account_number,
                        'data': processed,
                        'raw_data': positions,
                        'total_amount': get_total_amount(json.dumps(positions))
                    }
                else:
                    return {
                        'success': False,
                        'error': 'No positions found'
                    }
            
            # Se não temos conta específica, tentar obter todas as contas do parceiro
            else:
                logger.info("Obtendo posições de todas as contas do parceiro")
                all_accounts_info = client.get_all_accounts_positions()
                
                return {
                    'success': True,
                    'capture_date': datetime.now(),
                    'message': 'Posições do parceiro solicitadas',
                    'data': all_accounts_info,
                    'note': 'Os dados serão enviados via webhook conforme configurado na API'
                }
            
        except Exception as e:
            logger.error(f"Erro na captura digital: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def capture_all_portfolios(self) -> Dict:
        """
        Captura dados de todos os portfolios configurados
        
        Returns:
            Dict com todos os dados capturados
        """
        logger.info("Iniciando captura de todos os portfolios")
        
        results = {}
        
        for portfolio_id, portfolio_info in self.config.portfolios.items():
            logger.info(f"Processando: {portfolio_id}")
            
            if portfolio_info['type'] == 'fund':
                result = self.capture_fund_data(portfolio_info)
            elif portfolio_info['type'] == 'digital':
                result = self.capture_digital_account_data(portfolio_info)
            else:
                logger.warning(f"Tipo desconhecido: {portfolio_info['type']}")
                continue
            
            results[portfolio_id] = result
            
            # Pequeno delay entre capturas
            time.sleep(2)
        
        self.captured_data = results
        return results
    
    def save_captured_data(self, format='pickle') -> str:
        """
        Salva os dados capturados
        
        Args:
            format: Formato de salvamento (pickle, json, excel)
            
        Returns:
            Path do arquivo salvo
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'pickle':
            file_path = self.config.database_path / f'portfolio_capture_{timestamp}.pkl'
            with open(file_path, 'wb') as f:
                pickle.dump(self.captured_data, f)
        
        elif format == 'json':
            file_path = self.config.database_path / f'portfolio_capture_{timestamp}.json'
            # Converter datetime para string para JSON
            data_for_json = self._prepare_for_json(self.captured_data)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data_for_json, f, ensure_ascii=False, indent=2)
        
        elif format == 'excel':
            file_path = self.config.database_path / f'portfolio_capture_{timestamp}.xlsx'
            self._save_to_excel(file_path)
        
        logger.info(f"Dados salvos em: {file_path}")
        return str(file_path)
    
    def _process_fund_xml_data(self, raw_data: Dict) -> Dict:
        """
        Processa dados XML de um fundo
        
        Args:
            raw_data: Dados brutos da API
            
        Returns:
            Dict com dados processados
        """
        # Implementar processamento específico para XML de fundos
        # Baseado no código existente em api_btg_funds
        
        processed = {
            'positions': [],
            'summary': {},
            'asset_allocation': {}
        }
        
        # Extrair e processar posições
        # TODO: Implementar parsing XML completo
        
        return processed
    
    def _prepare_for_json(self, data: Dict) -> Dict:
        """Prepara dados para serialização JSON"""
        if isinstance(data, dict):
            return {k: self._prepare_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._prepare_for_json(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        elif isinstance(data, pd.DataFrame):
            return data.to_dict('records')
        else:
            return data
    
    def _save_to_excel(self, file_path: Path):
        """Salva dados em formato Excel com múltiplas abas"""
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            for portfolio_id, data in self.captured_data.items():
                if data.get('success'):
                    # Criar DataFrame resumo
                    summary_df = pd.DataFrame([{
                        'Portfolio': portfolio_id,
                        'Capture Date': data.get('capture_date'),
                        'Status': 'Success'
                    }])
                    summary_df.to_excel(writer, sheet_name=f'{portfolio_id}_summary', index=False)
                    
                    # Adicionar outros dados conforme disponível
                    # TODO: Expandir para incluir posições detalhadas
    
    def generate_summary_report(self) -> pd.DataFrame:
        """
        Gera relatório resumido de todos os portfolios capturados
        
        Returns:
            DataFrame com resumo
        """
        summary_data = []
        
        for portfolio_id, data in self.captured_data.items():
            if data.get('success'):
                summary_data.append({
                    'Portfolio ID': portfolio_id,
                    'Portfolio Name': data.get('fund_name', data.get('account_name', 'Unknown')),
                    'Capture Date': data.get('capture_date'),
                    'Status': 'Success',
                    'Total Value': self._extract_total_value(data)
                })
            else:
                summary_data.append({
                    'Portfolio ID': portfolio_id,
                    'Portfolio Name': 'Unknown',
                    'Capture Date': datetime.now(),
                    'Status': 'Failed',
                    'Error': data.get('error', 'Unknown error')
                })
        
        return pd.DataFrame(summary_data)
    
    def _extract_total_value(self, data: Dict) -> float:
        """Extrai valor total do portfolio dos dados capturados"""
        # Implementar lógica específica para cada tipo de portfolio
        return 0.0


def main():
    """Função principal para testes"""
    config = PortfolioCaptureConfig()
    capture = PortfolioCapture(config)
    
    # Capturar todos os portfolios
    results = capture.capture_all_portfolios()
    
    # Salvar dados
    capture.save_captured_data('pickle')
    capture.save_captured_data('json')
    
    # Gerar relatório
    summary = capture.generate_summary_report()
    print("\nResumo da Captura:")
    print(summary)


if __name__ == '__main__':
    main()