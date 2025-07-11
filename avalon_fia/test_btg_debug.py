#!/usr/bin/env python3
"""
Debug detalhado da API BTG para entender os problemas
"""

import json
import requests
import sys
import os
from pathlib import Path
from datetime import datetime
import time

sys.path.append(os.path.join(os.path.dirname(__file__), 'trackfia'))

from api_btg_utils import auth_apiBTG


def debug_response(response, show_html=False):
    """Mostra detalhes da resposta para debug"""
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    
    content_type = response.headers.get('Content-Type', '')
    
    if 'text/html' in content_type and show_html:
        # Mostrar primeiros 500 caracteres do HTML
        print(f"HTML Content (primeiros 500 chars):\n{response.text[:500]}")
    elif 'application/json' in content_type:
        try:
            print(f"JSON Response: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Text Response: {response.text[:500]}")
    else:
        print(f"Response Content Type: {content_type}")
        print(f"Response Text (primeiros 200 chars): {response.text[:200]}")


def test_authentication(config):
    """Testa e debug a autenticação"""
    print("=== TESTE DE AUTENTICAÇÃO ===\n")
    
    # Verificar configurações
    print("Configurações carregadas:")
    print(f"CLIENT_ID: {config.get('CLIENT_ID', 'NÃO DEFINIDO')}")
    print(f"CLIENT_SECRET: {'*' * len(config.get('CLIENT_SECRET', ''))}")
    print(f"GRANT_TYPE: {config.get('GRANT_TYPE', 'NÃO DEFINIDO')}")
    
    # Tentar autenticar
    auth_url = 'https://funds.btgpactual.com/connect/token'
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'grant_type': config.get('GRANT_TYPE'),
        'client_id': config.get('CLIENT_ID'),
        'client_secret': config.get('CLIENT_SECRET'),
    }
    
    print(f"\nFazendo requisição para: {auth_url}")
    
    try:
        response = requests.post(auth_url, headers=headers, data=data)
        print("\nResposta da autenticação:")
        debug_response(response)
        
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get('access_token')
            
            if token:
                print(f"\n✓ Token obtido com sucesso!")
                print(f"Token type: {token_data.get('token_type', 'bearer')}")
                print(f"Expires in: {token_data.get('expires_in', 'unknown')} seconds")
                return token
            else:
                print("\n✗ Resposta 200 mas sem token")
                return None
        else:
            print(f"\n✗ Erro na autenticação: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"\n✗ Exceção durante autenticação: {e}")
        return None


def test_old_endpoint(token):
    """Testa o endpoint antigo que sabemos que funcionava"""
    print("\n\n=== TESTE DO ENDPOINT ANTIGO (Portfolio) ===\n")
    
    url = 'https://funds.btgpactual.com/reports/Portfolio'
    
    # Tentar diferentes formatos de header
    header_formats = [
        {'X-SecureConnect-Token': token},
        {'Authorization': f'Bearer {token}'},
        {'Authorization': f'bearer {token}'},
        {'X-SecureConnect-Token': token, 'Authorization': f'Bearer {token}'}
    ]
    
    payload = {
        'contract': {
            'startDate': datetime.today().strftime('%Y-%m-%d'),
            'endDate': datetime.today().strftime('%Y-%m-%d'),
            'typeReport': 3,
            'fundName': 'AVALON FIA'
        },
        'pageSize': 100,
        'webhookEndpoint': 'string'
    }
    
    for i, headers in enumerate(header_formats):
        headers['Content-Type'] = 'application/json'
        
        print(f"\nTentativa {i+1} - Headers: {list(headers.keys())}")
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code != 401:  # Se não for erro de autenticação
                print("Resposta:")
                debug_response(response)
                
                if response.status_code == 200:
                    print("\n✓ Formato de header correto encontrado!")
                    return True
        except Exception as e:
            print(f"Erro: {e}")
    
    return False


def test_partner_endpoints_detailed(token):
    """Testa os novos endpoints com mais detalhes"""
    print("\n\n=== TESTE DETALHADO DOS ENDPOINTS DE PARCEIRO ===\n")
    
    # Baseando-se no link da documentação fornecido
    base_url = 'https://developer-partner.btgpactual.com/api/v4'
    funds_base = 'https://funds.btgpactual.com'
    
    endpoints_to_test = [
        # Tentativas baseadas na documentação
        f'{base_url}/position/get-position-by-partner-refresh',
        f'{base_url}/position/get-partner-position',
        f'{funds_base}/api/v4/position/refresh-partner',
        f'{funds_base}/api/v4/position/partner',
        # Endpoint mencionado no email
        f'{funds_base}/position/get-position-by-partner-refresh',
        f'{funds_base}/position/get-partner-position',
    ]
    
    headers = {
        'Content-Type': 'application/json',
        'X-SecureConnect-Token': token
    }
    
    for endpoint in endpoints_to_test:
        print(f"\nTestando: {endpoint}")
        
        # POST
        try:
            response = requests.post(endpoint, headers=headers, json={'cnpj': '47952345000109'})
            if response.status_code != 404 and response.status_code != 405:
                print(f"POST - Status: {response.status_code}")
                if 'text/html' not in response.headers.get('Content-Type', ''):
                    debug_response(response)
        except Exception as e:
            print(f"POST - Erro: {type(e).__name__}")
        
        # GET
        try:
            response = requests.get(f"{endpoint}?cnpj=47952345000109", headers=headers)
            if response.status_code != 404 and response.status_code != 405:
                print(f"GET - Status: {response.status_code}")
                if 'text/html' not in response.headers.get('Content-Type', ''):
                    debug_response(response)
        except Exception as e:
            print(f"GET - Erro: {type(e).__name__}")


if __name__ == "__main__":
    # Carregar configurações
    json_path = Path.home() / 'Desktop' / 'api_btg_info.json'
    
    if not json_path.exists():
        print(f"ERRO: Arquivo de configuração não encontrado em {json_path}")
        print("\nVerifique se o arquivo contém:")
        print("- CLIENT_ID")
        print("- CLIENT_SECRET")
        print("- GRANT_TYPE")
        sys.exit(1)
    
    with open(json_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Teste 1: Autenticação
    token = test_authentication(config)
    
    if not token:
        print("\nERRO: Não foi possível obter token de autenticação")
        print("Verifique as credenciais no arquivo api_btg_info.json")
        sys.exit(1)
    
    # Teste 2: Endpoint antigo
    old_endpoint_works = test_old_endpoint(token)
    
    if not old_endpoint_works:
        print("\nAVISO: Endpoint antigo não está funcionando. Token pode estar expirado ou inválido.")
        
        # Tentar reautenticar
        print("\nTentando reautenticar...")
        time.sleep(5)
        token = test_authentication(config)
        
        if token:
            old_endpoint_works = test_old_endpoint(token)
    
    # Teste 3: Novos endpoints
    if token:
        test_partner_endpoints_detailed(token)