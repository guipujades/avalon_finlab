#!/usr/bin/env python3
"""
Teste para capturar TODAS as carteiras do BTG
Baseado no código existente com melhorias para processar o ZIP de posições
"""

import os
import json
import zipfile
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from btg_api_client import BTGAPIClient, create_btg_client
import logging

# Configurar logging detalhado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def download_positions_file(url: str, output_path: str = "positions.zip") -> bool:
    """
    Faz download do arquivo ZIP de posições
    
    Args:
        url: URL do arquivo ZIP
        output_path: Caminho para salvar o arquivo
        
    Returns:
        True se sucesso
    """
    try:
        logger.info(f"📥 Baixando arquivo de posições...")
        logger.info(f"🔗 URL: {url}")
        
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Salva o arquivo
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = os.path.getsize(output_path)
        logger.info(f"✅ Download concluído! Tamanho: {file_size:,} bytes")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no download: {e}")
        return False


def process_positions_zip(zip_path: str) -> dict:
    """
    Processa o arquivo ZIP de posições e extrai informações
    
    Args:
        zip_path: Caminho do arquivo ZIP
        
    Returns:
        Dicionário com dados processados
    """
    try:
        logger.info(f"📦 Processando arquivo ZIP: {zip_path}")
        
        results = {
            "total_accounts": 0,
            "total_value": 0.0,
            "accounts": [],
            "funds_summary": {},
            "artesanal_funds": []
        }
        
        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            # Lista arquivos no ZIP
            file_list = zip_file.namelist()
            logger.info(f"📋 Arquivos encontrados no ZIP: {len(file_list)}")
            
            for filename in file_list:
                if filename.endswith('.json'):
                    logger.info(f"🔄 Processando: {filename}")
                    
                    # Lê o arquivo JSON
                    with zip_file.open(filename) as json_file:
                        data = json.load(json_file)
                        
                        # Processa dados da conta
                        account_info = process_account_data(data)
                        results["accounts"].append(account_info)
                        results["total_accounts"] += 1
                        results["total_value"] += account_info["total_amount"]
                        
                        # Atualiza resumo de fundos
                        for fund in account_info["funds"]:
                            fund_name = fund["name"]
                            if fund_name not in results["funds_summary"]:
                                results["funds_summary"][fund_name] = {
                                    "count": 0,
                                    "total_value": 0.0,
                                    "manager": fund["manager"]
                                }
                            results["funds_summary"][fund_name]["count"] += 1
                            results["funds_summary"][fund_name]["total_value"] += fund["balance"]
                            
                            # Verifica fundos Artesanal
                            if "artesanal" in fund_name.lower():
                                results["artesanal_funds"].append({
                                    "account": account_info["account_number"],
                                    "fund": fund
                                })
        
        logger.info(f"✅ Processamento concluído!")
        return results
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar ZIP: {e}")
        return {}


def process_account_data(data: dict) -> dict:
    """
    Processa dados de uma conta individual
    
    Args:
        data: Dados JSON da conta
        
    Returns:
        Informações resumidas da conta
    """
    account_info = {
        "account_number": data.get("AccountNumber", "N/A"),
        "position_date": data.get("PositionDate", "N/A"),
        "total_amount": data.get("TotalAmount", 0.0),
        "funds": [],
        "stocks": [],
        "fixed_income": []
    }
    
    # Processa fundos de investimento
    if "InvestmentFund" in data and data["InvestmentFund"]:
        for fund in data["InvestmentFund"]:
            fund_data = fund.get("Fund", {})
            account_info["funds"].append({
                "name": fund_data.get("FundName", "N/A"),
                "manager": fund_data.get("ManagerName", "N/A"),
                "cnpj": fund_data.get("FundCNPJ", "N/A"),
                "balance": fund.get("NetBalance", 0.0),
                "shares": fund.get("ShareBalance", 0.0)
            })
    
    # Processa ações
    if "Stocks" in data and data["Stocks"]:
        for stock in data["Stocks"]:
            account_info["stocks"].append({
                "ticker": stock.get("Ticker", "N/A"),
                "company": stock.get("CompanyName", "N/A"),
                "quantity": stock.get("Quantity", 0),
                "total_value": stock.get("TotalAmount", 0.0)
            })
    
    # Processa renda fixa
    if "FixedIncome" in data and data["FixedIncome"]:
        for fixed in data["FixedIncome"]:
            account_info["fixed_income"].append({
                "type": fixed.get("Type", "N/A"),
                "issuer": fixed.get("IssuerName", "N/A"),
                "value": fixed.get("NetValue", 0.0),
                "maturity": fixed.get("MaturityDate", "N/A")
            })
    
    return account_info


