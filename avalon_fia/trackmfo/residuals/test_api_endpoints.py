#!/usr/bin/env python3
"""
Script para testar diferentes endpoints da API BTG
"""

import json
import requests
import base64
import uuid
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_token():
    """Obtém token da API"""
    json_file = Path.home() / 'Desktop' / 'api_btg_access.json'
    
    with open(json_file) as f:
        data = json.load(f)
    
    client_id = data['client_id']
    client_secret = data['client_secret']
    
    credentials = f"{client_id}:{client_secret}"
    base64_string = base64.b64encode(credentials.encode()).decode()
    
    url = 'https://api.btgpactual.com/iaas-auth/api/v1/authorization/oauth2/accesstoken'
    headers = {
        'x-id-partner-request': str(uuid.uuid4()),
        'Authorization': f'Basic {base64_string}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    response = requests.post(url, data={'grant_type': 'client_credentials'}, headers=headers)
    
    if response.status_code == 200:
        return response.headers.get('access_token')
    else:
        logger.error(f"Erro ao obter token: {response.text}")
        return None


def test_endpoints(token):
    """Testa diferentes endpoints"""
    
    headers = {
        'x-id-partner-request': str(uuid.uuid4()),
        'access_token': token
    }
    
    print("\n" + "="*60)
    print("TESTANDO ENDPOINTS DA API BTG")
    print("="*60)
    
    # 1. Endpoint de parceiro (que deu erro)
    print("\n1. Endpoint /position/partner:")
    url = 'https://api.btgpactual.com/iaas-api-position/api/v1/position/partner'
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}...")
    
    # 2. Tentar listar contas
    print("\n2. Endpoint /account:")
    url = 'https://api.btgpactual.com/iaas-account-management/api/v1/account-management/account'
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}...")
    
    # 3. Tentar informações do parceiro
    print("\n3. Endpoint /partner/information:")
    url = 'https://api.btgpactual.com/iaas-account-management/api/v1/account-management/partner/information'
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}...")
    
    # 4. Tentar listar posições individuais
    print("\n4. Endpoint /position (sem partner):")
    url = 'https://api.btgpactual.com/iaas-api-position/api/v1/position'
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}...")
    
    # 5. Tentar webhook de posições
    print("\n5. Endpoint /position/webhook:")
    url = 'https://api.btgpactual.com/iaas-api-position/api/v1/position/webhook'
    body = {
        "webhookUrl": "http://example.com/webhook"
    }
    response = requests.post(url, headers=headers, json=body)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}...")
    
    # Se encontrarmos contas, tentar pegar posição individual
    if response.status_code == 200:
        try:
            data = response.json()
            if 'response' in data and isinstance(data['response'], list):
                accounts = data['response']
                if accounts:
                    print(f"\nEncontradas {len(accounts)} contas!")
                    
                    # Pegar posição da primeira conta
                    first_account = accounts[0]
                    account_id = first_account.get('accountNumber', first_account.get('account'))
                    
                    print(f"\n6. Testando posição da conta {account_id}:")
                    url = f'https://api.btgpactual.com/iaas-api-position/api/v1/position/{account_id}'
                    response = requests.get(url, headers=headers)
                    print(f"Status: {response.status_code}")
                    print(f"Response: {response.text[:200]}...")
        except:
            pass


def main():
    print("Testando API BTG Digital...")
    
    token = get_token()
    if not token:
        print("❌ Falha ao obter token")
        return
    
    print(f"✅ Token obtido: {token[:50]}...")
    
    test_endpoints(token)
    
    print("\n" + "="*60)
    print("Se algum endpoint retornou dados, podemos ajustar o script")
    print("para usar o endpoint correto.")
    print("="*60)


if __name__ == '__main__':
    main()