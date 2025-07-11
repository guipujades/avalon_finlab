#!/usr/bin/env python3
"""
Debug BTG API - Investigação detalhada do erro 500
"""

import os
import json
import base64
import uuid
import requests
from pathlib import Path
from urllib.parse import urlparse

def debug_credentials():
    """Debug das credenciais"""
    print("DEBUG: Verificando Credenciais")
    print("="*50)
    
    credentials_file = Path.home() / 'Desktop' / 'api_btg_access.json'
    
    if not credentials_file.exists():
        print("Arquivo nao encontrado")
        return None, None
    
    try:
        with open(credentials_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        client_id = data.get('client_id')
        client_secret = data.get('client_secret')
        
        print(f"Arquivo carregado: {credentials_file}")
        print(f"Estrutura do JSON: {list(data.keys())}")
        print(f"Client ID: {client_id[:10]}...{client_id[-5:] if client_id else 'None'}")
        print(f"Client Secret: {'***' if client_secret else 'None'} ({len(client_secret) if client_secret else 0} chars)")
        
        if not client_id or not client_secret:
            print("Credenciais incompletas!")
            return None, None
        
        return client_id, client_secret
        
    except Exception as e:
        print(f"Erro ao ler credenciais: {e}")
        return None, None

def debug_auth_request(client_id: str, client_secret: str):
    """Debug da requisição de autenticação"""
    print("\nDEBUG: Requisicao de Autenticacao")
    print("="*50)
    
    # Monta as credenciais
    credentials = f"{client_id}:{client_secret}"
    credentials_b64 = base64.b64encode(credentials.encode()).decode()
    
    print(f"Credenciais combinadas: {client_id}:***")
    print(f"Base64: {credentials_b64[:30]}...")
    
    # URL e headers
    url = "https://api.btgpactual.com/iaas-auth/api/v1/authorization/oauth2/accesstoken"
    headers = {
        'x-id-partner-request': str(uuid.uuid4()),
        'Authorization': f'Basic {credentials_b64}',
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'BTG-API-Client/1.0'
    }
    params = {'grant_type': 'client_credentials'}
    
    print(f"URL: {url}")
    print(f"Headers:")
    for key, value in headers.items():
        if 'Authorization' in key:
            print(f"   {key}: Basic ***")
        else:
            print(f"   {key}: {value}")
    print(f"Params: {params}")
    
    return url, headers, params

def test_btg_connection():
    """Teste detalhado da conexão BTG"""
    print("DEBUG COMPLETO - API BTG")
    print("="*60)
    
    # 1. Verifica credenciais
    client_id, client_secret = debug_credentials()
    if not client_id or not client_secret:
        return False
    
    # 2. Prepara requisição
    url, headers, params = debug_auth_request(client_id, client_secret)
    
    # 3. Testa conectividade básica
    print("\nDEBUG: Conectividade")
    print("="*50)
    
    try:
        # Parse da URL
        parsed = urlparse(url)
        print(f"Host: {parsed.netloc}")
        print(f"Path: {parsed.path}")
        
        # Teste de DNS/ping básico
        import socket
        print(f"Resolvendo DNS...")
        ip = socket.gethostbyname(parsed.netloc)
        print(f"IP resolvido: {ip}")
        
    except Exception as e:
        print(f"Erro de conectividade: {e}")
        return False
    
    # 4. Faz a requisição real
    print("\nDEBUG: Requisicao HTTP")
    print("="*50)
    
    try:
        print("Enviando requisicao...")
        
        response = requests.post(
            url, 
            params=params, 
            headers=headers,
            timeout=30,
            verify=True  # Verifica SSL
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Request URL: {response.request.url}")
        print(f"Response Headers:")
        for key, value in response.headers.items():
            print(f"   {key}: {value}")
        
        print(f"\nResponse Body:")
        try:
            if response.headers.get('content-type', '').startswith('application/json'):
                body = response.json()
                print(json.dumps(body, indent=2, ensure_ascii=False))
            else:
                print(response.text[:500] + "..." if len(response.text) > 500 else response.text)
        except:
            print(response.text[:500] + "..." if len(response.text) > 500 else response.text)
        
        # Analisa o erro
        if response.status_code == 500:
            print(f"\nERRO 500 - INTERNAL SERVER ERROR")
            print(f"   Possiveis causas:")
            print(f"   - Servidor BTG indisponivel")
            print(f"   - Credenciais invalidas")
            print(f"   - Formato da requisicao incorreto")
            print(f"   - Endpoint desatualizado")
            
        elif response.status_code == 401:
            print(f"\nERRO 401 - UNAUTHORIZED")
            print(f"   - Credenciais invalidas")
            
        elif response.status_code == 400:
            print(f"\nERRO 400 - BAD REQUEST")
            print(f"   - Parametros incorretos")
            
        elif response.status_code == 200:
            print(f"\nSUCESSO!")
            # Tenta extrair token do header
            token = response.headers.get('access_token')
            if token:
                print(f"TOKEN CAPTURADO: {token[:50]}...")
                return True
            else:
                print(f"Resposta 200 mas token nao encontrado no header")
        
        return False
        
    except requests.exceptions.ConnectionError as e:
        print(f"Erro de conexao: {e}")
        return False
    except requests.exceptions.Timeout as e:
        print(f"Timeout: {e}")
        return False
    except requests.exceptions.SSLError as e:
        print(f"Erro SSL: {e}")
        return False
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return False

def main():
    """Executa debug completo"""
    print("INICIANDO DEBUG DA API BTG")
    print("="*60)
    
    success = test_btg_connection()
    
    print("\n" + "="*60)
    if success:
        print("DEBUG CONCLUIDO - API FUNCIONANDO")
    else:
        print("DEBUG CONCLUIDO - PROBLEMAS IDENTIFICADOS")
        print("\nPROXIMOS PASSOS:")
        print("   1. Verificar se as credenciais estao corretas")
        print("   2. Confirmar se a API BTG esta online")
        print("   3. Verificar se o endpoint esta atualizado")
        print("   4. Contatar suporte BTG se necessario")

if __name__ == "__main__":
    main() 