"""
Módulo de integração com website
Prepara e disponibiliza dados capturados para visualização web
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

from data_storage import PortfolioDataStorage

logger = logging.getLogger(__name__)


class WebsiteDataProcessor:
    """Processador de dados para integração com website"""
    
    def __init__(self, storage: PortfolioDataStorage, output_path: Optional[Path] = None):
        """
        Inicializa o processador
        
        Args:
            storage: Instância do storage
            output_path: Caminho para salvar dados processados
        """
        self.storage = storage
        self.output_path = output_path or Path.home() / 'Documents' / 'GitHub' / 'avalon_fia' / 'website_data'
        self.output_path.mkdir(parents=True, exist_ok=True)
    
    def process_portfolio_for_web(self, portfolio_id: str) -> Dict:
        """
        Processa dados de um portfolio para exibição web
        
        Args:
            portfolio_id: ID do portfolio
            
        Returns:
            Dict com dados formatados para web
        """
        # Obter última captura
        latest_capture = self.storage.get_latest_capture(portfolio_id)
        
        if not latest_capture or not latest_capture.get('success'):
            return {
                'portfolio_id': portfolio_id,
                'status': 'no_data',
                'message': 'Nenhum dado disponível'
            }
        
        # Obter informações do portfolio
        portfolios_df = self.storage.get_all_portfolios()
        portfolio_info = portfolios_df[portfolios_df['id'] == portfolio_id].iloc[0].to_dict()
        
        # Obter histórico
        history = self.storage.get_portfolio_history(portfolio_id, days=30)
        
        # Processar dados para web
        web_data = {
            'portfolio_id': portfolio_id,
            'portfolio_name': portfolio_info.get('name', 'Unknown'),
            'portfolio_type': portfolio_info.get('type', 'Unknown'),
            'last_update': latest_capture.get('capture_date', datetime.now()).isoformat(),
            'status': 'success',
            'summary': self._generate_summary(latest_capture),
            'positions': self._format_positions(latest_capture),
            'charts': self._generate_chart_data(latest_capture, history),
            'history': self._format_history(history),
            'metrics': self._calculate_metrics(latest_capture, history)
        }
        
        return web_data
    
    def _generate_summary(self, capture_data: Dict) -> Dict:
        """Gera resumo do portfolio"""
        summary = {
            'total_value': 0,
            'total_positions': 0,
            'asset_types': {},
            'top_positions': []
        }
        
        # Processar dados conforme tipo
        if 'data' in capture_data:
            data = capture_data['data']
            
            # Se for tuple do process_account_data
            if isinstance(data, tuple) and len(data) >= 13:
                total_positions = data[11]  # Índice 11 é o total_positions
                total_equity = data[12]     # Índice 12 é o total_equity
                
                summary['total_value'] = float(total_equity)
                summary['total_positions'] = float(total_positions)
                
                # Contar ativos por tipo
                dataframes = data[:11]
                for i, df in enumerate(dataframes):
                    if isinstance(df, pd.DataFrame) and not df.empty:
                        asset_type = self._get_asset_type_name(i)
                        summary['asset_types'][asset_type] = len(df)
        
        return summary
    
    def _format_positions(self, capture_data: Dict) -> List[Dict]:
        """Formata posições para exibição"""
        positions = []
        
        if 'data' in capture_data:
            data = capture_data['data']
            
            # Se for tuple do process_account_data
            if isinstance(data, tuple) and len(data) >= 11:
                dataframes = data[:11]
                
                for i, df in enumerate(dataframes):
                    if isinstance(df, pd.DataFrame) and not df.empty:
                        asset_type = self._get_asset_type_name(i)
                        
                        for _, row in df.iterrows():
                            position = {
                                'asset_type': asset_type,
                                'name': row.get('FundName', row.get('Issuer', row.get('Ticker', 'Unknown'))),
                                'ticker': row.get('Ticker', ''),
                                'value': float(row.get('GrossAssetValue', row.get('GrossValue', row.get('Value', 0)))),
                                'percentage': 0  # Calcular depois
                            }
                            positions.append(position)
        
        # Calcular percentuais
        total_value = sum(p['value'] for p in positions)
        if total_value > 0:
            for position in positions:
                position['percentage'] = (position['value'] / total_value) * 100
        
        # Ordenar por valor
        positions.sort(key=lambda x: x['value'], reverse=True)
        
        return positions
    
    def _generate_chart_data(self, capture_data: Dict, history: pd.DataFrame) -> Dict:
        """Gera dados para gráficos"""
        charts = {
            'allocation_pie': self._generate_allocation_pie(capture_data),
            'value_timeline': self._generate_value_timeline(history),
            'asset_types_bar': self._generate_asset_types_bar(capture_data)
        }
        
        return charts
    
    def _generate_allocation_pie(self, capture_data: Dict) -> Dict:
        """Gera dados para gráfico de pizza de alocação"""
        positions = self._format_positions(capture_data)
        
        # Agrupar posições pequenas
        threshold = 2.0  # 2%
        main_positions = []
        others_value = 0
        
        for pos in positions:
            if pos['percentage'] >= threshold:
                main_positions.append({
                    'name': pos['name'],
                    'value': pos['value'],
                    'percentage': pos['percentage']
                })
            else:
                others_value += pos['value']
        
        if others_value > 0:
            total_value = sum(p['value'] for p in positions)
            main_positions.append({
                'name': 'Outros',
                'value': others_value,
                'percentage': (others_value / total_value) * 100 if total_value > 0 else 0
            })
        
        return {
            'type': 'pie',
            'data': main_positions,
            'title': 'Alocação do Portfolio'
        }
    
    def _generate_value_timeline(self, history: pd.DataFrame) -> Dict:
        """Gera dados para gráfico de linha temporal"""
        if history.empty:
            return {
                'type': 'line',
                'data': [],
                'title': 'Evolução do Patrimônio'
            }
        
        # Filtrar apenas capturas bem-sucedidas
        history_success = history[history['status'] == 'success'].copy()
        
        data_points = []
        for _, row in history_success.iterrows():
            data_points.append({
                'date': row['capture_date'],
                'value': float(row['total_value']) if pd.notna(row['total_value']) else 0
            })
        
        return {
            'type': 'line',
            'data': data_points,
            'title': 'Evolução do Patrimônio'
        }
    
    def _generate_asset_types_bar(self, capture_data: Dict) -> Dict:
        """Gera dados para gráfico de barras por tipo de ativo"""
        asset_summary = {}
        
        if 'data' in capture_data:
            data = capture_data['data']
            
            if isinstance(data, tuple) and len(data) >= 11:
                dataframes = data[:11]
                
                for i, df in enumerate(dataframes):
                    if isinstance(df, pd.DataFrame) and not df.empty:
                        asset_type = self._get_asset_type_name(i)
                        
                        # Somar valores
                        total = 0
                        for _, row in df.iterrows():
                            value = row.get('GrossAssetValue', row.get('GrossValue', row.get('Value', 0)))
                            total += float(value) if pd.notna(value) else 0
                        
                        if total > 0:
                            asset_summary[asset_type] = total
        
        # Converter para formato de gráfico
        data_points = [
            {'category': k, 'value': v}
            for k, v in sorted(asset_summary.items(), key=lambda x: x[1], reverse=True)
        ]
        
        return {
            'type': 'bar',
            'data': data_points,
            'title': 'Distribuição por Tipo de Ativo'
        }
    
    def _format_history(self, history: pd.DataFrame) -> List[Dict]:
        """Formata histórico para exibição"""
        history_list = []
        
        for _, row in history.iterrows():
            history_list.append({
                'date': row['capture_date'],
                'value': float(row['total_value']) if pd.notna(row['total_value']) else 0,
                'status': row['status']
            })
        
        return history_list
    
    def _calculate_metrics(self, capture_data: Dict, history: pd.DataFrame) -> Dict:
        """Calcula métricas do portfolio"""
        metrics = {
            'total_return': 0,
            'daily_return': 0,
            'monthly_return': 0,
            'volatility': 0,
            'sharpe_ratio': 0,
            'max_drawdown': 0
        }
        
        # Calcular retornos se houver histórico suficiente
        if not history.empty and len(history) > 1:
            history_success = history[history['status'] == 'success'].copy()
            
            if len(history_success) > 1:
                # Ordenar por data
                history_success = history_success.sort_values('capture_date')
                values = history_success['total_value'].values
                
                # Retorno total
                if values[0] > 0:
                    metrics['total_return'] = ((values[-1] - values[0]) / values[0]) * 100
                
                # Retorno diário (último dia)
                if len(values) >= 2 and values[-2] > 0:
                    metrics['daily_return'] = ((values[-1] - values[-2]) / values[-2]) * 100
                
                # Volatilidade (desvio padrão dos retornos)
                if len(values) > 2:
                    returns = pd.Series(values).pct_change().dropna()
                    metrics['volatility'] = returns.std() * 100
        
        return metrics
    
    def _get_asset_type_name(self, index: int) -> str:
        """Mapeia índice para nome do tipo de ativo"""
        mapping = {
            0: 'Fundos de Investimento',
            1: 'Renda Fixa',
            2: 'COE',
            3: 'Ações',
            4: 'Derivativos',
            5: 'Commodities',
            6: 'Criptomoedas',
            7: 'Caixa',
            8: 'Previdência',
            9: 'Créditos',
            10: 'Valores em Trânsito'
        }
        return mapping.get(index, 'Outros')
    
    def export_all_portfolios_for_web(self) -> Dict:
        """
        Exporta dados de todos os portfolios para o website
        
        Returns:
            Dict com status da exportação
        """
        logger.info("Exportando dados para website...")
        
        # Obter todos os portfolios
        portfolios = self.storage.get_all_portfolios()
        
        export_results = {
            'timestamp': datetime.now().isoformat(),
            'portfolios': {},
            'summary': {
                'total_portfolios': len(portfolios),
                'successful_exports': 0,
                'failed_exports': 0
            }
        }
        
        # Processar cada portfolio
        for _, portfolio in portfolios.iterrows():
            portfolio_id = portfolio['id']
            
            try:
                # Processar dados
                web_data = self.process_portfolio_for_web(portfolio_id)
                
                # Salvar arquivo individual
                portfolio_file = self.output_path / f'{portfolio_id}_data.json'
                with open(portfolio_file, 'w', encoding='utf-8') as f:
                    json.dump(web_data, f, ensure_ascii=False, indent=2)
                
                export_results['portfolios'][portfolio_id] = {
                    'status': 'success',
                    'file': str(portfolio_file)
                }
                export_results['summary']['successful_exports'] += 1
                
                logger.info(f"✅ Exportado: {portfolio_id}")
                
            except Exception as e:
                export_results['portfolios'][portfolio_id] = {
                    'status': 'error',
                    'error': str(e)
                }
                export_results['summary']['failed_exports'] += 1
                
                logger.error(f"❌ Erro ao exportar {portfolio_id}: {str(e)}")
        
        # Salvar índice geral
        index_file = self.output_path / 'index.json'
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(export_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Exportação concluída: {export_results['summary']}")
        
        return export_results
    
    def generate_dashboard_data(self) -> Dict:
        """
        Gera dados consolidados para dashboard geral
        
        Returns:
            Dict com dados do dashboard
        """
        portfolios = self.storage.get_all_portfolios()
        
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'overview': {
                'total_portfolios': len(portfolios),
                'total_value': 0,
                'active_portfolios': 0
            },
            'portfolios': [],
            'aggregated_charts': {}
        }
        
        total_value = 0
        all_positions = []
        
        for _, portfolio in portfolios.iterrows():
            portfolio_id = portfolio['id']
            
            # Obter dados processados
            web_data = self.process_portfolio_for_web(portfolio_id)
            
            if web_data.get('status') == 'success':
                portfolio_summary = {
                    'id': portfolio_id,
                    'name': web_data['portfolio_name'],
                    'type': web_data['portfolio_type'],
                    'value': web_data['summary']['total_value'],
                    'last_update': web_data['last_update'],
                    'metrics': web_data['metrics']
                }
                
                dashboard_data['portfolios'].append(portfolio_summary)
                total_value += web_data['summary']['total_value']
                all_positions.extend(web_data['positions'])
                dashboard_data['overview']['active_portfolios'] += 1
        
        dashboard_data['overview']['total_value'] = total_value
        
        # Gerar gráficos agregados
        dashboard_data['aggregated_charts'] = self._generate_aggregated_charts(all_positions, total_value)
        
        # Salvar dashboard
        dashboard_file = self.output_path / 'dashboard.json'
        with open(dashboard_file, 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, ensure_ascii=False, indent=2)
        
        return dashboard_data
    
    def _generate_aggregated_charts(self, all_positions: List[Dict], total_value: float) -> Dict:
        """Gera gráficos agregados de todos os portfolios"""
        # Agrupar por tipo de ativo
        asset_types_summary = {}
        
        for position in all_positions:
            asset_type = position['asset_type']
            if asset_type not in asset_types_summary:
                asset_types_summary[asset_type] = 0
            asset_types_summary[asset_type] += position['value']
        
        return {
            'total_allocation': {
                'type': 'pie',
                'data': [
                    {
                        'name': asset_type,
                        'value': value,
                        'percentage': (value / total_value * 100) if total_value > 0 else 0
                    }
                    for asset_type, value in asset_types_summary.items()
                ],
                'title': 'Alocação Total Consolidada'
            }
        }


def main():
    """Função de teste"""
    storage = PortfolioDataStorage()
    processor = WebsiteDataProcessor(storage)
    
    # Exportar todos os portfolios
    results = processor.export_all_portfolios_for_web()
    print(f"Exportação concluída: {results['summary']}")
    
    # Gerar dashboard
    dashboard = processor.generate_dashboard_data()
    print(f"Dashboard gerado com {len(dashboard['portfolios'])} portfolios")


if __name__ == '__main__':
    main()