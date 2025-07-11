#!/usr/bin/env python3
"""
Teste REAL da API BTG - Captura Token e Carteiras
SEM MOCK - Apenas API real
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from btg_api_client import BTGAPIClient

def test_real_btg_token():
    """Teste para capturar token real da API BTG"""
    print("🔐 TESTE: Captura de Token Real da API BTG")
    print("="*60)
    
    # Carrega variáveis de ambiente
    load_dotenv()
    
    # Busca arquivo de credenciais
    credentials_paths = [
        Path.home() / 'Desktop' / 'api_btg_access.json',
        Path.cwd() / 'api_btg_access.json',
        Path.cwd() / 'credentials' / 'api_btg_access.json'
    ]
    
    credentials_file = None
    for path in credentials_paths:
        if path.exists():
            credentials_file = path
            break
    
    if not credentials_file:
        print("❌ Arquivo de credenciais não encontrado!")
        print("   Procurei em:")
        for path in credentials_paths:
            print(f"     {path}")
        print("\n💡 Crie o arquivo 'api_btg_access.json' com:")
        print('   {"client_id": "seu_client_id", "client_secret": "seu_client_secret"}')
        return False
    
    print(f"✅ Credenciais encontradas: {credentials_file}")
    
    try:
        # Inicializa cliente BTG REAL
        print("\n🔄 Inicializando cliente BTG...")
        client = BTGAPIClient(credentials_path=str(credentials_file))
        
        # Tenta obter token real
        print("🔄 Obtendo token de acesso real...")
        token = client.get_access_token()
        
        if token:
            print("✅ TOKEN CAPTURADO COM SUCESSO!")
            print(f"🔑 Token: {token[:50]}...")
            print(f"📏 Tamanho do token: {len(token)} caracteres")
            print(f"⏰ Expira em: {client.token_expiry}")
            
            return client
        else:
            print("❌ Falha ao obter token")
            return False
            
    except FileNotFoundError as e:
        print(f"❌ Erro: Arquivo de credenciais não encontrado - {e}")
        return False
    except KeyError as e:
        print(f"❌ Erro: Chave não encontrada no arquivo de credenciais - {e}")
        return False
    except Exception as e:
        print(f"❌ Erro ao capturar token: {e}")
        return False

def test_all_portfolios(client: BTGAPIClient):
    """Teste para capturar todas as carteiras"""
    print("\n📊 TESTE: Captura de Todas as Carteiras")
    print("="*60)
    
    try:
        print("🔄 Obtendo todas as posições do parceiro...")
        
        # Chama API para obter todas as posições (retorna URL do ZIP)
        all_positions_response = client.get_all_accounts_positions()
        
        print("✅ RESPOSTA DA API RECEBIDA!")
        print(f"📋 Resposta completa:")
        print(json.dumps(all_positions_response, indent=2, ensure_ascii=False))
        
        # Verifica se tem URL para download
        if 'response' in all_positions_response:
            response_data = all_positions_response['response']
            if 'url' in response_data:
                download_url = response_data['url']
                print(f"\n🔗 URL de Download das Posições:")
                print(f"   {download_url}")
                
                # Extrai informações úteis da URL
                from urllib.parse import urlparse
                parsed_url = urlparse(download_url)
                filename = parsed_url.path.split('/')[-1] if parsed_url.path else "unknown"
                
                print(f"📄 Nome do arquivo: {filename}")
                print(f"🌐 Servidor: {parsed_url.netloc}")
                
        return True
        
    except Exception as e:
        print(f"❌ Erro ao obter carteiras: {e}")
        return False

def test_single_account(client: BTGAPIClient, account_number: str = None):
    """Teste para uma conta específica (se fornecida)"""
    if not account_number:
        print("\n⚠️ Nenhuma conta específica fornecida para teste individual")
        return
    
    print(f"\n📊 TESTE: Conta Específica {account_number}")
    print("="*60)
    
    try:
        print(f"🔄 Obtendo posição da conta {account_number}...")
        
        position_data = client.get_account_position(account_number)
        
        print("✅ POSIÇÃO OBTIDA COM SUCESSO!")
        
        # Extrai informações principais
        total_amount = position_data.get('TotalAmount', 0)
        position_date = position_data.get('PositionDate', 'N/A')
        account_num = position_data.get('AccountNumber', account_number)
        
        print(f"📊 Resumo da Conta {account_num}:")
        print(f"   💰 Total: R$ {total_amount:,.2f}")
        print(f"   📅 Data: {position_date}")
        
        # Lista categorias disponíveis
        categories = []
        for key in position_data.keys():
            if key not in ['AccountNumber', 'PositionDate', 'TotalAmount', 'Agency', 'ContractVersion']:
                if position_data[key]:  # Se não estiver vazio
                    categories.append(key)
        
        print(f"   📋 Categorias com dados: {', '.join(categories)}")
        
        # Se tem fundos, mostra alguns detalhes
        if 'InvestmentFund' in position_data:
            funds = position_data['InvestmentFund']
            print(f"\n🏦 Fundos de Investimento ({len(funds)} fundos):")
            
            for i, fund in enumerate(funds[:3], 1):  # Mostra apenas os 3 primeiros
                fund_info = fund.get('Fund', {})
                fund_name = fund_info.get('FundName', 'N/A')
                manager = fund_info.get('ManagerName', 'N/A')
                
                print(f"   {i}. {fund_name}")
                print(f"      Gestora: {manager}")
                
                # Verifica se é Artesanal
                if 'Artesanal' in fund_name:
                    print(f"      🎯 FUNDO ARTESANAL DETECTADO!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao obter conta {account_number}: {e}")
        return False

def main():
    """Executa teste completo da API real"""
    print("🚀 TESTE REAL - API BTG PACTUAL")
    print("="*60)
    print("⚠️  ATENÇÃO: Este teste usa a API REAL do BTG")
    print("⚠️  Certifique-se de ter credenciais válidas")
    print("="*60)
    
    # Teste 1: Captura token real
    client = test_real_btg_token()
    if not client:
        print("\n❌ TESTE ABORTADO - Falha na autenticação")
        return
    
    # Teste 2: Obter todas as carteiras
    success = test_all_portfolios(client)
    
    if success:
        print("\n✅ TESTE CONCLUÍDO COM SUCESSO!")
        print("✅ Token capturado")
        print("✅ API de carteiras acessada")
        print("✅ Sistema pronto para uso")
    else:
        print("\n⚠️ TESTE PARCIALMENTE CONCLUÍDO")
        print("✅ Token capturado")
        print("❌ Problema ao acessar carteiras")
    
    # Opção para testar conta específica (descomente se quiser)
    # test_single_account(client, "004300296")  # Substitua pelo número real

if __name__ == "__main__":
    main() 