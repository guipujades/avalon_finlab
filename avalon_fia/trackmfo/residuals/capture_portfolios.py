#!/usr/bin/env python3
"""
Script principal para captura automática de dados de múltiplas carteiras
Baseado no update_and_run.py mas expandido para múltiplos portfolios
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
import schedule
import time

# Adicionar trackfia ao path
sys.path.append(str(Path(__file__).parent))

from portfolio_capture import PortfolioCapture, PortfolioCaptureConfig
from data_storage import PortfolioDataStorage


# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('portfolio_capture.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PortfolioCaptureRunner:
    """Gerenciador de execução de capturas"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Inicializa o runner
        
        Args:
            config_file: Arquivo de configuração JSON
        """
        self.config = self._load_config(config_file)
        self.capture_config = PortfolioCaptureConfig()
        self.storage = PortfolioDataStorage()
        
        # Atualizar configuração com dados do arquivo
        if self.config:
            self._update_capture_config()
    
    def _load_config(self, config_file: str) -> dict:
        """Carrega configuração de arquivo JSON"""
        if config_file and Path(config_file).exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Configuração padrão
            return {
                'portfolios': {
                    'avalon_fia': {
                        'type': 'fund',
                        'name': 'AVALON FIA',
                        'cnpj': '47952345000109',
                        'enabled': True
                    }
                },
                'capture_schedule': {
                    'daily_at': '09:00',
                    'on_startup': True
                },
                'storage': {
                    'formats': ['pickle', 'json', 'excel'],
                    'cleanup_days': 90
                },
                'notifications': {
                    'on_error': True,
                    'on_success': False
                }
            }
    
    def _update_capture_config(self):
        """Atualiza configuração de captura com dados do arquivo"""
        if 'portfolios' in self.config:
            self.capture_config.portfolios = self.config['portfolios']
    
    def capture_all(self) -> dict:
        """
        Executa captura de todos os portfolios habilitados
        
        Returns:
            Resumo da execução
        """
        logger.info("=" * 60)
        logger.info("Iniciando captura de portfolios")
        logger.info(f"Data/Hora: {datetime.now()}")
        logger.info("=" * 60)
        
        # Filtrar apenas portfolios habilitados
        enabled_portfolios = {
            k: v for k, v in self.capture_config.portfolios.items()
            if v.get('enabled', True)
        }
        
        logger.info(f"Portfolios para capturar: {len(enabled_portfolios)}")
        
        # Executar captura
        capture = PortfolioCapture(self.capture_config)
        results = {}
        
        for portfolio_id, portfolio_info in enabled_portfolios.items():
            logger.info(f"\nCapturando: {portfolio_info['name']}")
            
            try:
                if portfolio_info['type'] == 'fund':
                    result = capture.capture_fund_data(portfolio_info)
                elif portfolio_info['type'] == 'digital':
                    result = capture.capture_digital_account_data(portfolio_info)
                else:
                    logger.warning(f"Tipo desconhecido: {portfolio_info['type']}")
                    continue
                
                # Salvar no storage
                if result['success']:
                    self.storage.save_portfolio_info(portfolio_id, portfolio_info)
                    capture_id = self.storage.save_capture(portfolio_id, result)
                    logger.info(f"✅ Captura salva com ID: {capture_id}")
                else:
                    logger.error(f"❌ Falha na captura: {result.get('error')}")
                
                results[portfolio_id] = result
                
            except Exception as e:
                logger.error(f"❌ Erro ao capturar {portfolio_id}: {str(e)}")
                results[portfolio_id] = {
                    'success': False,
                    'error': str(e)
                }
            
            # Delay entre capturas
            time.sleep(2)
        
        # Salvar resultados em diferentes formatos
        self._save_results(capture, results)
        
        # Gerar relatório resumido
        self._generate_summary(results)
        
        # Limpeza de dados antigos
        if self.config.get('storage', {}).get('cleanup_days'):
            self.storage.cleanup_old_data(self.config['storage']['cleanup_days'])
        
        return results
    
    def _save_results(self, capture: PortfolioCapture, results: dict):
        """Salva resultados em diferentes formatos"""
        formats = self.config.get('storage', {}).get('formats', ['pickle'])
        
        for format in formats:
            try:
                file_path = capture.save_captured_data(format)
                logger.info(f"✅ Dados salvos em formato {format}: {file_path}")
            except Exception as e:
                logger.error(f"❌ Erro ao salvar em {format}: {str(e)}")
    
    def _generate_summary(self, results: dict):
        """Gera e exibe resumo da execução"""
        success_count = sum(1 for r in results.values() if r.get('success'))
        total_count = len(results)
        
        logger.info("\n" + "=" * 60)
        logger.info("RESUMO DA EXECUÇÃO")
        logger.info("=" * 60)
        logger.info(f"Total de portfolios: {total_count}")
        logger.info(f"Capturas bem-sucedidas: {success_count}")
        logger.info(f"Capturas com falha: {total_count - success_count}")
        
        if total_count > success_count:
            logger.info("\nPortfolios com erro:")
            for portfolio_id, result in results.items():
                if not result.get('success'):
                    logger.info(f"  - {portfolio_id}: {result.get('error', 'Erro desconhecido')}")
        
        logger.info("=" * 60)
    
    def run_scheduled(self):
        """Executa capturas de acordo com agendamento"""
        logger.info("Iniciando modo agendado")
        
        # Captura inicial se configurado
        if self.config.get('capture_schedule', {}).get('on_startup', True):
            self.capture_all()
        
        # Configurar agendamento
        daily_time = self.config.get('capture_schedule', {}).get('daily_at', '09:00')
        schedule.every().day.at(daily_time).do(self.capture_all)
        
        logger.info(f"Agendamento configurado para: {daily_time}")
        logger.info("Pressione Ctrl+C para interromper")
        
        # Loop de execução
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Verificar a cada minuto
        except KeyboardInterrupt:
            logger.info("\nExecução interrompida pelo usuário")
    
    def generate_reports(self):
        """Gera relatórios para todos os portfolios"""
        logger.info("Gerando relatórios...")
        
        portfolios = self.storage.get_all_portfolios()
        
        for _, portfolio in portfolios.iterrows():
            try:
                report_path = self.storage.generate_portfolio_report(portfolio['id'])
                logger.info(f"✅ Relatório gerado: {report_path}")
            except Exception as e:
                logger.error(f"❌ Erro ao gerar relatório para {portfolio['id']}: {str(e)}")


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description='Captura dados de múltiplas carteiras de investimento'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Arquivo de configuração JSON'
    )
    
    parser.add_argument(
        '--once',
        action='store_true',
        help='Executar apenas uma vez (sem agendamento)'
    )
    
    parser.add_argument(
        '--reports',
        action='store_true',
        help='Gerar relatórios dos portfolios'
    )
    
    parser.add_argument(
        '--portfolio',
        type=str,
        help='Capturar apenas um portfolio específico'
    )
    
    args = parser.parse_args()
    
    # Criar runner
    runner = PortfolioCaptureRunner(args.config)
    
    # Executar ação solicitada
    if args.reports:
        runner.generate_reports()
    elif args.portfolio:
        # Capturar apenas um portfolio
        if args.portfolio in runner.capture_config.portfolios:
            temp_config = runner.capture_config.portfolios.copy()
            runner.capture_config.portfolios = {
                args.portfolio: temp_config[args.portfolio]
            }
            runner.capture_all()
        else:
            logger.error(f"Portfolio não encontrado: {args.portfolio}")
    elif args.once:
        runner.capture_all()
    else:
        runner.run_scheduled()


if __name__ == '__main__':
    main()