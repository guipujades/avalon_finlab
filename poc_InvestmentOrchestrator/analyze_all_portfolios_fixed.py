#!/usr/bin/env python3
"""
Análise Completa de Carteiras BTG - Versão Corrigida
Baseada na estrutura real dos dados retornados pela API
"""

import json
from pathlib import Path
from datetime import datetime
from btg_api_client import BTGAPIClient
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def calculate_fund_balance(fund_data: dict) -> float:
    """Calcula o saldo total de um fundo baseado nas aquisições"""
    total_balance = 0.0
    
    if 'Acquisition' in fund_data and fund_data['Acquisition']:
        for acquisition in fund_data['Acquisition']:
            # Usar NetAssetValue que é o valor líquido
            net_value = acquisition.get('NetAssetValue', '0')
            try:
                total_balance += float(net_value)
            except:
                pass
    
    return total_balance


def analyze_btg_portfolio(account_number: str = "004300296"):
    """Análise completa do portfólio BTG"""
    
    # Inicializar cliente
    credentials_path = Path('/mnt/c/Users/guilh/Desktop/api_btg_access.json')
    client = BTGAPIClient(credentials_path=str(credentials_path))
    
    logger.info("🚀 ANÁLISE COMPLETA DE CARTEIRAS BTG")
    logger.info("="*70)
    
    # Obter dados da conta
    position_data = client.get_account_position(account_number)
    account_info = client.get_account_info(account_number)
    
    # Processar valor total (corrigir typo da API)
    total_amount = float(position_data.get('TotalAmmount', '0'))
    
    logger.info(f"\n📊 CONTA: {account_number}")
    logger.info(f"👤 Titular: {account_info['holder']['name']}")
    logger.info(f"📅 Data Posição: {position_data.get('PositionDate')}")
    logger.info(f"💰 Valor Total: R$ {total_amount:,.2f}")
    
    # Análise por categoria
    logger.info(f"\n📈 RESUMO POR CATEGORIA:")
    summary = position_data.get('SummaryAccounts', [])
    for item in summary:
        market = item.get('MarketName')
        value = float(item.get('EndPositionValue', '0'))
        logger.info(f"   • {market}: R$ {value:,.2f}")
    
    # Análise de Fundos
    funds = position_data.get('InvestmentFund', [])
    if funds:
        logger.info(f"\n🏦 FUNDOS DE INVESTIMENTO ({len(funds)} fundos):")
        
        total_funds_value = 0
        artesanal_funds = []
        
        for fund in funds:
            fund_info = fund.get('Fund', {})
            fund_name = fund_info.get('FundName', 'N/A')
            manager = fund_info.get('ManagerName', 'N/A')
            
            # Calcular saldo total do fundo
            fund_balance = calculate_fund_balance(fund)
            total_funds_value += fund_balance
            
            logger.info(f"\n   📊 {fund_name}")
            logger.info(f"      • Gestora: {manager}")
            logger.info(f"      • Valor: R$ {fund_balance:,.2f}")
            logger.info(f"      • Aquisições: {len(fund.get('Acquisition', []))}")
            
            # Verificar se é Artesanal
            if 'artesanal' in fund_name.lower():
                artesanal_funds.append({
                    'name': fund_name,
                    'manager': manager,
                    'balance': fund_balance,
                    'acquisitions': len(fund.get('Acquisition', []))
                })
        
        logger.info(f"\n   💰 Total em Fundos: R$ {total_funds_value:,.2f}")
        
        # Resumo Artesanal
        if artesanal_funds:
            logger.info(f"\n🎯 FUNDOS ARTESANAL IDENTIFICADOS:")
            total_artesanal = sum(f['balance'] for f in artesanal_funds)
            
            for fund in artesanal_funds:
                logger.info(f"   • {fund['name']}")
                logger.info(f"     - Valor: R$ {fund['balance']:,.2f}")
                logger.info(f"     - Percentual do portfólio: {(fund['balance']/total_amount*100):.2f}%")
            
            logger.info(f"\n   💰 Total em Artesanal: R$ {total_artesanal:,.2f}")
            logger.info(f"   📊 Percentual Artesanal/Total: {(total_artesanal/total_amount*100):.2f}%")
    
    # Análise de Renda Fixa
    fixed_income = position_data.get('FixedIncome', [])
    if fixed_income:
        logger.info(f"\n📈 RENDA FIXA ({len(fixed_income)} títulos):")
        
        total_rf_value = 0
        for fi in fixed_income:
            issuer = fi.get('Issuer', 'N/A')
            ticker = fi.get('Ticker', 'N/A')
            net_value = float(fi.get('NetValue', '0'))
            maturity = fi.get('MaturityDate', 'N/A')
            
            total_rf_value += net_value
            
            logger.info(f"\n   📄 {ticker}")
            logger.info(f"      • Emissor: {issuer}")
            logger.info(f"      • Valor: R$ {net_value:,.2f}")
            logger.info(f"      • Vencimento: {maturity[:10] if maturity != 'N/A' else 'N/A'}")
        
        logger.info(f"\n   💰 Total em Renda Fixa: R$ {total_rf_value:,.2f}")
    
    # Conta Corrente
    cash = position_data.get('Cash', [])
    if cash and cash[0].get('CurrentAccount'):
        cc_value = float(cash[0]['CurrentAccount'].get('Value', '0'))
        logger.info(f"\n💵 CONTA CORRENTE: R$ {cc_value:,.2f}")
    
    # Tentar obter todas as posições
    logger.info(f"\n📦 VERIFICANDO ARQUIVO CONSOLIDADO:")
    try:
        all_positions = client.get_all_accounts_positions()
        if 'errors' in all_positions:
            logger.info(f"   ⚠️ {all_positions['errors'][0]['message']}")
        elif 'response' in all_positions and all_positions['response']:
            logger.info(f"   ✅ URL disponível: {all_positions['response'].get('url')}")
    except Exception as e:
        logger.info(f"   ❌ Erro: {e}")
    
    logger.info("\n" + "="*70)
    
    # Salvar resultados
    results = {
        "analysis_date": datetime.now().isoformat(),
        "account_number": account_number,
        "holder": account_info['holder']['name'],
        "total_amount": total_amount,
        "position_data": position_data,
        "account_info": account_info
    }
    
    output_file = f"portfolio_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n💾 Análise salva em: {output_file}")
    
    return results


if __name__ == "__main__":
    analyze_btg_portfolio()