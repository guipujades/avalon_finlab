#!/usr/bin/env python3
"""
Script para descobrir contas e fundos disponíveis na API BTG
"""

import sys
import os
from pathlib import Path
import json

sys.path.append(os.path.join(os.path.dirname(__file__), 'trackfia'))

from btg_api_client import create_btg_client
import requests


def discover_available_resources():
    """Descobre recursos disponíveis na API"""
    print("🔍 DESCOBRINDO RECURSOS DISPONÍVEIS NA API BTG")
    print("="*60)
    
    try:
        client = create_btg_client()
        token = client.get_access_token()
        
        # Headers para requisições
        headers = {
            'access_token': token,
            'Content-Type': 'application/json'
        }
        
        # 1. Tentar endpoint de parceiro sem CNPJ
        print("\n1️⃣ Testando endpoint de parceiro...")
        try:
            response = requests.get(
                f"{client.base_url}/iaas-api-position/api/v1/position/partner",
                headers=headers,
                timeout=30
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print("✅ Resposta obtida:")
                print(json.dumps(data, indent=2)[:500])
                
                # Se houver URL de download, baixar e analisar
                if 'downloadUrl' in data:
                    print(f"\n📥 URL de download encontrada: {data['downloadUrl']}")
            else:
                print(f"Resposta: {response.text[:200]}")
        except Exception as e:
            print(f"❌ Erro: {e}")
        
        # 2. Tentar listar contas diretamente
        print("\n2️⃣ Tentando listar contas...")
        endpoints_to_try = [
            "/iaas-account-management/api/v1/account-management/accounts",
            "/iaas-account-management/api/v1/account-management/account",
            "/iaas-api-position/api/v1/position/accounts",
            "/api/v1/accounts"
        ]
        
        for endpoint in endpoints_to_try:
            try:
                print(f"\nTestando: {endpoint}")
                response = requests.get(
                    f"{client.base_url}{endpoint}",
                    headers=headers,
                    timeout=10
                )
                if response.status_code == 200:
                    print("✅ Endpoint encontrado!")
                    data = response.json()
                    print(json.dumps(data, indent=2)[:300])
                    break
                elif response.status_code != 404:
                    print(f"Status: {response.status_code}")
            except Exception as e:
                if "404" not in str(e):
                    print(f"Erro: {type(e).__name__}")
        
        # 3. Tentar endpoint de fundos
        print("\n3️⃣ Testando endpoints de fundos...")
        fund_endpoints = [
            "/iaas-api-fund/api/v1/fund",
            "/api/v1/funds",
            "/api/v1/investment-funds"
        ]
        
        for endpoint in fund_endpoints:
            try:
                print(f"\nTestando: {endpoint}")
                response = requests.get(
                    f"{client.base_url}{endpoint}",
                    headers=headers,
                    timeout=10
                )
                if response.status_code == 200:
                    print("✅ Endpoint de fundos encontrado!")
                    data = response.json()
                    print(json.dumps(data, indent=2)[:300])
                    break
                elif response.status_code != 404:
                    print(f"Status: {response.status_code}")
            except Exception as e:
                if "404" not in str(e):
                    print(f"Erro: {type(e).__name__}")
        
        # 4. Verificar permissões
        print("\n4️⃣ Verificando permissões do token...")
        try:
            # Decodificar JWT (sem validar assinatura)
            import base64
            token_parts = token.split('.')
            if len(token_parts) >= 2:
                # Adicionar padding se necessário
                payload = token_parts[1]
                payload += '=' * (4 - len(payload) % 4)
                
                decoded = base64.b64decode(payload)
                token_data = json.loads(decoded)
                
                print("\n📋 Informações do token:")
                for key in ['scope', 'permissions', 'roles', 'cnpj', 'partner', 'sub']:
                    if key in token_data:
                        print(f"   {key}: {token_data[key]}")
        except Exception as e:
            print(f"Não foi possível decodificar token: {e}")
        
        # 5. Sugestões baseadas nos resultados
        print("\n💡 SUGESTÕES:")
        print("1. Se você tem números de conta específicos, use:")
        print("   client.get_account_position('NUMERO_DA_CONTA')")
        print("\n2. Para fundos Avalon FIA, pode ser necessário:")
        print("   - API específica de fundos (funds.btgpactual.com)")
        print("   - Credenciais diferentes")
        print("   - Permissões adicionais")
        
    except Exception as e:
        print(f"\n❌ Erro geral: {e}")


if __name__ == "__main__":
    discover_available_resources()