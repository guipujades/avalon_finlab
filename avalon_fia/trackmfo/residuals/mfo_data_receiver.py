"""
Receptor de dados MFO - Compatível com o sistema original
Recebe dados via POST e processa usando a mesma lógica do app.py original
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import pandas as pd

from api_btg_mfo_utils import process_account_data, get_total_amount
from data_storage import PortfolioDataStorage

logger = logging.getLogger(__name__)


class MFODataReceiver:
    """
    Receptor e processador de dados MFO
    Mantém compatibilidade com o formato original do app.py
    """
    
    def __init__(self, storage: Optional[PortfolioDataStorage] = None):
        """
        Inicializa o receptor
        
        Args:
            storage: Instância do storage (opcional)
        """
        self.storage = storage or PortfolioDataStorage()
        self.current_data = None
        
    def receive_data(self, data: Dict) -> Dict:
        """
        Recebe e processa dados no formato original do MFO
        
        Args:
            data: Dados recebidos via POST no formato:
                {
                    'clients': {
                        'account_id': account_data_json_string,
                        ...
                    },
                    'data_btg': dataframe_as_dict
                }
                
        Returns:
            Dict com resultado do processamento
        """
        try:
            # Validar estrutura
            if 'clients' not in data or 'data_btg' not in data:
                return {
                    'status': 'error',
                    'message': 'Formato inválido: esperado clients e data_btg'
                }
            
            # Armazenar dados recebidos
            self.current_data = data
            
            # Processar clientes
            processed_clients = self._process_all_clients(data['clients'], data['data_btg'])
            
            # Salvar no storage
            for client_id, client_data in processed_clients.items():
                if client_data['success']:
                    # Criar entrada de portfolio se não existir
                    portfolio_info = {
                        'name': client_data.get('client_name', f'Cliente {client_id}'),
                        'type': 'mfo_client',
                        'account_id': client_id
                    }
                    self.storage.save_portfolio_info(f'mfo_{client_id}', portfolio_info)
                    
                    # Salvar captura
                    capture_data = {
                        'success': True,
                        'capture_date': datetime.now(),
                        'data': client_data['processed_data'],
                        'raw_data': client_data['raw_data'],
                        'total_value': client_data['total_equity']
                    }
                    self.storage.save_capture(f'mfo_{client_id}', capture_data)
            
            return {
                'status': 'success',
                'message': 'Dados processados com sucesso',
                'clients_processed': len(processed_clients),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar dados: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _process_all_clients(self, clients: Dict, data_btg: Dict) -> Dict:
        """
        Processa todos os clientes seguindo a lógica do app.py original
        
        Args:
            clients: Dict com dados dos clientes
            data_btg: DataFrame com informações BTG
            
        Returns:
            Dict com dados processados de cada cliente
        """
        # Converter data_btg para DataFrame
        df_btg = pd.DataFrame.from_dict(data_btg)
        
        processed_clients = {}
        
        for client_id, client_data_json in clients.items():
            try:
                # Verificar se cliente está no data_btg
                if pd.to_numeric(client_id) not in list(df_btg.Conta):
                    logger.warning(f"Cliente {client_id} não encontrado em data_btg")
                    continue
                
                # Obter ID interno
                internal_id = list(df_btg[df_btg.Conta == pd.to_numeric(client_id)]['Id'])[0]
                
                # Processar dados do cliente
                processed_data = process_account_data(client_data_json)
                
                # Desempacotar os resultados
                (funds_df, fixed_income_df, coe_df, equities_df, derivatives_df,
                 commodities_df, crypto_df, cash_df, pension_df, credits_df, 
                 pending_settlements_df, total_positions, total_equity) = processed_data
                
                # Obter valor total
                total_amount = get_total_amount(client_data_json)
                
                # Obter taxa de gestão
                tx_gestao = list(df_btg[df_btg.Conta == pd.to_numeric(client_id)]['Taxas'])[0]
                
                # Calcular cobranças (seguindo lógica original)
                cobranca_info = self._calculate_fees(
                    total_amount, tx_gestao, funds_df, total_positions
                )
                
                # Montar resultado
                processed_clients[internal_id] = {
                    'success': True,
                    'client_id': client_id,
                    'internal_id': internal_id,
                    'client_name': f'Cliente {internal_id}',
                    'raw_data': client_data_json,
                    'processed_data': processed_data,
                    'dataframes': {
                        'fundos': funds_df,
                        'renda_fixa': fixed_income_df,
                        'coe': coe_df,
                        'acoes': equities_df,
                        'derivativos': derivatives_df,
                        'commodities': commodities_df,
                        'crypto': crypto_df,
                        'cash': cash_df,
                        'previdencia': pension_df,
                        'creditos': credits_df,
                        'valores_transito': pending_settlements_df
                    },
                    'total_positions': total_positions,
                    'total_equity': total_equity,
                    'total_amount': total_amount,
                    'tx_gestao': tx_gestao,
                    'cobranca_info': cobranca_info
                }
                
            except Exception as e:
                logger.error(f"Erro ao processar cliente {client_id}: {str(e)}")
                processed_clients[client_id] = {
                    'success': False,
                    'error': str(e)
                }
        
        return processed_clients
    
    def _calculate_fees(self, total_amount: float, tx_gestao: float, 
                       funds_df: pd.DataFrame, total_positions: float) -> Dict:
        """
        Calcula taxas seguindo a lógica original do app.py
        
        Args:
            total_amount: Valor total da conta
            tx_gestao: Taxa de gestão
            funds_df: DataFrame de fundos
            total_positions: Total de posições
            
        Returns:
            Dict com informações de cobrança
        """
        avalon_fia_tax = 0.02  # 2% ao ano
        
        if tx_gestao == 0.0:
            return {
                'limite_mes': 0.0,
                'tx_mes': 0.0,
                'cobranca_avalon_fia': 0.0,
                'tem_avalon_fia': False
            }
        
        # Limite mensal
        limite_mes = (total_amount * tx_gestao) / 12
        
        # Verificar investimento no Avalon FIA
        avalon_fia = funds_df[funds_df['FundName'] == 'Avalon FIA RL']
        cobranca_avalon_fia = 0.0
        tem_avalon_fia = False
        
        if not avalon_fia.empty:
            tem_avalon_fia = True
            investimento_avalon_fia = avalon_fia['GrossAssetValue'].sum()
            cobranca_avalon_fia = investimento_avalon_fia * (avalon_fia_tax / 12)
            tx_mes = limite_mes - cobranca_avalon_fia
        else:
            tx_mes = limite_mes
        
        # Ajustar se negativo
        if tx_mes < 0:
            tx_mes = 0
        
        return {
            'limite_mes': limite_mes,
            'tx_mes': tx_mes,
            'cobranca_avalon_fia': cobranca_avalon_fia,
            'tem_avalon_fia': tem_avalon_fia,
            'investimento_avalon_fia': avalon_fia['GrossAssetValue'].sum() if tem_avalon_fia else 0
        }
    
    def get_processed_summary(self) -> Dict:
        """
        Retorna resumo dos dados processados
        
        Returns:
            Dict com resumo
        """
        if not self.current_data:
            return {'status': 'no_data'}
        
        clients = self.current_data['clients']
        processed = self._process_all_clients(
            self.current_data['clients'], 
            self.current_data['data_btg']
        )
        
        total_equity = sum(
            c['total_equity'] for c in processed.values() 
            if c.get('success', False)
        )
        
        total_fees = sum(
            c['cobranca_info']['tx_mes'] for c in processed.values() 
            if c.get('success', False)
        )
        
        return {
            'total_clients': len(clients),
            'processed_clients': len([c for c in processed.values() if c.get('success')]),
            'failed_clients': len([c for c in processed.values() if not c.get('success')]),
            'total_equity': total_equity,
            'total_monthly_fees': total_fees,
            'last_update': datetime.now().isoformat()
        }
    
    def export_for_dashboard(self, output_path: Optional[Path] = None) -> Path:
        """
        Exporta dados processados para o dashboard
        
        Args:
            output_path: Caminho de saída (opcional)
            
        Returns:
            Path do arquivo exportado
        """
        if not output_path:
            output_path = Path.home() / 'Documents' / 'GitHub' / 'avalon_fia' / 'website_data'
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        summary = self.get_processed_summary()
        
        # Salvar resumo
        summary_file = output_path / 'mfo_summary.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Dashboard data exported to: {summary_file}")
        
        return summary_file


def main():
    """Teste do receptor"""
    receiver = MFODataReceiver()
    
    # Exemplo de dados de teste
    test_data = {
        'clients': {
            '12345': '{"InvestmentFund": [], "FixedIncome": [], "Cash": [{"CurrentAccount": {"Value": 1000}}]}',
            '67890': '{"InvestmentFund": [], "FixedIncome": [], "Cash": [{"CurrentAccount": {"Value": 2000}}]}'
        },
        'data_btg': {
            'Conta': [12345, 67890],
            'Id': ['CLI001', 'CLI002'],
            'Taxas': [0.02, 0.015]
        }
    }
    
    result = receiver.receive_data(test_data)
    print(f"Resultado: {result}")
    
    summary = receiver.get_processed_summary()
    print(f"Resumo: {summary}")


if __name__ == '__main__':
    main()