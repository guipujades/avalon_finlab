#!/usr/bin/env python3
"""
Script para configurar as credenciais da API BTG
"""

import json
import os
from pathlib import Path
import getpass


def check_existing_config():
    """Verifica a configuração existente"""
    json_path = Path.home() / 'Desktop' / 'api_btg_info.json'
    
    if json_path.exists():
        print(f"Arquivo de configuração encontrado em: {json_path}")
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            print("\nConfiguração atual:")
            print(f"CLIENT_ID: {config.get('CLIENT_ID', 'NÃO DEFINIDO')}")
            print(f"CLIENT_SECRET: {'*' * len(config.get('CLIENT_SECRET', '')) if config.get('CLIENT_SECRET') else 'NÃO DEFINIDO'}")
            print(f"GRANT_TYPE: {config.get('GRANT_TYPE', 'NÃO DEFINIDO')}")
            
            # Verificar outros campos que podem existir
            other_fields = [k for k in config.keys() if k not in ['CLIENT_ID', 'CLIENT_SECRET', 'GRANT_TYPE']]
            if other_fields:
                print(f"\nOutros campos encontrados: {', '.join(other_fields)}")
            
            return config
            
        except json.JSONDecodeError:
            print("ERRO: O arquivo existe mas não é um JSON válido!")
            return None
        except Exception as e:
            print(f"ERRO ao ler arquivo: {e}")
            return None
    else:
        print(f"Arquivo de configuração NÃO encontrado em: {json_path}")
        return None


def create_config_template():
    """Cria um template de configuração"""
    json_path = Path.home() / 'Desktop' / 'api_btg_info.json'
    
    print("\n=== CRIANDO ARQUIVO DE CONFIGURAÇÃO ===")
    print("\nPara usar a API do BTG, você precisa das seguintes informações:")
    print("1. CLIENT_ID - Identificador do cliente fornecido pelo BTG")
    print("2. CLIENT_SECRET - Senha/segredo do cliente fornecido pelo BTG")
    print("3. GRANT_TYPE - Tipo de autenticação (geralmente 'client_credentials')")
    
    print("\nEssas informações devem ter sido fornecidas pelo BTG quando você")
    print("solicitou acesso à API.")
    
    create = input("\nDeseja criar o arquivo de configuração agora? (s/n): ").lower()
    
    if create == 's':
        config = {}
        
        print("\nInsira as credenciais (ou pressione Enter para deixar em branco):")
        
        config['CLIENT_ID'] = input("CLIENT_ID: ").strip()
        config['CLIENT_SECRET'] = getpass.getpass("CLIENT_SECRET: ").strip()
        
        grant_type = input("GRANT_TYPE (padrão: client_credentials): ").strip()
        config['GRANT_TYPE'] = grant_type if grant_type else 'client_credentials'
        
        # Salvar arquivo
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            print(f"\n✓ Arquivo criado com sucesso em: {json_path}")
            print("\nIMPORTANTE: Mantenha este arquivo seguro, pois contém suas credenciais!")
            
            return config
            
        except Exception as e:
            print(f"\n✗ Erro ao criar arquivo: {e}")
            return None
    else:
        # Criar template vazio
        template = {
            "CLIENT_ID": "SEU_CLIENT_ID_AQUI",
            "CLIENT_SECRET": "SEU_CLIENT_SECRET_AQUI",
            "GRANT_TYPE": "client_credentials"
        }
        
        template_path = Path.home() / 'Desktop' / 'api_btg_info_TEMPLATE.json'
        
        try:
            with open(template_path, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2)
            
            print(f"\n✓ Template criado em: {template_path}")
            print(f"\n1. Edite o arquivo com suas credenciais")
            print(f"2. Renomeie para: api_btg_info.json")
            print(f"3. Mantenha o arquivo em: {Path.home() / 'Desktop'}")
            
        except Exception as e:
            print(f"\n✗ Erro ao criar template: {e}")


def test_credentials(config):
    """Testa as credenciais"""
    import requests
    
    print("\n=== TESTANDO CREDENCIAIS ===")
    
    auth_url = 'https://funds.btgpactual.com/connect/token'
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'grant_type': config.get('GRANT_TYPE', 'client_credentials'),
        'client_id': config.get('CLIENT_ID', ''),
        'client_secret': config.get('CLIENT_SECRET', ''),
    }
    
    print(f"\nTestando autenticação...")
    
    try:
        response = requests.post(auth_url, headers=headers, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            if 'access_token' in token_data:
                print("✓ Autenticação bem-sucedida!")
                print(f"Token type: {token_data.get('token_type', 'bearer')}")
                print(f"Expires in: {token_data.get('expires_in', 'unknown')} seconds")
                return True
            else:
                print("✗ Resposta 200 mas sem token")
                return False
        else:
            print(f"✗ Erro {response.status_code}: {response.text}")
            
            if response.status_code == 500 and 'Invalid Client' in response.text:
                print("\nPossíveis causas:")
                print("1. CLIENT_ID incorreto")
                print("2. CLIENT_SECRET incorreto")
                print("3. Credenciais expiradas ou revogadas")
                print("4. Cliente não autorizado para este ambiente")
            
            return False
            
    except Exception as e:
        print(f"✗ Erro na requisição: {e}")
        return False


def main():
    print("=== CONFIGURAÇÃO DE CREDENCIAIS BTG ===\n")
    
    # Verificar configuração existente
    config = check_existing_config()
    
    if config:
        # Testar credenciais existentes
        if config.get('CLIENT_ID') and config.get('CLIENT_ID') != 'NÃO DEFINIDO':
            test = input("\nDeseja testar as credenciais existentes? (s/n): ").lower()
            if test == 's':
                if test_credentials(config):
                    print("\n✓ Suas credenciais estão funcionando!")
                else:
                    print("\n✗ As credenciais não estão funcionando.")
                    recreate = input("\nDeseja recriar o arquivo de configuração? (s/n): ").lower()
                    if recreate == 's':
                        create_config_template()
        else:
            print("\nO arquivo existe mas não contém credenciais válidas.")
            create_config_template()
    else:
        # Criar nova configuração
        create_config_template()
    
    print("\n=== PRÓXIMOS PASSOS ===")
    print("\n1. Certifique-se de que o arquivo api_btg_info.json contém:")
    print("   - CLIENT_ID correto")
    print("   - CLIENT_SECRET correto")
    print("   - GRANT_TYPE (geralmente 'client_credentials')")
    print("\n2. Se você não tem essas credenciais:")
    print("   - Entre em contato com o BTG")
    print("   - Solicite acesso à API de fundos")
    print("   - Peça as credenciais de produção")
    print("\n3. Após configurar, execute novamente os testes")


if __name__ == "__main__":
    main()