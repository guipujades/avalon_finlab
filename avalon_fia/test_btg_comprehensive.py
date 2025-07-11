#!/usr/bin/env python3
"""
Teste abrangente para encontrar os endpoints corretos da API BTG
"""

import json
import requests
import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), 'trackfia'))

from api_btg_utils import auth_apiBTG


def test_endpoints(token, cnpj='47952345000109'):
    """Testa várias combinações de endpoints e métodos"""
    
    # Lista de possíveis endpoints baseados na documentação
    endpoints = [
        # Endpoints mencionados na documentação
        ('POST', 'https://funds.btgpactual.com/api/v4/position/get-position-by-partner-refresh'),
        ('GET', 'https://funds.btgpactual.com/api/v4/position/get-position-by-partner-refresh'),
        ('POST', 'https://funds.btgpactual.com/api/v4/position/get-partner-position'),
        ('GET', 'https://funds.btgpactual.com/api/v4/position/get-partner-position'),
        
        # Variações possíveis
        ('POST', 'https://funds.btgpactual.com/api/v4/positions/refresh'),
        ('POST', 'https://funds.btgpactual.com/api/v4/positions/partner'),
        ('POST', 'https://funds.btgpactual.com/reports/PositionByPartnerRefresh'),
        ('POST', 'https://funds.btgpactual.com/reports/PartnerPosition'),
        
        # Endpoints de posição padrão
        ('POST', 'https://funds.btgpactual.com/api/v4/position'),
        ('GET', 'https://funds.btgpactual.com/api/v4/position'),
    ]
    
    # Diferentes formatos de headers
    header_variations = [
        {
            'Content-Type': 'application/json',
            'X-SecureConnect-Token': token
        },
        {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        },
        {
            'Content-Type': 'application/json',
            'X-SecureConnect-Token': token,
            'Authorization': f'Bearer {token}'
        }
    ]
    
    # Diferentes formatos de payload
    payload_variations = [
        {'cnpj': cnpj},
        {'partnerCnpj': cnpj},
        {'contract': {'cnpj': cnpj}},
        {'partner': {'cnpj': cnpj}},
        {'cnpj': cnpj, 'webhookEndpoint': 'positions-by-partner'},
        {'contract': {'cnpj': cnpj}, 'webhookEndpoint': 'positions-by-partner'}
    ]
    
    print("=== TESTE ABRANGENTE DE ENDPOINTS BTG ===\n")
    
    success_count = 0
    
    for method, url in endpoints:
        print(f"\nTestando: {method} {url}")
        print("-" * 80)
        
        for i, headers in enumerate(header_variations):
            for j, payload in enumerate(payload_variations):
                try:
                    if method == 'POST':
                        response = requests.post(url, headers=headers, json=payload, timeout=10)
                    else:
                        # Para GET, adicionar CNPJ como query parameter
                        response = requests.get(f"{url}?cnpj={cnpj}", headers=headers, timeout=10)
                    
                    # Só mostrar combinações que não retornam 404 ou 405
                    if response.status_code not in [404, 405]:
                        print(f"  Headers #{i+1}, Payload #{j+1}: Status {response.status_code}")
                        
                        if response.status_code == 200:
                            success_count += 1
                            print(f"    ✓ SUCESSO!")
                            print(f"    Content-Type: {response.headers.get('Content-Type')}")
                            
                            # Se for JSON, mostrar conteúdo
                            if 'application/json' in response.headers.get('Content-Type', ''):
                                try:
                                    data = response.json()
                                    print(f"    Resposta: {json.dumps(data, indent=2)[:200]}...")
                                except:
                                    pass
                        elif response.status_code == 401:
                            print(f"    → Não autorizado (token pode estar expirado)")
                        elif response.status_code == 400:
                            print(f"    → Bad Request")
                            try:
                                print(f"    Erro: {response.json()}")
                            except:
                                pass
                                
                except requests.exceptions.Timeout:
                    print(f"  Headers #{i+1}, Payload #{j+1}: Timeout")
                except Exception as e:
                    if "404" not in str(e) and "405" not in str(e):
                        print(f"  Headers #{i+1}, Payload #{j+1}: Erro: {type(e).__name__}")
    
    print(f"\n\n=== RESUMO ===")
    print(f"Total de requisições bem-sucedidas (200): {success_count}")
    
    # Testar também o endpoint antigo que sabemos que funciona
    print("\n\n=== TESTANDO ENDPOINT ANTIGO (Portfolio) ===")
    
    old_endpoint = 'https://funds.btgpactual.com/reports/Portfolio'
    headers = {
        'Content-Type': 'application/json',
        'X-SecureConnect-Token': token
    }
    
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
    
    try:
        response = requests.post(old_endpoint, headers=headers, json=payload)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✓ Endpoint antigo ainda funciona")
            print(f"Resposta: {response.json()}")
        else:
            print(f"Erro: {response.text[:200]}")
    except Exception as e:
        print(f"Erro: {e}")


if __name__ == "__main__":
    # Carregar configurações
    json_path = Path.home() / 'Desktop' / 'api_btg_info.json'
    
    if not json_path.exists():
        print(f"ERRO: Arquivo de configuração não encontrado em {json_path}")
        sys.exit(1)
    
    with open(json_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Autenticar
    print("Autenticando...")
    try:
        token, _ = auth_apiBTG(config)
        print("Autenticação bem-sucedida!\n")
    except Exception as e:
        print(f"Erro na autenticação: {e}")
        sys.exit(1)
    
    # Executar testes
    test_endpoints(token)