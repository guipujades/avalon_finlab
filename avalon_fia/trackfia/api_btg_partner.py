"""
Módulo para lidar com as novas APIs de posições por parceiro do BTG
Implementado após mudanças de 21/01
"""

import json
import requests
import time
import tempfile
import zipfile
import os
import pandas as pd
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime

from api_btg_utils import parse_xml


def position_by_partner_refresh(token, cnpj='47952345000109'):
    """
    Atualiza as posições do parceiro para D0 usando o novo endpoint.
    Este endpoint deve ser chamado antes de tentar obter as posições.
    
    Args:
        token (str): Token de autenticação
        cnpj (str): CNPJ do parceiro
        
    Returns:
        dict: Resposta da API ou None em caso de erro
    """
    
    # URL baseada no padrão mencionado na documentação
    url = 'https://funds.btgpactual.com/api/v4/position/get-position-by-partner-refresh'
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',  # Tentar com Bearer token
        'X-SecureConnect-Token': token  # Manter também o header antigo
    }
    
    payload = {
        'partnerCnpj': cnpj,  # Tentar variações do campo
        'cnpj': cnpj,
        'webhookUrl': 'positions-by-partner'
    }
    
    print(f"Tentando refresh de posições para CNPJ {cnpj}...")
    
    # Tentar com POST
    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"POST Response: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 405:
            # Se POST não funcionar, tentar GET
            response = requests.get(f"{url}?cnpj={cnpj}", headers=headers)
            print(f"GET Response: {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        print(f"Erro na requisição: {e}")
    
    return None


def get_partner_positions(token, cnpj='47952345000109'):
    """
    Obtém as posições do parceiro após o refresh.
    
    Args:
        token (str): Token de autenticação
        cnpj (str): CNPJ do parceiro
        
    Returns:
        requests.Response: Resposta com o arquivo ZIP ou None
    """
    
    # URL baseada no padrão mencionado  
    url = 'https://funds.btgpactual.com/api/v4/position/get-partner-position'
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
        'X-SecureConnect-Token': token
    }
    
    payload = {
        'partnerCnpj': cnpj,
        'cnpj': cnpj
    }
    
    print(f"Obtendo posições para CNPJ {cnpj}...")
    
    # Tentar com POST primeiro
    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"POST Response: {response.status_code}")
        
        if response.status_code == 200:
            return response
        elif response.status_code == 405:
            # Se POST não funcionar, tentar GET
            response = requests.get(f"{url}?cnpj={cnpj}", headers=headers)
            print(f"GET Response: {response.status_code}")
            
            if response.status_code == 200:
                return response
    except Exception as e:
        print(f"Erro na requisição: {e}")
    
    return None


def process_partner_positions_response(response):
    """
    Processa a resposta das posições do parceiro.
    
    Args:
        response: Resposta da API
        
    Returns:
        tuple: (df, data_xml, header) ou (None, None, None) em caso de erro
    """
    
    if not response or response.status_code != 200:
        return None, None, None
    
    content_type = response.headers.get('Content-Type', '')
    
    # Se for JSON, pode ter informações sobre o arquivo
    if 'application/json' in content_type:
        try:
            data = response.json()
            print(f"Resposta JSON: {data}")
            
            # Verificar se há URL para download
            if 'fileUrl' in data or 'downloadUrl' in data:
                file_url = data.get('fileUrl') or data.get('downloadUrl')
                # Fazer download do arquivo
                file_response = requests.get(file_url)
                return process_partner_positions_response(file_response)
                
        except Exception as e:
            print(f"Erro ao processar JSON: {e}")
    
    # Se for ZIP ou binário
    elif 'application/zip' in content_type or 'application/octet-stream' in content_type:
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        temp_zip.write(response.content)
        temp_zip.close()
        
        try:
            with zipfile.ZipFile(temp_zip.name, 'r') as zip_ref:
                # Listar arquivos no ZIP
                files = zip_ref.namelist()
                print(f"Arquivos no ZIP: {files}")
                
                # Extrair para diretório temporário
                extract_dir = tempfile.mkdtemp()
                zip_ref.extractall(extract_dir)
                
                # Procurar por XML
                for file in files:
                    if file.endswith('.xml'):
                        xml_path = os.path.join(extract_dir, file)
                        tree = ET.parse(xml_path)
                        root = tree.getroot()
                        return parse_xml(root)
                        
        except Exception as e:
            print(f"Erro ao processar ZIP: {e}")
        finally:
            os.unlink(temp_zip.name)
    
    return None, None, None


def get_partner_portfolio(token, cnpj='47952345000109'):
    """
    Função principal para obter o portfolio do parceiro usando os novos endpoints.
    
    Args:
        token (str): Token de autenticação
        cnpj (str): CNPJ do parceiro
        
    Returns:
        tuple: (df, data_xml, header) ou (None, None, None) em caso de erro
    """
    
    print("=== Obtendo portfolio via novos endpoints ===")
    
    # 1. Fazer refresh das posições
    refresh_result = position_by_partner_refresh(token, cnpj)
    
    if refresh_result:
        print("Refresh realizado, aguardando processamento...")
        time.sleep(10)  # Aguardar mais tempo para processamento
    else:
        print("Falha no refresh, tentando obter posições mesmo assim...")
    
    # 2. Obter as posições
    positions_response = get_partner_positions(token, cnpj)
    
    if positions_response:
        # 3. Processar resposta
        return process_partner_positions_response(positions_response)
    
    print("Não foi possível obter as posições do parceiro")
    return None, None, None


if __name__ == "__main__":
    # Teste do módulo
    json_path = Path.home() / 'Desktop' / 'api_btg_info.json'
    
    with open(json_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    from api_btg_utils import auth_apiBTG
    token, _ = auth_apiBTG(config)
    
    df, data_xml, header = get_partner_portfolio(token)
    
    if df is not None:
        print(f"Portfolio obtido com sucesso! {len(df)} registros")
    else:
        print("Falha ao obter portfolio")