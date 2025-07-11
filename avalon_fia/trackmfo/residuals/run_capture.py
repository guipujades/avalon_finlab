#!/usr/bin/env python3
"""
Script simplificado para executar captura de portfolios
Uso: python run_capture.py
"""

import sys
from pathlib import Path

# Adicionar trackfia ao path para imports
sys.path.append(str(Path(__file__).parent.parent))

from portfolio_capture import PortfolioCapture, PortfolioCaptureConfig
from data_storage import PortfolioDataStorage
from website_integration import WebsiteDataProcessor


def main():
    """Executa captura básica de portfolios"""
    print("=" * 60)
    print("Track MFO - Captura de Múltiplas Carteiras")
    print("=" * 60)
    
    # Configurar
    config = PortfolioCaptureConfig()
    storage = PortfolioDataStorage()
    capture = PortfolioCapture(config)
    
    print("\nCarteiras configuradas:")
    for portfolio_id, info in config.portfolios.items():
        print(f"  - {info['name']} ({portfolio_id})")
    
    # Capturar dados
    print("\nIniciando captura...")
    results = capture.capture_all_portfolios()
    
    # Salvar resultados
    print("\nSalvando dados...")
    
    # Salvar cada captura no storage
    for portfolio_id, result in results.items():
        if result.get('success'):
            storage.save_portfolio_info(portfolio_id, config.portfolios[portfolio_id])
            capture_id = storage.save_capture(portfolio_id, result)
            print(f"✅ {portfolio_id}: Captura salva (ID: {capture_id})")
        else:
            print(f"❌ {portfolio_id}: Falha - {result.get('error')}")
    
    # Gerar dados para website
    print("\nGerando dados para website...")
    web_processor = WebsiteDataProcessor(storage)
    web_results = web_processor.export_all_portfolios_for_web()
    
    print(f"\nDados exportados para: {web_processor.output_path}")
    print(f"Portfolios processados: {web_results['summary']['successful_exports']}")
    
    # Gerar dashboard consolidado
    dashboard = web_processor.generate_dashboard_data()
    print(f"Dashboard gerado com {len(dashboard['portfolios'])} portfolios")
    
    print("\n✅ Processo concluído!")
    print(f"Dados salvos em: {storage.base_path}")
    print(f"Website data em: {web_processor.output_path}")


if __name__ == '__main__':
    main()