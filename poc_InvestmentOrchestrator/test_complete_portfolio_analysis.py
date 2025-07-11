#!/usr/bin/env python3
"""
Teste Completo - Análise de Portfólio BTG
Consolida todas as descobertas anteriores e expande a análise
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


class BTGPortfolioAnalyzer:
    """Analisador completo de portfólios BTG"""
    
    def __init__(self, client: BTGAPIClient):
        self.client = client
        self.results = {
            "analysis_date": datetime.now().isoformat(),
            "known_accounts": [],
            "portfolio_summary": {},
            "artesanal_analysis": {},
            "errors": []
        }
    
    def analyze_known_account(self, account_number: str) -> dict:
        """Análise detalhada de uma conta conhecida"""
        logger.info(f"📊 Analisando conta {account_number}...")
        
        try:
            # 1. Obter posição da conta
            position_data = self.client.get_account_position(account_number)
            
            # 2. Obter informações da conta
            try:
                account_info = self.client.get_account_info(account_number)
            except:
                account_info = {}
            
            # 3. Processar dados
            analysis = {
                "account_number": account_number,
                "position_date": position_data.get('PositionDate'),
                "total_amount": position_data.get('TotalAmount', 0),
                "account_info": account_info,
                "asset_allocation": {
                    "funds": 0,
                    "stocks": 0,
                    "fixed_income": 0,
                    "others": 0
                },
                "funds_detail": [],
                "artesanal_funds": []
            }
            
            # 4. Analisar fundos de investimento
            if position_data.get('InvestmentFund'):
                for fund in position_data['InvestmentFund']:
                    fund_info = fund.get('Fund', {})
                    fund_detail = {
                        "name": fund_info.get('FundName'),
                        "manager": fund_info.get('ManagerName'),
                        "cnpj": fund_info.get('FundCNPJ'),
                        "balance": fund.get('NetBalance', 0),
                        "shares": fund.get('ShareBalance', 0),
                        "share_value": fund.get('ShareValue', 0)
                    }
                    
                    analysis['funds_detail'].append(fund_detail)
                    # Garantir que balance é numérico
                    balance_value = float(fund_detail['balance']) if fund_detail['balance'] else 0
                    analysis['asset_allocation']['funds'] += balance_value
                    
                    # Verificar se é Artesanal
                    if fund_detail['name'] and 'artesanal' in fund_detail['name'].lower():
                        analysis['artesanal_funds'].append(fund_detail)
            
            # 5. Analisar ações
            if position_data.get('Stocks'):
                for stock in position_data['Stocks']:
                    analysis['asset_allocation']['stocks'] += stock.get('TotalAmount', 0)
            
            # 6. Analisar renda fixa
            if position_data.get('FixedIncome'):
                for fixed in position_data['FixedIncome']:
                    analysis['asset_allocation']['fixed_income'] += fixed.get('NetValue', 0)
            
            # 7. Calcular percentuais
            total = analysis['total_amount']
            if total > 0:
                for asset_type in analysis['asset_allocation']:
                    value = analysis['asset_allocation'][asset_type]
                    analysis['asset_allocation'][f'{asset_type}_pct'] = (value / total) * 100
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Erro ao analisar conta {account_number}: {e}")
            self.results['errors'].append(f"Conta {account_number}: {str(e)}")
            return None
    
    def search_account_range(self, base_account: str, range_size: int = 10):
        """Busca contas em um range baseado em conta conhecida"""
        logger.info(f"🔍 Buscando contas próximas a {base_account}...")
        
        found_accounts = []
        base_num = int(base_account)
        
        for offset in range(-range_size, range_size + 1):
            test_account = str(base_num + offset).zfill(9)
            
            if test_account == base_account:
                continue  # Pular a conta base
            
            try:
                # Tenta obter informações básicas
                info = self.client.get_account_info(test_account)
                if info:
                    found_accounts.append(test_account)
                    logger.info(f"✅ Conta encontrada: {test_account}")
            except:
                pass  # Conta não existe ou sem acesso
        
        return found_accounts
    
    def generate_comprehensive_report(self):
        """Gera relatório completo da análise"""
        report = []
        report.append("\n" + "="*80)
        report.append("📊 RELATÓRIO COMPLETO DE ANÁLISE DE PORTFÓLIO BTG")
        report.append("="*80)
        report.append(f"📅 Data da análise: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        report.append(f"🏢 Parceiro CNPJ: 47952345000109")
        
        # Resumo geral
        total_accounts = len(self.results['known_accounts'])
        total_value = sum(acc['total_amount'] for acc in self.results['known_accounts'] if acc)
        
        report.append(f"\n📈 RESUMO GERAL:")
        report.append(f"   • Total de contas analisadas: {total_accounts}")
        report.append(f"   • Valor total sob gestão: R$ {total_value:,.2f}")
        
        # Análise Artesanal
        artesanal_accounts = [acc for acc in self.results['known_accounts'] 
                            if acc and acc.get('artesanal_funds')]
        
        if artesanal_accounts:
            report.append(f"\n🎯 ANÁLISE DE FUNDOS ARTESANAL:")
            report.append(f"   • Contas com Artesanal: {len(artesanal_accounts)}")
            
            artesanal_total = 0
            artesanal_funds_list = []
            
            for acc in artesanal_accounts:
                for fund in acc['artesanal_funds']:
                    artesanal_total += fund['balance']
                    artesanal_funds_list.append(fund)
            
            report.append(f"   • Valor total em Artesanal: R$ {artesanal_total:,.2f}")
            report.append(f"   • Número de fundos Artesanal: {len(artesanal_funds_list)}")
            
            # Listar fundos únicos
            unique_funds = {}
            for fund in artesanal_funds_list:
                name = fund['name']
                if name not in unique_funds:
                    unique_funds[name] = {
                        'count': 0,
                        'total_value': 0,
                        'manager': fund['manager']
                    }
                unique_funds[name]['count'] += 1
                unique_funds[name]['total_value'] += fund['balance']
            
            report.append("\n   Fundos Artesanal identificados:")
            for fund_name, data in unique_funds.items():
                report.append(f"   • {fund_name}")
                report.append(f"     - Gestora: {data['manager']}")
                report.append(f"     - Ocorrências: {data['count']}")
                report.append(f"     - Valor total: R$ {data['total_value']:,.2f}")
        
        # Detalhes por conta
        if self.results['known_accounts']:
            report.append(f"\n📋 DETALHES POR CONTA:")
            for acc in self.results['known_accounts']:
                if acc:
                    report.append(f"\n   Conta: {acc['account_number']}")
                    report.append(f"   • Valor total: R$ {acc['total_amount']:,.2f}")
                    report.append(f"   • Data posição: {acc['position_date']}")
                    
                    # Alocação de ativos
                    alloc = acc['asset_allocation']
                    if acc['total_amount'] > 0:
                        report.append(f"   • Alocação:")
                        if alloc.get('funds_pct', 0) > 0:
                            report.append(f"     - Fundos: {alloc.get('funds_pct', 0):.1f}%")
                        if alloc.get('stocks_pct', 0) > 0:
                            report.append(f"     - Ações: {alloc.get('stocks_pct', 0):.1f}%")
                        if alloc.get('fixed_income_pct', 0) > 0:
                            report.append(f"     - Renda Fixa: {alloc.get('fixed_income_pct', 0):.1f}%")
        
        # Erros encontrados
        if self.results['errors']:
            report.append(f"\n⚠️ ERROS ENCONTRADOS:")
            for error in self.results['errors'][:5]:  # Mostrar apenas os 5 primeiros
                report.append(f"   • {error}")
            if len(self.results['errors']) > 5:
                report.append(f"   ... e mais {len(self.results['errors']) - 5} erros")
        
        report.append("\n" + "="*80)
        
        return "\n".join(report)
    
    def save_results(self, filename_prefix: str = "btg_portfolio_analysis"):
        """Salva resultados da análise"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Salvar JSON detalhado
        json_file = f"{filename_prefix}_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Dados salvos em: {json_file}")
        
        # Salvar relatório em texto
        report = self.generate_comprehensive_report()
        txt_file = f"{filename_prefix}_report_{timestamp}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"📄 Relatório salvo em: {txt_file}")
        
        return json_file, txt_file


