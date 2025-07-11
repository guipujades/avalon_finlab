#!/usr/bin/env python3
"""
Debug - Verificar estrutura dos dados da conta
"""

import json
from pathlib import Path
from btg_api_client import BTGAPIClient

def debug_account_data():
    """Debug da estrutura de dados retornada pela API"""
    
    # Criar cliente
    credentials_path = Path('/mnt/c/Users/guilh/Desktop/api_btg_access.json')
    client = BTGAPIClient(credentials_path=str(credentials_path))
    
    # Obter dados da conta conhecida
    account = "004300296"
    print(f"🔍 Analisando estrutura de dados da conta {account}\n")
    
    try:
        # 1. Obter posição
        position_data = client.get_account_position(account)
        
        print("📊 ESTRUTURA DE POSITION_DATA:")
        print(json.dumps(position_data, indent=2, ensure_ascii=False))
        
        # 2. Verificar tipos de dados
        print("\n📋 TIPOS DE DADOS:")
        print(f"TotalAmount: {type(position_data.get('TotalAmount'))} = {position_data.get('TotalAmount')}")
        
        if position_data.get('InvestmentFund'):
            print("\n🏦 FUNDOS DE INVESTIMENTO:")
            for i, fund in enumerate(position_data['InvestmentFund']):
                print(f"\nFundo {i+1}:")
                print(f"  NetBalance: {type(fund.get('NetBalance'))} = {fund.get('NetBalance')}")
                print(f"  ShareBalance: {type(fund.get('ShareBalance'))} = {fund.get('ShareBalance')}")
                print(f"  ShareValue: {type(fund.get('ShareValue'))} = {fund.get('ShareValue')}")
                
                fund_info = fund.get('Fund', {})
                print(f"  FundName: {fund_info.get('FundName')}")
        
        # 3. Obter informações da conta
        print("\n📄 INFORMAÇÕES DA CONTA:")
        account_info = client.get_account_info(account)
        print(json.dumps(account_info, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_account_data()