def generate_report(results: dict) -> str:
    """
    Gera relatório formatado dos resultados
    
    Args:
        results: Dados processados
        
    Returns:
        Relatório em string
    """
    report = []
    report.append("\n" + "="*70)
    report.append("📊 RELATÓRIO COMPLETO DE CARTEIRAS BTG")
    report.append("="*70)
    report.append(f"📅 Data do relatório: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    report.append("")
    
    # Resumo geral
    report.append("📈 RESUMO GERAL:")
    report.append(f"   • Total de contas: {results['total_accounts']:,}")
    report.append(f"   • Valor total sob custódia: R$ {results['total_value']:,.2f}")
    report.append(f"   • Fundos únicos identificados: {len(results['funds_summary'])}")
    report.append("")
    
    # Top 10 fundos por valor total
    if results['funds_summary']:
        report.append("🏆 TOP 10 FUNDOS POR VALOR TOTAL:")
        sorted_funds = sorted(
            results['funds_summary'].items(),
            key=lambda x: x[1]['total_value'],
            reverse=True
        )[:10]
        
        for i, (fund_name, fund_data) in enumerate(sorted_funds, 1):
            report.append(f"   {i}. {fund_name}")
            report.append(f"      • Gestora: {fund_data['manager']}")
            report.append(f"      • Contas investidas: {fund_data['count']}")
            report.append(f"      • Valor total: R$ {fund_data['total_value']:,.2f}")
        report.append("")
    
    # Fundos Artesanal
    if results['artesanal_funds']:
        report.append("🎯 FUNDOS ARTESANAL ENCONTRADOS:")
        report.append(f"   • Total de posições: {len(results['artesanal_funds'])}")
        
        artesanal_total = sum(
            af['fund']['balance'] for af in results['artesanal_funds']
        )
        report.append(f"   • Valor total em Artesanal: R$ {artesanal_total:,.2f}")
        
        # Lista algumas posições
        report.append("\n   Algumas posições Artesanal:")
        for i, artesanal in enumerate(results['artesanal_funds'][:5], 1):
            report.append(f"   {i}. Conta: {artesanal['account']}")
            report.append(f"      • Fundo: {artesanal['fund']['name']}")
            report.append(f"      • Valor: R$ {artesanal['fund']['balance']:,.2f}")
        
        if len(results['artesanal_funds']) > 5:
            report.append(f"   ... e mais {len(results['artesanal_funds']) - 5} posições")
    
    report.append("\n" + "="*70)
    
    return "\n".join(report)


def save_results(results: dict, filename: str = "portfolios_analysis.json"):
    """
    Salva resultados em arquivo JSON
    
    Args:
        results: Dados para salvar
        filename: Nome do arquivo
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Resultados salvos em: {filename}")
    except Exception as e:
        logger.error(f"❌ Erro ao salvar resultados: {e}")


def main():
    """Executa teste completo de captura de todas as carteiras"""
    print("\n🚀 TESTE COMPLETO - TODAS AS CARTEIRAS BTG")
    print("="*70)
    
    try:
        # 1. Criar cliente e autenticar
        logger.info("🔄 Criando cliente BTG...")
        # Usar caminho específico do Desktop Windows
        credentials_path = Path('/mnt/c/Users/guilh/Desktop/api_btg_access.json')
        if not credentials_path.exists():
            logger.error(f"❌ Arquivo de credenciais não encontrado em: {credentials_path}")
            return
        
        client = BTGAPIClient(credentials_path=str(credentials_path))
        
        # 2. Testar conexão
        if not client.test_connection():
            logger.error("❌ Falha na conexão com API")
            return
        
        # 3. Obter URL do arquivo de posições
        logger.info("🔄 Obtendo URL do arquivo de posições...")
        positions_response = client.get_all_accounts_positions()
        
        # Log da resposta completa para debug
        logger.info(f"📋 Resposta da API: {json.dumps(positions_response, indent=2, ensure_ascii=False)}")
        
        # Verificar estrutura da resposta
        if not positions_response:
            logger.error("❌ Resposta vazia da API")
            return
            
        if isinstance(positions_response, dict):
            # Tentar diferentes estruturas de resposta
            download_url = None
            
            # Estrutura 1: response.url
            if 'response' in positions_response and isinstance(positions_response['response'], dict):
                download_url = positions_response['response'].get('url')
            
            # Estrutura 2: direto na raiz
            elif 'url' in positions_response:
                download_url = positions_response['url']
            
            # Estrutura 3: download_url
            elif 'download_url' in positions_response:
                download_url = positions_response['download_url']
            
            if not download_url:
                logger.error("❌ URL de download não encontrada na resposta")
                logger.error(f"Estrutura da resposta: {list(positions_response.keys())}")
                return
        else:
            logger.error(f"❌ Resposta inesperada: tipo {type(positions_response)}")
            return
            
        logger.info(f"✅ URL obtida: {download_url}")
        
        # 4. Baixar arquivo ZIP
        zip_filename = f"positions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        if download_positions_file(download_url, zip_filename):
            
            # 5. Processar arquivo ZIP
            results = process_positions_zip(zip_filename)
            
            if results and results['total_accounts'] > 0:
                # 6. Gerar relatório
                report = generate_report(results)
                print(report)
                
                # 7. Salvar resultados
                save_results(results)
                
                # 8. Salvar relatório em texto
                report_filename = f"portfolios_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(report_filename, 'w', encoding='utf-8') as f:
                    f.write(report)
                logger.info(f"📄 Relatório salvo em: {report_filename}")
                
                # 9. Limpar arquivo ZIP (opcional)
                # os.remove(zip_filename)
                
                logger.info("✅ TESTE CONCLUÍDO COM SUCESSO!")
            else:
                logger.error("❌ Nenhuma conta processada do arquivo ZIP")
        else:
            logger.error("❌ Falha no download do arquivo de posições")
            
    except Exception as e:
        logger.error(f"❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Carrega variáveis de ambiente
    load_dotenv()
    
    # Executa teste
    main()