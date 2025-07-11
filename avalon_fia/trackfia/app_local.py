#!/usr/bin/env python3
"""
Aplicação local para visualização dos dados do fundo AVALON FIA
Usa a nova API BTG de fundos e gera HTML local
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from scipy.stats import norm
import pickle as pkl
import json
from flask import Flask, render_template, jsonify, request

# Adicionar o diretório ao path
sys.path.append(str(Path(__file__).parent))

# Importar módulos customizados
from api_btg_funds import fund_data_corrected
from mt5_connect import *
from manager import *
from options_data import id_options

# Configurar Flask
app = Flask(__name__)

# Configurar logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AvalonFIATracker:
    """Classe principal para tracking do fundo Avalon FIA"""
    
    def __init__(self):
        self.initialize_mt5()
        self.current_date = datetime.now().strftime('%Y-%m-%d')
        self.pickle_dir = Path.home() / 'Documents' / 'GitHub' / 'database' / 'dados_api'
        self.pickle_dir.mkdir(parents=True, exist_ok=True)
        
    def initialize_mt5(self):
        """Inicializa conexão com MetaTrader 5"""
        try:
            mt5_path = Path('C:/', 'Program Files', 'Rico - MetaTrader 5', 'terminal64.exe')
            initialize(user_path=str(mt5_path), server='GenialInvestimentos-PRD', login=156691, key='Avca@1985')
            logger.info("MT5 inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar MT5: {e}")
            
    def get_fund_data(self):
        """Obtém dados do fundo via API BTG"""
        # Caminhos dos arquivos pickle
        df_xml_path = self.pickle_dir / f'df_xml_{self.current_date}.pkl'
        data_xml_path = self.pickle_dir / f'data_xml_{self.current_date}.pkl'
        header_path = self.pickle_dir / f'header_{self.current_date}.pkl'
        
        # Verifica cache
        if all(p.exists() for p in [df_xml_path, data_xml_path, header_path]):
            logger.info('Carregando dados do cache...')
            with open(df_xml_path, 'rb') as f:
                df_xml = pkl.load(f)
            with open(data_xml_path, 'rb') as f:
                data_xml = pkl.load(f)
            with open(header_path, 'rb') as f:
                header = pkl.load(f)
        else:
            logger.info('Obtendo dados da API BTG...')
            df_xml, data_xml, header = fund_data_corrected('xml')
            
            # Salvar cache
            with open(df_xml_path, 'wb') as f:
                pkl.dump(df_xml, f)
            with open(data_xml_path, 'wb') as f:
                pkl.dump(data_xml, f)
            with open(header_path, 'wb') as f:
                pkl.dump(header, f)
                
        return df_xml, data_xml, header
        
    def get_real_time_prices(self, portfolio):
        """Obtém preços em tempo real via MT5"""
        prices_full = {}
        prices = {}
        
        for ticker in portfolio.keys():
            if portfolio[ticker]['quantity'] != 0:
                try:
                    prepare_symbol(ticker)
                    
                    # Tratamento especial para ISAE4
                    if ticker == 'ISAE4':
                        prices[ticker] = 22.95
                        novo_df = pd.DataFrame({
                            'Abertura': [22.95],
                            'Maxima': [22.95],
                            'Minima': [22.95],
                            'Fechamento': [22.95],
                            'Volume_Financeiro': [1.045980e+09]
                        }, index=[pd.to_datetime('2024-12-20')])
                        prices_full[ticker] = novo_df
                        continue
                        
                    df_ = get_prices_mt5(symbol=ticker, n=100, timeframe=mt5.TIMEFRAME_D1)
                    if df_ is not None:
                        df_['Volume_Financeiro'] = ((df_['Máxima'] + df_['Mínima']) / 2) * df_['Volume']
                        df_ = df_[['Abertura', 'Máxima', 'Mínima', 'Fechamento', 'Volume_Financeiro']]
                        df_.columns = ['Abertura', 'Maxima', 'Minima', 'Fechamento', 'Volume_Financeiro']
                        df_.index.name = 'Data'
                        prices_full[ticker] = df_
                        last_price = df_.iloc[-1]['Fechamento']
                        prices[ticker] = last_price
                except Exception as e:
                    logger.error(f"Erro ao obter preço de {ticker}: {e}")
                    
        return prices, prices_full
        
    def calculate_portfolio_metrics(self, portfolio, prices):
        """Calcula métricas do portfolio"""
        pnl = {}
        
        for ticker, data in portfolio.items():
            if data['quantity'] != 0:
                current_price = prices.get(ticker, 0)
                average_price = data['average_price']
                current_value = current_price * data['quantity']
                initial_value = average_price * data['quantity']
                profit_loss = current_value - initial_value
                
                pnl[ticker] = {
                    'current_price': current_price,
                    'quantity': data['quantity'],
                    'average_price': average_price,
                    'current_value': current_value,
                    'profit_loss': profit_loss,
                    'percentage_change': (profit_loss / abs(initial_value)) if initial_value != 0 else 0
                }
                
        return pnl
        
    def calculate_var(self, prices_df, weights, time_ahead):
        """Calcula Value at Risk"""
        returns = np.log(1 + prices_df.pct_change())
        cov_matrix = returns.cov() * 252
        portfolio_std_dev = np.sqrt(weights.T @ cov_matrix @ weights)
        
        confidence_levels = [0.90, 0.95, 0.99]
        VaRs = []
        for cl in confidence_levels:
            VaR = portfolio_std_dev * norm.ppf(cl) * np.sqrt(time_ahead / 252)
            VaRs.append(round(VaR * 100, 4))
            
        return VaRs
        
    def process_portfolio_data(self):
        """Processa todos os dados do portfolio"""
        # Obter dados do fundo
        df_xml, data_xml, header = self.get_fund_data()
        
        # Extrair informações do header
        pl_fundo = header['patliq']
        data_dados = pd.to_datetime(header['dtposicao']).strftime('%d/%m/%Y')
        cota_fia = header['valorcota']
        a_receber = header['valorreceber']
        a_pagar = header['valorpagar']
        
        # Obter portfolio local
        portfolio, df_original_table = run_manager_xml()
        
        # Obter preços em tempo real
        last_prices, prices_full = self.get_real_time_prices(portfolio)
        
        # Calcular P&L
        pnl = self.calculate_portfolio_metrics(portfolio, last_prices)
        
        # Criar DataFrame base
        df = pd.DataFrame.from_dict(pnl, orient='index')
        df['pcts_port'] = (df['current_value'] / df['current_value'].sum()) * 100
        df['percentage_change'] = df['percentage_change'] * 100
        df['impact'] = df['percentage_change'] * df['pcts_port'] / 100
        
        # Separar ações de opções
        df_stocks = df[df.index.str.len() < 7]
        df_options = df[df.index.str.len() >= 7]
        
        # Calcular métricas para ações
        if len(df_stocks) > 0:
            weights = df_stocks['pcts_port'].values / 100
            
            # Criar DataFrame de preços
            df_var = pd.DataFrame({k: v['Fechamento'] for k, v in prices_full.items() 
                                 if k in list(df_stocks.index)})
            df_var.index = pd.to_datetime(df_var.index)
            
            # VaR do portfolio
            portfolio_var_1_week = self.calculate_var(df_var, weights, 5)
            portfolio_var_1_month = self.calculate_var(df_var, weights, 21)
            
            # Variações
            daily_change = self.calculate_daily_change(df_var)
            weekly_change = self.calculate_weekly_change(df_var)
            monthly_change = self.calculate_monthly_change(df_var)
            
            # Portfolio changes
            portfolio_change = self.calculate_portfolio_change_pm(df)
            portfolio_change_stocks = self.calculate_portfolio_change_pm(df_stocks)
            portfolio_daily_change = self.calculate_portfolio_change(df_var, weights, 1)
            portfolio_weekly_change = self.calculate_weekly_portfolio_change(df_var, weights)
        else:
            portfolio_var_1_week = [0, 0, 0]
            portfolio_var_1_month = [0, 0, 0]
            portfolio_change = 0
            portfolio_change_stocks = 0
            portfolio_daily_change = 0
            portfolio_weekly_change = 0
            
        # Calcular enquadramento
        enquadramento = df['current_value'].sum() / pl_fundo
        
        # Processar opções
        limits_der = 0
        df_opts_table_dict = {}
        impact_by_date = {}
        
        if len(df_options) > 0:
            limits_der = abs(df_options['current_value']).sum() / pl_fundo
            # TODO: Processar opções conforme necessário
            
        # Preparar dados finais
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        portfolio_data = {
            'current_time': current_time,
            'data': data_dados,
            'current_pl': pl_fundo,
            'cota': cota_fia,
            'receber': a_receber,
            'pagar': a_pagar,
            'enquadramento': enquadramento,
            'limits_der': limits_der,
            'portfolio_change': portfolio_change,
            'portfolio_change_stocks': portfolio_change_stocks,
            'portfolio_daily_change': portfolio_daily_change,
            'portfolio_weekly_change': portfolio_weekly_change,
            'portfolio_var_1_week': portfolio_var_1_week,
            'portfolio_var_1_month': portfolio_var_1_month,
            'df_stocks': df_stocks,
            'df_options': df_options,
            'portfolio': portfolio,
            'df': df
        }
        
        return portfolio_data
        
    # Métodos auxiliares de cálculo
    def calculate_daily_change(self, prices_df):
        """Calcula variação diária"""
        if len(prices_df) < 2:
            return pd.Series()
        today = prices_df.iloc[-1]
        yesterday = prices_df.iloc[-2]
        change = ((today - yesterday) / yesterday) * 100
        return change
        
    def calculate_weekly_change(self, prices_df):
        """Calcula variação semanal"""
        if len(prices_df) < 5:
            return pd.Series()
        week_ago = prices_df.iloc[-5]
        today = prices_df.iloc[-1]
        change = ((today - week_ago) / week_ago) * 100
        return change
        
    def calculate_monthly_change(self, prices_df):
        """Calcula variação mensal"""
        if len(prices_df) < 21:
            return pd.Series()
        month_ago = prices_df.iloc[-21]
        today = prices_df.iloc[-1]
        change = ((today - month_ago) / month_ago) * 100
        return change
        
    def calculate_portfolio_change_pm(self, df):
        """Calcula variação do portfolio baseado no preço médio"""
        if df.empty:
            return 0
        initial_value = (df['average_price'] * df['quantity']).sum()
        current_value = df['current_value'].sum()
        if initial_value == 0:
            return 0
        portfolio_change = (current_value / initial_value) - 1
        return portfolio_change * 100
        
    def calculate_portfolio_change(self, prices_df, weights, days):
        """Calcula variação do portfolio para N dias"""
        if len(prices_df) < days + 1:
            return 0
        returns = np.log(prices_df / prices_df.shift(1))
        weighted_returns = returns * weights
        portfolio_change = weighted_returns.sum(axis=1).iloc[-days:].sum() * 100
        return portfolio_change
        
    def calculate_weekly_portfolio_change(self, prices_df, weights):
        """Calcula variação semanal do portfolio"""
        return self.calculate_portfolio_change(prices_df, weights, 5)


# Instância global do tracker
tracker = AvalonFIATracker()


@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')


@app.route('/api/portfolio_data')
def get_portfolio_data():
    """API endpoint para obter dados do portfolio"""
    try:
        portfolio_data = tracker.process_portfolio_data()
        
        # Converter DataFrames para dicionários
        if isinstance(portfolio_data.get('df_stocks'), pd.DataFrame):
            portfolio_data['df_stocks'] = portfolio_data['df_stocks'].to_dict('index')
        if isinstance(portfolio_data.get('df_options'), pd.DataFrame):
            portfolio_data['df_options'] = portfolio_data['df_options'].to_dict('index')
        if isinstance(portfolio_data.get('df'), pd.DataFrame):
            portfolio_data['df'] = portfolio_data['df'].to_dict('index')
            
        return jsonify(portfolio_data)
    except Exception as e:
        logger.error(f"Erro ao processar dados: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/refresh')
def refresh_data():
    """Força atualização dos dados"""
    try:
        # Limpar cache
        for file in tracker.pickle_dir.glob(f'*_{tracker.current_date}.pkl'):
            file.unlink()
            
        # Reprocessar
        portfolio_data = tracker.process_portfolio_data()
        return jsonify({'status': 'success', 'message': 'Dados atualizados'})
    except Exception as e:
        logger.error(f"Erro ao atualizar: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("🚀 Iniciando Avalon FIA Tracker Local")
    print("📊 Acesse http://localhost:5000 para visualizar os dados")
    app.run(debug=True, host='localhost', port=5000)