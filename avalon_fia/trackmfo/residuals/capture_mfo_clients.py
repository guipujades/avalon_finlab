#!/usr/bin/env python3
"""
Script para capturar dados de múltiplas contas BTG (clientes MFO)
Baseado no api_btg_mfo_main.py original
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

from btg_api_client import BTGAPIClient
from api_btg_mfo_utils import process_account_data, get_total_amount

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MFOClientCapture:
    """Captura dados de múltiplos clientes MFO via API BTG"""
    
    def __init__(self, credentials_path=None):
        """
        Inicializa o capturador
        
        Args:
            credentials_path: Caminho para arquivo de credenciais
        """
        # Caminhos padrão
        self.json_file_access = credentials_path or str(Path.home() / 'Desktop' / 'api_btg_info.json')
        self.cl_data_path = Path.home() / 'Documents' / 'GitHub' / 'database' / 'data_cl.xlsx'
        self.pickle_dir = Path.home() / 'Documents' / 'GitHub' / 'database' / 'dados_api'
        self.pickle_dir.mkdir(parents=True, exist_ok=True)
        
        # Cliente BTG
        self.btg_client = BTGAPIClient(credentials_path=self.json_file_access)
        
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
            token = self.btg_client.get_access_token()
            
            # Fazer requisição para obter posições do parceiro
            uuid_request = str(uuid.uuid4())
            url = 'https://api.btgpactual.com/iaas-api-position/api/v1/position/partner'
            
            headers = {
                'x-id-partner-request': uuid_request,
                'access_token': token
            }
            
            response = requests.get(url=url, headers=headers, timeout=60)
            response_data = response.json()
            
            if response_data.get('errors') is None:
                url_archive = response_data['response']['url']
                logger.info(f"URL do arquivo obtida: {url_archive}")
                
                # Baixar e extrair arquivo
                clients = self._download_and_extract_positions(url_archive)
                
                # Salvar cache
                with open(file_for_today, 'wb') as f:
                    pickle.dump(clients, f)
                logger.info(f"Dados salvos em cache: {file_for_today}")
                
                return clients
            else:
                logger.error(f"Erro na API: {response_data.get('errors')}")
                return {}
                
        except Exception as e:
            logger.error(f"Erro ao capturar dados: {e}")
            return {}
    
    def _download_and_extract_positions(self, url_archive):
        """
        Baixa e extrai arquivo ZIP com posições
        
        Args:
            url_archive: URL do arquivo ZIP
            
        Returns:
            Dict com dados dos clientes
        """
        clients = {}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Baixar arquivo
            logger.info("Baixando arquivo de posições...")
            
            # Extrair nome do arquivo da URL
            parsed_url = urlparse(url_archive)
            filename = os.path.basename(parsed_url.path)
            if not filename:
                filename = f"positions_{datetime.now().strftime('%Y%m%d')}.zip"
            
            archive_path = os.path.join(temp_dir, filename)
            
            # Baixar usando requests
            response = requests.get(url_archive, stream=True, timeout=300)
            response.raise_for_status()
            
            with open(archive_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Arquivo baixado: {archive_path}")
            
            # Extrair ZIP
            logger.info("Extraindo arquivo...")
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Encontrar pasta com JSONs
            pre_archive = os.path.splitext(archive_path)[0]
            number = os.path.basename(pre_archive)[:-9]
            path_archive = Path(temp_dir) / 'iaas-position-holder' / number / 'position'
            
            # Ler JSONs dos clientes
            logger.info(f"Lendo dados de {path_archive}")
            for filename in os.listdir(path_archive):
                if filename.endswith('.json'):
                    account_id = filename.replace('.json', '')
                    with open(path_archive / filename, 'r', encoding='utf8') as f:
                        clients[account_id] = f.read()
            
            logger.info(f"Total de clientes capturados: {len(clients)}")
            
        return clients
    
    def prepare_data_for_app(self, clients_data):
        """
        Prepara dados no formato esperado pelo app.py
        
        Args:
            clients_data: Dict com dados brutos dos clientes
            
        Returns:
            Dict no formato esperado pelo /update_data
        """
        # Carregar data_btg se existir
        data_btg = pd.DataFrame()
        
        if self.cl_data_path.exists():
            try:
                data_btg = pd.read_excel(self.cl_data_path)
                logger.info(f"Carregado data_btg com {len(data_btg)} registros")
            except Exception as e:
                logger.warning(f"Não foi possível carregar data_btg: {e}")
                # Criar DataFrame vazio com estrutura mínima
                data_btg = pd.DataFrame({
                    'Conta': [],
                    'Id': [],
                    'Taxas': []
                })
        
        # Formato esperado pelo app
        formatted_data = {
            'clients': clients_data,
            'data_btg': data_btg.to_dict('records')
        }
        
        return formatted_data
    
    def send_to_app(self, data, app_url='http://localhost:5000/update_data'):
        """
        Envia dados para o app via POST
        
        Args:
            data: Dados formatados
            app_url: URL do endpoint
            
        Returns:
            Response da requisição
        """
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
        """
        Executa captura completa e envia para o app
        
        Args:
            app_url: URL do app
            use_cache: Se deve usar cache
            
        Returns:
            Bool indicando sucesso
        """
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
    
    def get_summary(self):
        """
        Retorna resumo dos dados capturados
        
        Returns:
            Dict com resumo
        """
        current_date = datetime.now().strftime('%Y%m%d')
        file_for_today = self.pickle_dir / f'api_mfo_{current_date}.pkl'
        
        if not file_for_today.exists():
            return {'status': 'no_data', 'message': 'Nenhum dado capturado hoje'}
        
        with open(file_for_today, 'rb') as f:
            clients = pickle.load(f)
        
        total_value = 0
        client_summaries = []
        
        for client_id, data in clients.items():
            try:
                total_amount = get_total_amount(data)
                total_value += total_amount
                
                client_summaries.append({
                    'client_id': client_id,
                    'total_amount': total_amount
                })
            except:
                pass
        
        return {
            'status': 'success',
            'capture_date': current_date,
            'total_clients': len(clients),
            'total_value': total_value,
            'clients': client_summaries
        }


def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Captura dados MFO de múltiplas contas BTG')
    parser.add_argument('--app-url', default='http://localhost:5000/update_data', 
                        help='URL do endpoint do app')
    parser.add_argument('--no-cache', action='store_true', 
                        help='Forçar nova captura ignorando cache')
    parser.add_argument('--credentials', help='Caminho para arquivo de credenciais')
    parser.add_argument('--summary', action='store_true', help='Mostrar apenas resumo')
    
    args = parser.parse_args()
    
    # Criar capturador
    capture = MFOClientCapture(credentials_path=args.credentials)
    
    if args.summary:
        # Mostrar resumo
        summary = capture.get_summary()
        print(json.dumps(summary, indent=2))
    else:
        # Executar captura
        success = capture.run_capture_and_send(
            app_url=args.app_url,
            use_cache=not args.no_cache
        )
        
        if success:
            print("\n✅ Processo concluído com sucesso!")
            print("\nResumo:")
            print(json.dumps(capture.get_summary(), indent=2))
        else:
            print("\n❌ Falha no processo")


if __name__ == '__main__':
    main()