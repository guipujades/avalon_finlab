#!/usr/bin/env python3
"""
Teste Real do Token BTG API
Captura token real usando credenciais do arquivo
"""

import json
import base64
import uuid
import requests
from pathlib import Path
from datetime import datetime


def test_real_btg_token():
    """Teste real para capturar token BTG"""
    print("🔧 TESTE REAL: Captura de Token BTG API")
    print("="*50)
    
    # Caminho das credenciais reais
    json_file_apiaccess = str(Path(Path.home(), 'Desktop', 'api_btg_access.json'))
    
    print(f"📂 Arquivo de credenciais: {json_file_apiaccess}")
    
    try:
        # 1. Verifica se arquivo existe
        credentials_path = Path(json_file_apiaccess)
        if not credentials_path.exists():
            print(f"❌ Arquivo não encontrado: {json_file_apiaccess}")
            return False
        
        print("✅ Arquivo de credenciais encontrado")
        
        # 2. Carrega credenciais
        with open(credentials_path, 'r', encoding='utf-8') as f:
            credentials_data = json.load(f)
        
        client_id = credentials_data.get('client_id')
        client_secret = credentials_data.get('client_secret')
        
        if not client_id or not client_secret:
            print("❌ client_id ou client_secret não encontrados no arquivo")
            return False
        
        print(f"✅ Credenciais carregadas:")
        print(f"   Client ID: {client_id[:10]}...{client_id[-10:]}")
        print(f"   Client Secret: {client_secret[:10]}...{client_secret[-10:]}")
        
        # 3. Prepara requisição OAuth2
        base_url = "https://api.btgpactual.com"
        endpoint = "/iaas-auth/api/v1/authorization/oauth2/accesstoken"
        url = f"{base_url}{endpoint}"
        
        # Codifica credenciais em Base64
        credentials_string = f"{client_id}:{client_secret}"
        credentials_b64 = base64.b64encode(credentials_string.encode()).decode()
        
        # Headers da requisição
        headers = {
            'x-id-partner-request': str(uuid.uuid4()),
            'Authorization': f'Basic {credentials_b64}',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'BTG-API-Client/1.0'
        }
        
        # Parâmetros
        params = {'grant_type': 'client_credentials'}
        
        print(f"\n🔄 Fazendo requisição para obter token...")
        print(f"   URL: {url}")
        print(f"   Request ID: {headers['x-id-partner-request']}")
        
        # 4. Faz a requisição
        start_time = datetime.now()
        
        response = requests.post(
            url, 
            params=params, 
            headers=headers, 
            timeout=30,
            verify=True  # Verifica SSL
        )
        
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        print(f"⏱️ Tempo de resposta: {response_time:.2f} segundos")
        print(f"📊 Status Code: {response.status_code}")
        
        # 5. Analisa a resposta
        print(f"\n📋 HEADERS DE RESPOSTA:")
        for key, value in response.headers.items():
            if 'token' in key.lower() or 'auth' in key.lower():
                print(f"   {key}: {value}")
        
        print(f"\n📋 CONTEÚDO DA RESPOSTA:")
        if response.text:
            print(f"   Body: {response.text}")
        else:
            print("   Body: [vazio]")
        
        # 6. Verifica se obteve o token
        if response.status_code == 200:
            # Token pode estar no header
            token = response.headers.get('access_token')
            
            if token:
                print(f"\n🎉 TOKEN OBTIDO COM SUCESSO!")
                print(f"✅ Token: {token}")
                print(f"✅ Tamanho: {len(token)} caracteres")
                print(f"✅ Primeiros 50 chars: {token[:50]}...")
                
                # Salva token para debug
                token_file = Path.home() / 'Desktop' / 'btg_token_debug.txt'
                with open(token_file, 'w') as f:
                    f.write(f"Token obtido em: {datetime.now()}\n")
                    f.write(f"Token: {token}\n")
                print(f"✅ Token salvo em: {token_file}")
                
                return True
            else:
                print("❌ Token não encontrado no header da resposta")
                
        elif response.status_code == 401:
            print("❌ Erro 401: Credenciais inválidas")
        elif response.status_code == 403:
            print("❌ Erro 403: Acesso negado")
        elif response.status_code == 429:
            print("❌ Erro 429: Muitas requisições (rate limit)")
        else:
            print(f"❌ Erro {response.status_code}: {response.text}")
        
        # Força erro para debug
        response.raise_for_status()
        
        return False
        
    except FileNotFoundError:
        print(f"❌ Arquivo de credenciais não encontrado: {json_file_apiaccess}")
        return False
    except json.JSONDecodeError:
        print("❌ Erro ao decodificar JSON do arquivo de credenciais")
        return False
    except requests.Timeout:
        print("❌ Timeout na requisição (>30s)")
        return False
    except requests.ConnectionError:
        print("❌ Erro de conexão - verifique sua internet")
        return False
    except requests.HTTPError as e:
        print(f"❌ Erro HTTP: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False


def main():
    """Executa o teste"""
    print("🚀 TESTE REAL DA API BTG")
    print("="*40)
    print("Objetivo: Capturar token real usando credenciais reais")
    print("="*40)
    
    success = test_real_btg_token()
    
    print("\n" + "="*40)
    if success:
        print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("✅ Token real capturado da API BTG")
    else:
        print("❌ TESTE FALHOU")
        print("❌ Não foi possível obter o token")
    print("="*40)


if __name__ == "__main__":
    main() 