#!/usr/bin/env python3
"""
Script para testar API BTG com mais detalhes
"""

import json
import requests
import base64
import uuid
from pathlib import Path
from datetime import datetime, timedelta
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
    return None


def test_detailed(token):
    """Testa com mais detalhes"""
    
    headers = {
        'x-id-partner-request': str(uuid.uuid4()),
        'access_token': token,
        'Content-Type': 'application/json'
    }
    
    print("\n" + "="*60)
    print("TESTES DETALHADOS")
    print("="*60)
    
    # 1. Testar webhook com data
    print("\n1. Webhook com data:")
    url = 'https://api.btgpactual.com/iaas-api-position/api/v1/position/webhook'
    
    # Testar diferentes formatos de data
    dates_to_test = [
        datetime.now().strftime('%Y-%m-%d'),  # Hoje
        (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),  # Ontem
        datetime.now().strftime('%Y%m%d'),  # Formato sem traços
    ]
    
    for date_str in dates_to_test:
        print(f"\nTestando com data: {date_str}")
        body = {
            "webhookUrl": "http://example.com/webhook",
            "date": date_str
        }
        response = requests.post(url, headers=headers, json=body)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:300]}...")
        
        if response.status_code == 200:
            break
    
    # 2. Testar diferentes CNPJs
    print("\n\n2. Testando parceiro com diferentes parâmetros:")
    
    # Tentar sem CNPJ
    print("\na) Sem CNPJ:")
    url = 'https://api.btgpactual.com/iaas-api-position/api/v1/position/partner'
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}...")
    
    # Tentar com CNPJ no header
    print("\nb) Com CNPJ no header:")
    headers_with_cnpj = headers.copy()
    headers_with_cnpj['cnpj'] = '47952345000109'
    response = requests.get(url, headers=headers_with_cnpj)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}...")
    
    # 3. Verificar se há endpoint de listagem
    print("\n\n3. Procurando endpoints de listagem:")
    
    endpoints_to_try = [
        '/iaas-api-position/api/v1/position/list',
        '/iaas-api-position/api/v1/positions',
        '/iaas-account-management/api/v1/accounts',
        '/iaas-account-management/api/v1/account',
        '/iaas-api-position/api/v1/position/all',
        '/iaas-api-position/api/v1/position/accounts',
    ]
    
    base_url = 'https://api.btgpactual.com'
    
    for endpoint in endpoints_to_try:
        print(f"\nTestando {endpoint}:")
        response = requests.get(base_url + endpoint, headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code != 404:
            print(f"Response: {response.text[:200]}...")
    
    # 4. Verificar informações do token
    print("\n\n4. Decodificando token JWT:")
    try:
        import jwt
        # Decodificar sem verificar assinatura para ver o conteúdo
        decoded = jwt.decode(token, options={"verify_signature": False})
        print("Conteúdo do token:")
        for key, value in decoded.items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"Não foi possível decodificar token: {e}")
    
    # 5. Testar endpoint de refresh
    print("\n\n5. Testando endpoint de refresh:")
    url = 'https://api.btgpactual.com/iaas-api-position/api/v1/position/refresh'
    body = {
        "date": datetime.now().strftime('%Y-%m-%d')
    }
    response = requests.post(url, headers=headers, json=body)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}...")


def main():
    print("Teste detalhado da API BTG...")
    
    token = get_token()
    if not token:
        print("❌ Falha ao obter token")
        return
    
    print(f"✅ Token obtido com sucesso")
    
    test_detailed(token)
    
    print("\n" + "="*60)
    print("CONCLUSÃO")
    print("="*60)
    print("Verifique os resultados acima para entender:")
    print("1. Se você tem acesso a contas individuais")
    print("2. Se precisa solicitar posições via webhook")
    print("3. Se há restrições no seu acesso")


if __name__ == '__main__':
    main()