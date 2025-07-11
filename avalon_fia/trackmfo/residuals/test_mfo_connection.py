#!/usr/bin/env python3
"""
Script para testar conexão com API BTG de parceiros
"""

import json
import requests
import sys
from pathlib import Path

# Adicionar trackfia ao path
sys.path.append(str(Path(__file__).parent.parent / 'trackfia'))

def test_partner_api():
    """Testa conexão com API de parceiros"""
    
    print("Testando conexão com API BTG de Parceiros")
    print("=" * 50)
    
    # Tentar diferentes métodos de autenticação
    
    # Método 1: Usar credenciais do Avalon (api_btg_funds)
    print("\n1. Tentando com credenciais do Avalon FIA...")
    
    from api_btg_funds import auth_apiBTG_funds
    
    try:
        config = {}  # Config vazio, usa credenciais hardcoded
        token, _ = auth_apiBTG_funds(config)
        print(f"✅ Token obtido: {token[:50]}...")
        
        # Testar endpoint de parceiro
        print("\n2. Testando endpoint de parceiro...")
        
        headers = {
            'X-SecureConnect-Token': token,
            'Authorization': f'Bearer {token}'
        }
        
        # Tentar obter posições do parceiro
        url = 'https://funds.btgpactual.com/api/v4/position/partner'
        response = requests.get(url, headers=headers)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            print("\n✅ API de parceiro está acessível!")
        else:
            print("\n⚠️ API retornou erro, mas conexão foi estabelecida")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    # Método 2: Tentar com BTGAPIClient
    print("\n\n3. Tentando com BTGAPIClient...")
    
    try:
        from btg_api_client import BTGAPIClient
        
        # Verificar se existe arquivo de credenciais
        cred_file = Path.home() / 'Desktop' / 'api_btg_info.json'
        
        if cred_file.exists():
            print(f"Usando credenciais de: {cred_file}")
            client = BTGAPIClient(credentials_path=str(cred_file))
        else:
            print("Arquivo de credenciais não encontrado")
            print("Execute: python create_credentials.py")
            return
        
        # Obter token
        token = client.get_access_token()
        print(f"✅ Token obtido: {token[:50]}...")
        
        # Testar posições do parceiro
        print("\n4. Obtendo posições do parceiro...")
        positions = client.get_all_accounts_positions()
        print(f"Response: {positions}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    print("\n" + "=" * 50)
    print("Teste concluído!")


if __name__ == '__main__':
    test_partner_api()