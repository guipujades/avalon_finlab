#!/usr/bin/env python3
"""
Teste BTG API Real - Versão Corrigida
Usa o código correto fornecido pelo usuário
"""

import json
from pathlib import Path
from btg_api_client import BTGAPIClient, create_btg_client


def test_token_real():
    """Teste 1: Captura token real usando código correto"""
    print("🔐 TESTE 1: Token Real BTG")
    print("="*50)
    
    try:
        client = create_btg_client()
        token = client.get_access_token()
        
        print(f"✅ TOKEN CAPTURADO COM SUCESSO!")
        print(f"🔑 Token: {token[:50]}...")
        print(f"📏 Tamanho: {len(token)} caracteres")
        print(f"⏰ Expira: {client.token_expiry}")
        
        return client
        
    except Exception as e:
        print(f"❌ Erro ao capturar token: {e}")
        return None


def test_account_position(client: BTGAPIClient, account_number: str):
    """Teste 2: Posição de uma conta específica"""
    print(f"\n📊 TESTE 2: Posição da Conta {account_number}")
    print("="*50)
    
    try:
        position_data = client.get_account_position(account_number)
        
        # Informações básicas
        total = position_data.get('TotalAmount', 0)
        date = position_data.get('PositionDate', 'N/A')
        account = position_data.get('AccountNumber', account_number)
        
        print(f"✅ POSIÇÃO OBTIDA COM SUCESSO!")
        print(f"📊 Conta: {account}")
        print(f"💰 Total: R$ {total:,.2f}")
        print(f"📅 Data: {date}")
        
        # Lista categorias disponíveis
        categories = []
        for key in position_data.keys():
            if key not in ['AccountNumber', 'PositionDate', 'TotalAmount', 'Agency', 'ContractVersion']:
                if position_data[key]:  # Se não estiver vazio
                    categories.append(key)
        
        print(f"📋 Categorias com dados: {', '.join(categories)}")
        
        # Busca fundos Artesanal especificamente
        artesanal_funds = []
        artesanal_total = 0
        
        for fund in position_data.get('InvestmentFund', []):
            fund_info = fund.get('Fund', {})
            fund_name = fund_info.get('FundName', '')
            
            if 'Artesanal' in fund_name:
                fund_value = 0
                for acquisition in fund.get('Acquisition', []):
                    fund_value += acquisition.get('GrossAssetValue', 0)
                
                artesanal_funds.append({
                    'name': fund_name,
                    'manager': fund_info.get('ManagerName', 'N/A'),
                    'value': fund_value
                })
                artesanal_total += fund_value
        
        if artesanal_funds:
            print(f"\n🎯 FUNDOS ARTESANAL ENCONTRADOS:")
            for fund in artesanal_funds:
                print(f"  • {fund['name']}")
                print(f"    Gestora: {fund['manager']}")
                print(f"    Valor: R$ {fund['value']:,.2f}")
            
            artesanal_pct = (artesanal_total / total * 100) if total > 0 else 0
            print(f"\n🎯 TOTAL ARTESANAL: R$ {artesanal_total:,.2f} ({artesanal_pct:.1f}%)")
        else:
            print(f"\n⚠️ Nenhum fundo Artesanal encontrado nesta conta")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao obter posição: {e}")
        return False


def test_all_positions(client: BTGAPIClient):
    """Teste 3: Todas as posições"""
    print(f"\n📊 TESTE 3: Todas as Posições do Parceiro")
    print("="*50)
    
    try:
        all_positions = client.get_all_accounts_positions()
        
        print(f"✅ RESPOSTA OBTIDA!")
        print(f"📋 Estrutura da resposta:")
        
        # Mostra estrutura da resposta
        for key, value in all_positions.items():
            if isinstance(value, dict):
                print(f"  {key}: {list(value.keys())}")
            else:
                print(f"  {key}: {type(value).__name__}")
        
        # Se tem URL de download
        if 'response' in all_positions:
            response_data = all_positions['response']
            if 'url' in response_data:
                download_url = response_data['url']
                print(f"\n🔗 URL de Download:")
                print(f"   {download_url}")
                
                from urllib.parse import urlparse
                parsed = urlparse(download_url)
                filename = parsed.path.split('/')[-1] if parsed.path else "unknown"
                print(f"📄 Arquivo: {filename}")
                print(f"🌐 Servidor: {parsed.netloc}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao obter todas as posições: {e}")
        return False


def main():
    """Executa todos os testes"""
    print("🚀 TESTE COMPLETO - BTG API REAL")
    print("="*60)
    print("✅ Usando código corrigido com 'data' em vez de 'params'")
    print("="*60)
    
    # Teste 1: Token
    client = test_token_real()
    if not client:
        print("\n❌ TESTES ABORTADOS - Falha no token")
        return
    
    # Teste 2: Conta específica (substitua pelo número real se quiser)
    # test_account_position(client, "004300296")  # Descomente e use número real
    
    # Teste 3: Todas as posições
    success = test_all_positions(client)
    
    print("\n" + "="*60)
    if success:
        print("🎉 TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
        print("✅ Token real capturado")
        print("✅ API BTG funcionando")
        print("✅ Sistema pronto para uso")
        print("\n💡 Para testar conta específica:")
        print("   Descomente a linha test_account_position e use número real")
    else:
        print("⚠️ TESTES PARCIALMENTE CONCLUÍDOS")
        print("✅ Token funcionando")
        print("❌ Algum problema com outras APIs")


if __name__ == "__main__":
    main() 