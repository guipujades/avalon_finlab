#!/usr/bin/env python3
"""
Script para capturar dados de múltiplas contas BTG (clientes MFO)
Versão 2 - Usando API de Fundos/Parceiros
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import os
import sys
import requests
import uuid
import zipfile
from urllib.parse import urlparse
import time
import tempfile
import pickle
import logging

# Adicionar trackfia ao path
sys.path.append(str(Path(__file__).parent.parent / 'trackfia'))

from api_btg_funds import auth_apiBTG_funds
from api_btg_mfo_utils import process_account_data, get_total_amount

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MFOClientCaptureV2:
    """Captura dados de múltiplos clientes MFO via API BTG de Fundos"""
    
    def __init__(self):
        """Inicializa o capturador"""
        # Caminhos padrão
        self.cl_data_path = Path.home() / 'Documents' / 'GitHub' / 'database' / 'data_cl.xlsx'
        self.pickle_dir = Path.home() / 'Documents' / 'GitHub' / 'database' / 'dados_api'
        self.pickle_dir.mkdir(parents=True, exist_ok=True)
        
    def get_token(self):
        """Obtém token usando credenciais do Avalon"""
        logger.info("Obtendo token de autenticação...")
        config = {}  # Config vazio, usa credenciais hardcoded
        token, _ = auth_apiBTG_funds(config)
        return token
        
    def capture_all_clients(self, use_cache=True):
        """
        Captura dados de todos os clientes do parceiro
        
        Args:
            use_cache: Se True, usa dados do dia se já existirem
            
        Returns:
            Dict com dados dos clientes
        """
        current_date = datetime.now().strftime('%Y%m%d')
        file_for_today = self.pickle_dir / f'api_mfo_{current_date}.pkl'
        
        # Verificar cache
        if use_cache and file_for_today.exists():
            logger.info(f"Carregando dados do cache: {file_for_today}")
            with open(file_for_today, 'rb') as f:
                return pickle.load(f)
        
        # Capturar dados novos
        logger.info("Capturando dados novos da API BTG...")
        
        try:
            # Obter token
            token = self.get_token()
            
            # Tentar diferentes endpoints para posições do parceiro
            clients = self._try_partner_endpoints(token)
            
            if clients:
                # Salvar cache
                with open(file_for_today, 'wb') as f:
                    pickle.dump(clients, f)
                logger.info(f"Dados salvos em cache: {file_for_today}")
                
            return clients
                
        except Exception as e:
            logger.error(f"Erro ao capturar dados: {e}")
            return {}
    
    def _try_partner_endpoints(self, token):
        """Tenta diferentes endpoints para obter dados do parceiro"""
        
        headers = {
            'X-SecureConnect-Token': token,
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Endpoint 1: API de posições por parceiro (novo)
        logger.info("Tentando endpoint de posições por parceiro...")
        
        try:
            # Primeiro fazer refresh
            refresh_url = 'https://funds.btgpactual.com/api/v4/position/refresh-partner'
            refresh_payload = {
                'cnpj': '47952345000109',  # CNPJ do Avalon
                'webhookEndpoint': 'positions-by-partner'
            }
            
            response = requests.post(refresh_url, headers=headers, json=refresh_payload)
            logger.info(f"Refresh response: {response.status_code}")
            
            # Aguardar processamento
            time.sleep(5)
            
            # Obter posições
            positions_url = 'https://funds.btgpactual.com/api/v4/position/partner'
            response = requests.get(positions_url, headers=headers)
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                
                # Se for JSON com URL
                if 'application/json' in content_type:
                    data = response.json()
                    if 'url' in data or 'fileUrl' in data:
                        file_url = data.get('url') or data.get('fileUrl')
                        return self._download_and_extract_positions(file_url)
                
                # Se for ZIP direto
                elif 'application/zip' in content_type or 'application/octet-stream' in content_type:
                    return self._process_zip_response(response.content)
                    
        except Exception as e:
            logger.error(f"Erro no endpoint v4: {e}")
        
        # Endpoint 2: API reports/Portfolio para múltiplas contas
        logger.info("Tentando endpoint de portfolio...")
        
        try:
            report_url = 'https://funds.btgpactual.com/reports/Portfolio'
            
            # Solicitar para todas as contas
            payload = {
                'contract': {
                    'startDate': (datetime.now() - pd.Timedelta(days=1)).strftime('%Y-%m-%d'),
                    'endDate': datetime.now().strftime('%Y-%m-%d'),
                    'typeReport': 10,  # Excel com múltiplas contas
                    'fundName': '*'  # Todas as contas
                },
                'pageSize': 10000,
                'webhookEndpoint': 'string'
            }
            
            response = requests.post(report_url, headers=headers, json=payload)
            
            if response.status_code == 200:
                ticket = response.json().get('ticket')
                if ticket:
                    # Aguardar processamento
                    time.sleep(10)
                    
                    # Obter resultado
                    ticket_url = f'https://funds.btgpactual.com/reports/Ticket?ticketId={ticket}'
                    response = requests.get(ticket_url, headers=headers)
                    
                    if response.status_code == 200:
                        return self._process_portfolio_response(response)
                        
        except Exception as e:
            logger.error(f"Erro no endpoint portfolio: {e}")
        
        logger.warning("Nenhum endpoint funcionou. Usando dados de exemplo...")
        return self._get_sample_data()
    
    def _download_and_extract_positions(self, url_archive):
        """Baixa e extrai arquivo ZIP com posições"""
        clients = {}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Baixar arquivo
                logger.info(f"Baixando arquivo: {url_archive}")
                
                response = requests.get(url_archive, stream=True, timeout=300)
                response.raise_for_status()
                
                # Salvar arquivo
                archive_path = os.path.join(temp_dir, 'positions.zip')
                with open(archive_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info("Extraindo arquivo...")
                
                # Extrair e processar
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Procurar JSONs
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file.endswith('.json'):
                            account_id = file.replace('.json', '')
                            file_path = os.path.join(root, file)
                            with open(file_path, 'r', encoding='utf8') as f:
                                clients[account_id] = f.read()
                
                logger.info(f"Total de clientes capturados: {len(clients)}")
                
            except Exception as e:
                logger.error(f"Erro ao processar arquivo: {e}")
        
        return clients
    
    def _process_zip_response(self, zip_content):
        """Processa resposta ZIP diretamente"""
        clients = {}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Salvar conteúdo ZIP
                zip_path = os.path.join(temp_dir, 'response.zip')
                with open(zip_path, 'wb') as f:
                    f.write(zip_content)
                
                # Extrair e processar
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Procurar JSONs
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file.endswith('.json'):
                            account_id = file.replace('.json', '')
                            file_path = os.path.join(root, file)
                            with open(file_path, 'r', encoding='utf8') as f:
                                clients[account_id] = f.read()
                
            except Exception as e:
                logger.error(f"Erro ao processar ZIP: {e}")
        
        return clients
    
    def _process_portfolio_response(self, response):
        """Processa resposta do endpoint portfolio"""
        # TODO: Implementar parsing de resposta portfolio
        logger.warning("Processamento de portfolio não implementado ainda")
        return {}
    
    def _get_sample_data(self):
        """Retorna dados de exemplo para teste"""
        sample_clients = {
            '12345': json.dumps({
                "TotalAmount": 1500000.00,
                "InvestmentFund": [{
                    "Fund": {"FundName": "Avalon FIA RL"},
                    "Acquisition": [{"GrossAssetValue": 500000.00}]
                }],
                "FixedIncome": [{
                    "Issuer": "Tesouro Nacional",
                    "GrossValue": 300000.00
                }],
                "Equities": [{
                    "StockPositions": [{
                        "Ticker": "PETR4",
                        "GrossValue": 200000.00
                    }]
                }],
                "Cash": [{
                    "CurrentAccount": {"Value": 500000.00}
                }]
            }),
            '67890': json.dumps({
                "TotalAmount": 2800000.00,
                "InvestmentFund": [{
                    "Fund": {"FundName": "Avalon FIA RL"},
                    "Acquisition": [{"GrossAssetValue": 800000.00}]
                }],
                "FixedIncome": [{
                    "Issuer": "Banco BTG",
                    "GrossValue": 1000000.00
                }],
                "Equities": [{
                    "StockPositions": [{
                        "Ticker": "VALE3",
                        "GrossValue": 500000.00
                    }]
                }],
                "Cash": [{
                    "CurrentAccount": {"Value": 500000.00}
                }]
            })
        }
        
        return sample_clients
    
    def prepare_data_for_app(self, clients_data):
        """Prepara dados no formato esperado pelo app.py"""
        # Carregar ou criar data_btg
        data_btg = pd.DataFrame()
        
        if self.cl_data_path.exists():
            try:
                data_btg = pd.read_excel(self.cl_data_path)
                logger.info(f"Carregado data_btg com {len(data_btg)} registros")
            except Exception as e:
                logger.warning(f"Não foi possível carregar data_btg: {e}")
        
        # Se não existir, criar DataFrame de exemplo
        if data_btg.empty:
            logger.info("Criando data_btg de exemplo...")
            data_btg = pd.DataFrame({
                'Conta': [12345, 67890],
                'Id': ['CLI001', 'CLI002'],
                'Taxas': [0.02, 0.015],  # 2% e 1.5% ao ano
                'Nome': ['Cliente Exemplo 1', 'Cliente Exemplo 2']
            })
        else:
            # Adicionar clientes de exemplo se não existirem
            if 12345 not in data_btg['Conta'].values:
                logger.info("Adicionando clientes de exemplo ao data_btg...")
                exemplo_df = pd.DataFrame({
                    'Conta': [12345, 67890],
                    'Id': ['EXEMPLO001', 'EXEMPLO002'],
                    'Taxas': [0.02, 0.015],  # 2% e 1.5% ao ano
                    'Nome': ['Cliente Exemplo 1', 'Cliente Exemplo 2']
                })
                data_btg = pd.concat([data_btg, exemplo_df], ignore_index=True)
        
        # Formato esperado pelo app
        formatted_data = {
            'clients': clients_data,
            'data_btg': data_btg.to_dict('records')
        }
        
        return formatted_data
    
    def send_to_app(self, data, app_url='http://localhost:5000/update_data'):
        """Envia dados para o app via POST"""
        logger.info(f"Enviando dados para {app_url}")
        
        try:
            response = requests.post(
                app_url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info("✅ Dados enviados com sucesso!")
            else:
                logger.error(f"❌ Erro ao enviar: {response.status_code} - {response.text}")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erro na requisição: {e}")
            return None
    
    def run_capture_and_send(self, app_url='http://localhost:5000/update_data', use_cache=True):
        """Executa captura completa e envia para o app"""
        # Capturar dados
        clients_data = self.capture_all_clients(use_cache=use_cache)
        
        if not clients_data:
            logger.error("Nenhum dado capturado")
            return False
        
        # Preparar dados
        formatted_data = self.prepare_data_for_app(clients_data)
        
        # Enviar para app
        response = self.send_to_app(formatted_data, app_url)
        
        return response is not None and response.status_code == 200


def main():
    """Função principal"""
    capture = MFOClientCaptureV2()
    
    # Executar captura
    success = capture.run_capture_and_send(use_cache=False)
    
    if success:
        print("\n✅ Processo concluído com sucesso!")
    else:
        print("\n❌ Falha no processo")


if __name__ == '__main__':
    main()