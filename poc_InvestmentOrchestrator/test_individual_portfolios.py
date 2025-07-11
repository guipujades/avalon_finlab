#!/usr/bin/env python3
"""
Teste alternativo - Busca carteiras individuais
Quando não há arquivo consolidado de posições disponível
"""

import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from btg_api_client import BTGAPIClient
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_known_accounts(client: BTGAPIClient, account_numbers: list) -> dict:
    """
    Testa contas conhecidas individualmente
    
    Args:
        client: Cliente BTG autenticado
        account_numbers: Lista de números de conta para testar
        
    Returns:
        Resumo das contas encontradas
    """
    results = {
        "tested_accounts": len(account_numbers),
        "found_accounts": 0,
        "total_value": 0.0,
        "accounts_data": [],
        "errors": []
    }
    
    for account in account_numbers:
        logger.info(f"🔄 Testando conta: {account}")
        
        try:
            # Tenta obter posição da conta
            position_data = client.get_account_position(account)
            
            if position_data:
                results["found_accounts"] += 1
                total = position_data.get('TotalAmount', 0)
                results["total_value"] += total
                
                account_summary = {
                    "account_number": account,
                    "total_amount": total,
                    "position_date": position_data.get('PositionDate', 'N/A'),
                    "has_funds": bool(position_data.get('InvestmentFund')),
                    "has_stocks": bool(position_data.get('Stocks')),
                    "has_fixed_income": bool(position_data.get('FixedIncome'))
                }
                
                # Verifica fundos Artesanal
                if position_data.get('InvestmentFund'):
                    artesanal_funds = []
                    for fund in position_data['InvestmentFund']:
                        fund_info = fund.get('Fund', {})
                        fund_name = fund_info.get('FundName', '')
                        if 'artesanal' in fund_name.lower():
                            artesanal_funds.append({
                                "name": fund_name,
                                "balance": fund.get('NetBalance', 0)
                            })
                    
                    if artesanal_funds:
                        account_summary["artesanal_funds"] = artesanal_funds
                
                results["accounts_data"].append(account_summary)
                logger.info(f"✅ Conta {account} encontrada - Total: R$ {total:,.2f}")
                
        except Exception as e:
            error_msg = f"Conta {account}: {str(e)}"
            results["errors"].append(error_msg)
            logger.error(f"❌ Erro: {error_msg}")
    
    return results


def search_accounts_by_pattern(client: BTGAPIClient, patterns: list) -> list:
    """
    Tenta encontrar contas usando padrões conhecidos
    
    Args:
        client: Cliente BTG autenticado
        patterns: Lista de padrões para testar
        
    Returns:
        Lista de contas encontradas
    """
    found_accounts = []
    
    for pattern in patterns:
        logger.info(f"🔍 Testando padrão: {pattern}")
        
        try:
            # Testa se a conta existe
            info = client.get_account_info(pattern)
            if info:
                found_accounts.append(pattern)
                logger.info(f"✅ Conta encontrada: {pattern}")
        except:
            # Conta não existe ou sem acesso
            pass
    
    return found_accounts


def main():
    """Executa teste de carteiras individuais"""
    print("\n🚀 TESTE DE CARTEIRAS INDIVIDUAIS - BTG")
    print("="*70)
    
    try:
        # 1. Criar cliente e autenticar
        logger.info("🔄 Criando cliente BTG...")
        credentials_path = Path('/mnt/c/Users/guilh/Desktop/api_btg_access.json')
        
        if not credentials_path.exists():
            logger.error(f"❌ Arquivo de credenciais não encontrado em: {credentials_path}")
            return
        
        client = BTGAPIClient(credentials_path=str(credentials_path))
        
        # 2. Testar conexão
        if not client.test_connection():
            logger.error("❌ Falha na conexão com API")
            return
        
        logger.info("✅ Conexão estabelecida com sucesso!")
        
        # 3. Listar contas conhecidas para teste
        # Substitua com números de conta reais se conhecidos
        known_accounts = [
            "004300296",  # Exemplo do código original
            "000000001",  # Conta teste 1
            "123456789",  # Conta teste 2
        ]
        
        logger.info("\n📊 TESTANDO CONTAS CONHECIDAS")
        logger.info("="*50)
        
        # 4. Testar contas conhecidas
        results = test_known_accounts(client, known_accounts)
        
        # 5. Gerar relatório
        print("\n" + "="*70)
        print("📊 RELATÓRIO DE TESTE")
        print("="*70)
        print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"\n📈 RESUMO:")
        print(f"   • Contas testadas: {results['tested_accounts']}")
        print(f"   • Contas encontradas: {results['found_accounts']}")
        print(f"   • Valor total encontrado: R$ {results['total_value']:,.2f}")
        
        if results['accounts_data']:
            print(f"\n📋 DETALHES DAS CONTAS ENCONTRADAS:")
            for acc in results['accounts_data']:
                print(f"\n   Conta: {acc['account_number']}")
                print(f"   • Total: R$ {acc['total_amount']:,.2f}")
                print(f"   • Data posição: {acc['position_date']}")
                print(f"   • Tem fundos: {'Sim' if acc['has_funds'] else 'Não'}")
                print(f"   • Tem ações: {'Sim' if acc['has_stocks'] else 'Não'}")
                print(f"   • Tem renda fixa: {'Sim' if acc['has_fixed_income'] else 'Não'}")
                
                if acc.get('artesanal_funds'):
                    print(f"   • 🎯 Fundos Artesanal encontrados:")
                    for fund in acc['artesanal_funds']:
                        print(f"      - {fund['name']}: R$ {fund['balance']:,.2f}")
        
        if results['errors']:
            print(f"\n⚠️ ERROS ENCONTRADOS:")
            for error in results['errors']:
                print(f"   • {error}")
        
        # 6. Salvar resultados
        output_file = f"individual_portfolios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n💾 Resultados salvos em: {output_file}")
        
        # 7. Sugestão
        if results['found_accounts'] == 0:
            print("\n💡 SUGESTÃO:")
            print("   Nenhuma conta foi encontrada com os números testados.")
            print("   Para obter números de conta válidos:")
            print("   1. Verifique com o BTG os números de conta do parceiro")
            print("   2. Consulte a documentação da API para endpoints de listagem")
            print("   3. Entre em contato com o suporte técnico do BTG")
        
    except Exception as e:
        logger.error(f"❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Carrega variáveis de ambiente
    load_dotenv()
    
    # Executa teste
    main()