def main():
    """Executa análise completa de portfólio"""
    print("\n🚀 ANÁLISE COMPLETA DE PORTFÓLIO BTG")
    print("="*80)
    
    try:
        # 1. Inicializar cliente
        logger.info("🔄 Inicializando cliente BTG...")
        credentials_path = Path('/mnt/c/Users/guilh/Desktop/api_btg_access.json')
        
        if not credentials_path.exists():
            logger.error(f"❌ Credenciais não encontradas: {credentials_path}")
            return
        
        client = BTGAPIClient(credentials_path=str(credentials_path))
        
        if not client.test_connection():
            logger.error("❌ Falha na conexão")
            return
        
        # 2. Criar analisador
        analyzer = BTGPortfolioAnalyzer(client)
        
        # 3. Analisar conta conhecida
        known_account = "004300296"
        logger.info(f"\n📊 FASE 1: Analisando conta conhecida {known_account}")
        
        account_analysis = analyzer.analyze_known_account(known_account)
        if account_analysis:
            analyzer.results['known_accounts'].append(account_analysis)
        
        # 4. Buscar contas próximas
        logger.info(f"\n🔍 FASE 2: Buscando contas próximas")
        nearby_accounts = analyzer.search_account_range(known_account, range_size=5)
        
        if nearby_accounts:
            logger.info(f"✅ Encontradas {len(nearby_accounts)} contas adicionais")
            for acc in nearby_accounts:
                analysis = analyzer.analyze_known_account(acc)
                if analysis:
                    analyzer.results['known_accounts'].append(analysis)
        
        # 5. Tentar obter todas as posições novamente
        logger.info(f"\n📦 FASE 3: Tentando obter arquivo consolidado")
        try:
            all_positions = client.get_all_accounts_positions()
            if all_positions and 'response' in all_positions and all_positions['response']:
                analyzer.results['consolidated_file_available'] = True
                analyzer.results['consolidated_file_url'] = all_positions['response'].get('url')
            else:
                analyzer.results['consolidated_file_available'] = False
                if all_positions and 'errors' in all_positions:
                    analyzer.results['consolidated_file_error'] = all_positions['errors']
        except Exception as e:
            analyzer.results['consolidated_file_available'] = False
            analyzer.results['consolidated_file_error'] = str(e)
        
        # 6. Gerar e exibir relatório
        report = analyzer.generate_comprehensive_report()
        print(report)
        
        # 7. Salvar resultados
        json_file, txt_file = analyzer.save_results()
        
        # 8. Sugestões finais
        print("\n💡 PRÓXIMOS PASSOS:")
        print("1. Solicitar ao BTG lista completa de contas autorizadas")
        print("2. Verificar com o BTG sobre disponibilidade do arquivo consolidado")
        print("3. Implementar webhook para receber dados assíncronos")
        print("4. Expandir análise para incluir rentabilidade histórica")
        
    except Exception as e:
        logger.error(f"❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    load_dotenv()
    main()