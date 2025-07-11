#!/usr/bin/env python3
"""
Teste Real do Token BTG API - Versão 2
Usando cliente refatorado com retry e diagnósticos
"""

import time
import json
from pathlib import Path
from btg_api_client import BTGAPIClient


def test_real_token_with_client():
    """Teste usando o cliente refatorado"""
    print("🔧 TESTE REAL V2: Token BTG via Cliente Refatorado")
    print("="*60)
    
    # Caminho das credenciais reais
    json_file_apiaccess = str(Path(Path.home(), 'Desktop', 'api_btg_access.json'))
    
    try:
        print(f"📂 Carregando credenciais de: {json_file_apiaccess}")
        
        # Verifica se arquivo existe
        if not Path(json_file_apiaccess).exists():
            print(f"❌ Arquivo não encontrado: {json_file_apiaccess}")
            return False
        
        # Cria cliente com credenciais reais
        print("🔄 Inicializando cliente BTG...")
        client = BTGAPIClient(credentials_path=json_file_apiaccess)
        print("✅ Cliente BTG inicializado")
        
        # Tenta obter token com retry
        max_attempts = 3
        
        for attempt in range(1, max_attempts + 1):
            print(f"\n🔄 Tentativa {attempt}/{max_attempts} - Obtendo token...")
            
            try:
                # Tenta obter o token
                token = client.get_access_token()
                
                if token:
                    print(f"\n🎉 TOKEN OBTIDO COM SUCESSO!")
                    print(f"✅ Token: {token}")
                    print(f"✅ Tamanho: {len(token)} caracteres")
                    print(f"✅ Tipo: {type(token)}")
                    
                    # Mostra primeiros e últimos caracteres
                    if len(token) > 20:
                        print(f"✅ Início: {token[:20]}...")
                        print(f"✅ Fim: ...{token[-20:]}")
                    
                    # Salva token para debug
                    token_file = Path.home() / 'Desktop' / 'btg_token_real.txt'
                    with open(token_file, 'w') as f:
                        f.write(f"Token real obtido em: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"Token: {token}\n")
                    print(f"✅ Token salvo em: {token_file}")
                    
                    # Testa se token é válido (fazendo uma requisição simples)
                    print(f"\n🧪 Testando validade do token...")
                    test_result = client.test_connection()
                    
                    if test_result:
                        print("✅ Token válido - conexão teste bem-sucedida")
                    else:
                        print("⚠️ Token obtido mas teste de conexão falhou")
                    
                    return True
                    
                else:
                    print("❌ Token não obtido (retornou None/vazio)")
                    
            except Exception as e:
                print(f"❌ Erro na tentativa {attempt}: {e}")
                
                # Se não é a última tentativa, espera antes de tentar novamente
                if attempt < max_attempts:
                    wait_time = attempt * 2  # 2s, 4s, 6s...
                    print(f"⏳ Aguardando {wait_time}s antes da próxima tentativa...")
                    time.sleep(wait_time)
        
        print(f"\n❌ Falha após {max_attempts} tentativas")
        return False
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        return False


def test_credentials_file():
    """Testa se o arquivo de credenciais está correto"""
    print("\n🔍 VERIFICAÇÃO DO ARQUIVO DE CREDENCIAIS")
    print("="*50)
    
    json_file_apiaccess = str(Path(Path.home(), 'Desktop', 'api_btg_access.json'))
    
    try:
        with open(json_file_apiaccess, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("✅ Arquivo JSON válido")
        
        # Verifica estrutura
        required_keys = ['client_id', 'client_secret']
        missing_keys = [key for key in required_keys if key not in data]
        
        if missing_keys:
            print(f"❌ Chaves ausentes: {missing_keys}")
            return False
        
        client_id = data['client_id']
        client_secret = data['client_secret']
        
        print(f"✅ client_id: {client_id[:15]}... ({len(client_id)} chars)")
        print(f"✅ client_secret: {client_secret[:15]}... ({len(client_secret)} chars)")
        
        # Verifica se são strings não vazias
        if not client_id or not client_secret:
            print("❌ client_id ou client_secret estão vazios")
            return False
        
        # Verifica tamanhos razoáveis
        if len(client_id) < 10 or len(client_secret) < 10:
            print("⚠️ Credenciais parecem muito curtas")
        
        print("✅ Estrutura do arquivo de credenciais OK")
        return True
        
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {json_file_apiaccess}")
        return False
    except json.JSONDecodeError:
        print("❌ Arquivo JSON inválido")
        return False
    except Exception as e:
        print(f"❌ Erro ao verificar credenciais: {e}")
        return False


def main():
    """Executa todos os testes"""
    print("🚀 TESTE REAL DO TOKEN BTG - VERSÃO 2")
    print("="*60)
    print("Objetivo: Capturar token real usando cliente refatorado")
    print("="*60)
    
    # Primeiro verifica credenciais
    creds_ok = test_credentials_file()
    
    if not creds_ok:
        print("\n❌ Problema com arquivo de credenciais - abortando")
        return
    
    # Tenta obter token
    success = test_real_token_with_client()
    
    print("\n" + "="*60)
    if success:
        print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("✅ Token real capturado da API BTG")
        print("✅ Cliente refatorado funcionando")
    else:
        print("❌ TESTE FALHOU")
        print("❌ Não foi possível obter o token")
        print("💡 Possíveis causas:")
        print("   • Problema temporário na API BTG")
        print("   • Credenciais inválidas ou expiradas")
        print("   • Mudança no endpoint ou formato da API")
    print("="*60)


if __name__ == "__main__":
    main() 