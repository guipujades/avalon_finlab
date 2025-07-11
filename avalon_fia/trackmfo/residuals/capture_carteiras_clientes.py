#!/usr/bin/env python3
"""
Script para capturar carteiras de múltiplos clientes BTG
Usa a API Digital BTG (não a API de fundos)
"""

import os
import sys
import json
import base64
import uuid
import requests
import zipfile
import tempfile
import pickle
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging
from urllib.parse import urlparse

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adicionar api_btg_mfo_utils ao path
sys.path.append(str(Path(__file__).parent))
from api_btg_mfo_utils import process_account_data, get_total_amount


class CarteirasClientesCapture:
    """Captura carteiras de clientes usando API Digital BTG"""
    
    def __init__(self):
        """Inicializa o capturador"""
        # Arquivo de credenciais
        self.json_file_access = Path.home() / 'Desktop' / 'api_btg_access.json'
        
        # Diretórios
        self.pickle_dir = Path.home() / 'Documents' / 'GitHub' / 'database' / 'dados_api'
        self.pickle_dir.mkdir(parents=True, exist_ok=True)
        
        # Arquivo com dados dos clientes (taxas, etc)
        self.cl_data_path = Path.home() / 'Documents' / 'GitHub' / 'database' / 'data_cl.xlsx'
        
    def get_token_btg(self):
        """Obtém token da API Digital BTG"""
        logger.info("Obtendo token BTG Digital...")
        
        # Verificar se arquivo existe
        if not self.json_file_access.exists():
            logger.error(f"Arquivo de credenciais não encontrado: {self.json_file_access}")
            logger.info("Crie o arquivo com: {'client_id': 'seu_id', 'client_secret': 'seu_secret'}")
            return None
        
        # Carregar credenciais
        with open(self.json_file_access) as f:
            data = json.load(f)
        
        client_id = data['client_id']
        client_secret = data['client_secret']
        
        # Preparar autenticação
        credentials = f"{client_id}:{client_secret}"
        cred_bytes = credentials.encode("ascii")
        base64_bytes = base64.b64encode(cred_bytes)
        base64_string = base64_bytes.decode("ascii")
        
        uuid_request = str(uuid.uuid4())
        
        # Fazer requisição
        url = 'https://api.btgpactual.com/iaas-auth/api/v1/authorization/oauth2/accesstoken'
        headers = {
            'x-id-partner-request': uuid_request,
            'Authorization': f'Basic {base64_string}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {'grant_type': 'client_credentials'}
        
        try:
            response = requests.post(url=url, data=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                # Token vem no header
                token = response.headers.get('access_token')
                if token:
                    logger.info("✅ Token obtido com sucesso!")
                    return token
                else:
                    logger.error("Token não encontrado na resposta")
                    return None
            else:
                logger.error(f"Erro ao obter token: {response.status_code}")
                logger.error(f"Resposta: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Erro na requisição: {e}")
            return None
    
    def capturar_carteiras(self, use_cache=True):
        """
        Captura dados de todas as carteiras dos clientes
        
        Args:
            use_cache: Se True, usa dados do dia se existirem
            
        Returns:
            Dict com dados dos clientes
        """
        current_date = datetime.now().strftime('%Y%m%d')
        cache_file = self.pickle_dir / f'api_mfo_{current_date}.pkl'
        
        # Verificar cache
        if use_cache and cache_file.exists():
            logger.info(f"Usando cache: {cache_file}")
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        
        # Obter token
        token = self.get_token_btg()
        if not token:
            logger.error("Falha ao obter token")
            return {}
        
        # Requisitar dados das carteiras
        logger.info("Requisitando dados das carteiras...")
        
        uuid_request = str(uuid.uuid4())
        url = 'https://api.btgpactual.com/iaas-api-position/api/v1/position/partner'
        
        headers = {
            'x-id-partner-request': uuid_request,
            'access_token': token
        }
        
        try:
            response = requests.get(url=url, headers=headers, timeout=60)
            data = response.json()
            
            if data.get('errors') is None:
                url_archive = data.get('response', {}).get('url')
                if url_archive:
                    logger.info(f"URL do arquivo: {url_archive}")
                    
                    # Baixar e processar arquivo
                    clients = self._download_and_process_zip(url_archive)
                    
                    # Salvar cache
                    with open(cache_file, 'wb') as f:
                        pickle.dump(clients, f)
                    
                    logger.info(f"✅ {len(clients)} carteiras capturadas e salvas em cache")
                    return clients
                else:
                    logger.error("URL do arquivo não encontrada na resposta")
            else:
                logger.error(f"Erro na API: {data.get('errors')}")
                
        except Exception as e:
            logger.error(f"Erro ao capturar carteiras: {e}")
            
        return {}
    
    def _download_and_process_zip(self, url_archive):
        """Baixa e processa arquivo ZIP com dados das carteiras"""
        clients = {}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Baixar arquivo
                logger.info("Baixando arquivo ZIP...")
                
                # Extrair nome do arquivo
                parsed = urlparse(url_archive)
                filename = os.path.basename(parsed.path)
                if not filename.endswith('.zip'):
                    filename = f"carteiras_{datetime.now().strftime('%Y%m%d')}.zip"
                
                zip_path = os.path.join(temp_dir, filename)
                
                # Download
                response = requests.get(url_archive, stream=True, timeout=300)
                response.raise_for_status()
                
                with open(zip_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                logger.info("Extraindo arquivo...")
                
                # Extrair ZIP
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Procurar JSONs das contas
                # Estrutura esperada: iaas-position-holder/[numero]/position/
                for root, dirs, files in os.walk(temp_dir):
                    if 'position' in root:
                        for file in files:
                            if file.endswith('.json'):
                                # ID da conta é o nome do arquivo sem .json
                                account_id = file.replace('.json', '')
                                file_path = os.path.join(root, file)
                                
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    clients[account_id] = f.read()
                
                logger.info(f"Processados {len(clients)} arquivos JSON")
                
            except Exception as e:
                logger.error(f"Erro ao processar ZIP: {e}")
        
        return clients
    
    def processar_e_salvar(self, clients_data):
        """
        Processa dados e salva relatórios
        
        Args:
            clients_data: Dict com dados das carteiras
        """
        if not clients_data:
            logger.warning("Nenhum dado para processar")
            return
        
        # Carregar data_cl se existir
        data_btg = pd.DataFrame()
        if self.cl_data_path.exists():
            try:
                data_btg = pd.read_excel(self.cl_data_path)
                logger.info(f"Carregado data_cl com {len(data_btg)} registros")
            except Exception as e:
                logger.warning(f"Não foi possível carregar data_cl: {e}")
        
        # Processar cada cliente
        resultados = []
        total_patrimonio = 0
        total_cobranca = 0
        
        for client_id, data_json in clients_data.items():
            try:
                # Processar dados da conta
                (funds_df, fixed_income_df, coe_df, equities_df, derivatives_df,
                 commodities_df, crypto_df, cash_df, pension_df, credits_df, 
                 pending_settlements_df, total_positions, total_equity) = process_account_data(data_json)
                
                # Obter valor total
                total_amount = get_total_amount(data_json)
                
                # Obter taxa se disponível
                taxa = 0.01  # Taxa padrão 1%
                if not data_btg.empty and int(client_id) in data_btg['Conta'].values:
                    taxa = data_btg[data_btg['Conta'] == int(client_id)]['Taxas'].iloc[0]
                
                # Calcular cobrança mensal
                cobranca_mensal = (total_amount * taxa) / 12
                
                resultados.append({
                    'Cliente ID': client_id,
                    'Patrimônio Total': total_amount,
                    'Taxa Anual (%)': taxa * 100,
                    'Cobrança Mensal': cobranca_mensal,
                    'Fundos': len(funds_df),
                    'Renda Fixa': len(fixed_income_df),
                    'Ações': len(equities_df),
                    'Cash': cash_df['Value'].sum() if not cash_df.empty else 0
                })
                
                total_patrimonio += total_amount
                total_cobranca += cobranca_mensal
                
            except Exception as e:
                logger.error(f"Erro ao processar cliente {client_id}: {e}")
        
        # Criar DataFrame com resultados
        df_resultados = pd.DataFrame(resultados)
        
        # Salvar relatório
        output_dir = Path.home() / 'Desktop' / 'Carteiras_Clientes'
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / f'carteiras_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Resumo
            df_resultados.to_excel(writer, sheet_name='Resumo', index=False)
            
            # Totais
            totais_df = pd.DataFrame([{
                'Total Clientes': len(resultados),
                'Patrimônio Total': total_patrimonio,
                'Cobrança Mensal Total': total_cobranca,
                'Taxa Média (%)': (total_cobranca * 12 / total_patrimonio * 100) if total_patrimonio > 0 else 0
            }])
            totais_df.to_excel(writer, sheet_name='Totais', index=False)
        
        logger.info(f"✅ Relatório salvo em: {output_file}")
        
        # Exibir resumo
        print("\n" + "=" * 60)
        print("RESUMO DAS CARTEIRAS")
        print("=" * 60)
        print(f"Total de clientes: {len(resultados)}")
        print(f"Patrimônio total: R$ {total_patrimonio:,.2f}")
        print(f"Cobrança mensal total: R$ {total_cobranca:,.2f}")
        if total_patrimonio > 0:
            print(f"Taxa média: {(total_cobranca * 12 / total_patrimonio * 100):.2f}% ao ano")
        print("=" * 60)


def main():
    """Função principal"""
    print("\nCaptura de Carteiras de Clientes BTG")
    print("=" * 40)
    
    capture = CarteirasClientesCapture()
    
    # Capturar dados
    print("\nCapturando carteiras...")
    carteiras = capture.capturar_carteiras(use_cache=False)
    
    if carteiras:
        # Processar e salvar
        capture.processar_e_salvar(carteiras)
    else:
        print("\n❌ Falha na captura das carteiras")
        print("\nVerifique:")
        print("1. Se o arquivo ~/Desktop/api_btg_access.json existe")
        print("2. Se as credenciais estão corretas")
        print("3. Se você tem acesso à API de parceiros")


if __name__ == '__main__':
    main()