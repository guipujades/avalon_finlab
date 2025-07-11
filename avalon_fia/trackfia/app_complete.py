#!/usr/bin/env python3
"""
Aplicação completa para visualização dos dados do fundo AVALON FIA
Versão elegante com todos os cálculos e métricas
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import pickle as pkl
import json
from flask import Flask, render_template, jsonify, request
import logging

# Adicionar o diretório ao path
sys.path.append(str(Path(__file__).parent))

# Importar módulos customizados
from api_btg_funds import fund_data_corrected
try:
    from mt5_connect import *
except ImportError:
    logger.warning("MT5 não disponível")
    mt5 = None
try:
    from manager import *
except ImportError:
    logger.warning("Manager padrão não disponível")
from manager_simple import run_manager_xml_simple
from portfolio_processor_fixed import process_portfolio_from_api_fixed
try:
    from options_data import id_options
except ImportError:
    id_options = {}

# Configurar Flask
app = Flask(__name__)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AvalonFIAAnalytics:
    """Sistema completo de análise do fundo Avalon FIA"""
    
    def __init__(self):
        self.initialize_mt5()
        self.current_date = datetime.now().strftime('%Y-%m-%d')
        self.pickle_dir = Path.home() / 'Documents' / 'GitHub' / 'database' / 'dados_api'
        self.pickle_dir.mkdir(parents=True, exist_ok=True)
        
    def initialize_mt5(self):
        """Inicializa conexão com MetaTrader 5"""
        try:
            if mt5 is None:
                logger.warning("Módulo MT5 não disponível")
                return
            mt5_path = Path('C:/', 'Program Files', 'Rico - MetaTrader 5', 'terminal64.exe')
            initialize(user_path=str(mt5_path), server='GenialInvestimentos-PRD', login=156691, key='Avca@1985')
            logger.info("MT5 inicializado com sucesso")
        except Exception as e:
            logger.warning(f"MT5 não disponível: {e}")
            
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
        
    def get_market_data(self):
        """Obtém dados de mercado (IBOV, dólar, etc)"""
        try:
            market_data = {}
            
            # IBOVESPA
            if mt5 is not None:
                prepare_symbol('IBOV')
                ibov_df = get_prices_mt5(symbol='IBOV', n=30, timeframe=mt5.TIMEFRAME_D1)
            else:
                ibov_df = None
            if ibov_df is not None and len(ibov_df) > 1:
                market_data['ibov_points'] = ibov_df.iloc[-1]['Fechamento']
                market_data['ibov_change'] = ((ibov_df.iloc[-1]['Fechamento'] / ibov_df.iloc[-2]['Fechamento']) - 1) * 100
            else:
                market_data['ibov_points'] = 0
                market_data['ibov_change'] = 0
            
            # Dólar
            if mt5 is not None:
                prepare_symbol('USDBRL')
                usd_df = get_prices_mt5(symbol='USDBRL', n=30, timeframe=mt5.TIMEFRAME_D1)
            else:
                usd_df = None
            if usd_df is not None and len(usd_df) > 1:
                market_data['usd_brl'] = usd_df.iloc[-1]['Fechamento']
                market_data['usd_change'] = ((usd_df.iloc[-1]['Fechamento'] / usd_df.iloc[-2]['Fechamento']) - 1) * 100
            else:
                market_data['usd_brl'] = 0
                market_data['usd_change'] = 0
                
            return market_data
        except Exception as e:
            logger.error(f"Erro ao obter dados de mercado: {e}")
            return {
                'ibov_points': 0,
                'ibov_change': 0,
                'usd_brl': 0,
                'usd_change': 0
            }
            
    def get_real_time_prices(self, portfolio):
        """Obtém preços em tempo real via MT5"""
        prices_full = {}
        prices = {}
        
        for ticker in portfolio.keys():
            if portfolio[ticker]['quantity'] != 0:
                try:
                    prepare_symbol(ticker)
                    
                    # Tratamento especial para alguns ativos
                    if ticker == 'ISAE4':
                        prices[ticker] = 22.95
                        continue
                        
                    if mt5 is not None:
                        df_ = get_prices_mt5(symbol=ticker, n=100, timeframe=mt5.TIMEFRAME_D1)
                    else:
                        df_ = None
                    if df_ is not None and len(df_) > 0:
                        df_['Volume_Financeiro'] = ((df_['Máxima'] + df_['Mínima']) / 2) * df_['Volume']
                        df_ = df_[['Abertura', 'Máxima', 'Mínima', 'Fechamento', 'Volume_Financeiro']]
                        df_.columns = ['Abertura', 'Maxima', 'Minima', 'Fechamento', 'Volume_Financeiro']
                        prices_full[ticker] = df_
                        prices[ticker] = df_.iloc[-1]['Fechamento']
                    else:
                        # Usar preço médio do portfolio se não conseguir do MT5
                        prices[ticker] = portfolio[ticker].get('average_price', 0)
                except Exception as e:
                    logger.error(f"Erro ao obter preço de {ticker}: {e}")
                    prices[ticker] = portfolio[ticker].get('average_price', 0)
                    
        return prices, prices_full
        
    def calculate_portfolio_metrics(self, portfolio, prices):
        """Calcula métricas detalhadas do portfolio"""
        pnl = {}
        
        for ticker, data in portfolio.items():
            if data['quantity'] != 0:
                current_price = prices.get(ticker, data.get('average_price', 0))
                average_price = data.get('average_price', 0)
                quantity = data['quantity']
                
                current_value = current_price * quantity
                initial_value = average_price * quantity
                profit_loss = current_value - initial_value
                
                pnl[ticker] = {
                    'current_price': current_price,
                    'quantity': quantity,
                    'average_price': average_price,
                    'current_value': current_value,
                    'initial_value': initial_value,
                    'profit_loss': profit_loss,
                    'percentage_change': (profit_loss / abs(initial_value) * 100) if initial_value != 0 else 0,
                    'type': 'option' if len(ticker) >= 7 else 'stock'
                }
                
        return pnl
        
    def calculate_risk_metrics(self, prices_df, weights):
        """Calcula métricas de risco usando métodos alternativos ao scipy"""
        try:
            # Calcular retornos
            returns = prices_df.pct_change().dropna()
            
            # Volatilidade do portfolio
            portfolio_returns = (returns * weights).sum(axis=1)
            volatility = portfolio_returns.std() * np.sqrt(252)
            
            # VaR simplificado (assumindo distribuição normal)
            confidence_levels = [0.90, 0.95, 0.99]
            z_scores = [1.282, 1.645, 2.326]  # valores z para os níveis de confiança
            
            var_1_week = []
            var_1_month = []
            
            for z in z_scores:
                var_w = volatility * z * np.sqrt(5/252) * 100
                var_m = volatility * z * np.sqrt(21/252) * 100
                var_1_week.append(round(var_w, 2))
                var_1_month.append(round(var_m, 2))
                
            # Sharpe Ratio
            risk_free_rate = 0.1175  # Selic atual
            excess_returns = portfolio_returns.mean() * 252 - risk_free_rate
            sharpe_ratio = excess_returns / volatility if volatility > 0 else 0
            
            return {
                'volatility': volatility * 100,
                'var_1_week': var_1_week,
                'var_1_month': var_1_month,
                'sharpe_ratio': sharpe_ratio
            }
        except Exception as e:
            logger.error(f"Erro ao calcular métricas de risco: {e}")
            return {
                'volatility': 0,
                'var_1_week': [0, 0, 0],
                'var_1_month': [0, 0, 0],
                'sharpe_ratio': 0
            }
            
    def analyze_concentration(self, df):
        """Analisa concentração do portfolio"""
        # Top 5 posições
        df_sorted = df.sort_values('current_value', ascending=False)
        top5 = df_sorted.head(5)
        top5_concentration = (top5['current_value'].sum() / df['current_value'].sum()) * 100
        
        # Setores (simplificado)
        sectors = {
            'Financeiro': ['BBAS3', 'ITUB4', 'SANB11', 'BBDC4'],
            'Consumo': ['MGLU3', 'VVAR3', 'LREN3', 'PCAR3'],
            'Commodities': ['VALE3', 'PETR4', 'GGBR4', 'CSNA3'],
            'Utilities': ['ELET3', 'ENBR3', 'TAEE11', 'CPFE3'],
            'Outros': []
        }
        
        sector_allocation = {}
        for sector, tickers in sectors.items():
            sector_value = df[df.index.isin(tickers)]['current_value'].sum()
            if sector == 'Outros':
                sector_value = df[~df.index.isin([t for s in sectors.values() for t in s if s])]['current_value'].sum()
            sector_allocation[sector] = (sector_value / df['current_value'].sum()) * 100
            
        return {
            'top5': top5.to_dict('index'),
            'top5_concentration': top5_concentration,
            'sector_allocation': sector_allocation
        }
        
    def process_complete_analytics(self):
        """Processa análise completa do portfolio"""
        # Obter dados do fundo
        df_xml, data_xml, header = self.get_fund_data()
        
        # Extrair informações básicas
        pl_fundo = header.get('patliq', 0)
        data_dados = pd.to_datetime(header.get('dtposicao', datetime.now())).strftime('%d/%m/%Y')
        cota_fia = header.get('valorcota', 0)
        a_receber = header.get('valorreceber', 0)
        a_pagar = header.get('valorpagar', 0)
        
        # Obter portfolio via processor sem pandas
        try:
            logger.info("Processando portfolio com processor limpo")
            portfolio_data = process_portfolio_from_api_fixed()
            
            if portfolio_data:
                portfolio = portfolio_data.get('positions', {})
                df_operations = pd.DataFrame()  # Vazio por enquanto
            else:
                portfolio = {}
                df_operations = pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Erro ao obter portfolio: {e}")
            portfolio = {}
            df_operations = pd.DataFrame()
            
        # Portfolio já vem processado, só calcular métricas adicionais
        if portfolio:
            # Criar estrutura de preços para compatibilidade
            prices = {ticker: data['current_price'] for ticker, data in portfolio.items()}
            prices_full = {}  # Não usado na versão simplificada
            pnl = portfolio  # Já vem com os cálculos
            
            # Criar DataFrame principal
            df = pd.DataFrame.from_dict(pnl, orient='index')
            df['pcts_port'] = (df['current_value'] / df['current_value'].sum()) * 100
            
            # Separar ações e opções
            df_stocks = df[df['type'] == 'stock']
            df_options = df[df['type'] == 'option']
            
            # Métricas de risco (se houver ações)
            risk_metrics = {'volatility': 0, 'var_1_week': [0,0,0], 'var_1_month': [0,0,0], 'sharpe_ratio': 0}
            if len(df_stocks) > 0 and prices_full:
                # Criar DataFrame de preços
                price_cols = [col for col in df_stocks.index if col in prices_full]
                if price_cols:
                    df_prices = pd.DataFrame({
                        col: prices_full[col]['Fechamento'] 
                        for col in price_cols
                    })
                    weights = df_stocks.loc[price_cols, 'pcts_port'].values / 100
                    risk_metrics = self.calculate_risk_metrics(df_prices, weights)
            
            # Análise de concentração
            concentration = self.analyze_concentration(df) if not df.empty else {}
            
            # Dados de mercado
            market_data = self.get_market_data()
            
        else:
            df = pd.DataFrame()
            df_stocks = pd.DataFrame()
            df_options = pd.DataFrame()
            risk_metrics = {'volatility': 0, 'var_1_week': [0,0,0], 'var_1_month': [0,0,0], 'sharpe_ratio': 0}
            concentration = {}
            market_data = {'ibov_points': 0, 'ibov_change': 0, 'usd_brl': 0, 'usd_change': 0}
            
        # Calcular métricas gerais
        total_value = df['current_value'].sum() if not df.empty else 0
        total_pl = df['profit_loss'].sum() if not df.empty else 0
        portfolio_return = (total_pl / (total_value - total_pl) * 100) if (total_value - total_pl) > 0 else 0
        
        # Preparar dados finais
        analytics_data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'fund_info': {
                'name': 'AVALON FIA RESPONSABILIDADE LIMITADA',
                'cnpj': '40.921.027/0001-31',
                'data_position': data_dados,
                'pl': float(pl_fundo),
                'quota_value': float(cota_fia),
                'receivables': float(a_receber),
                'payables': float(a_pagar),
                'total_assets': len(df_xml)
            },
            'portfolio_summary': {
                'total_value': float(total_value),
                'total_pl': float(total_pl),
                'total_return': float(portfolio_return),
                'compliance_ratio': float(total_value / pl_fundo) if pl_fundo > 0 else 0,
                'derivatives_limit': float(abs(df_options['current_value'].sum()) / pl_fundo) if pl_fundo > 0 and not df_options.empty else 0,
                'stocks_count': len(df_stocks),
                'options_count': len(df_options)
            },
            'risk_metrics': risk_metrics,
            'market_data': market_data,
            'concentration': concentration,
            'positions': self.clean_dataframe(df),
            'stocks': self.clean_dataframe(df_stocks),
            'options': self.clean_dataframe(df_options),
            'operations_history': self.clean_dataframe(df_operations) if not df_operations.empty else []
        }
        
        return analytics_data
        
    def clean_dataframe(self, df):
        """Limpa DataFrame para serialização JSON"""
        if df.empty:
            return {}
            
        df_clean = df.copy()
        
        # Substituir NaN e Inf
        df_clean = df_clean.replace([np.inf, -np.inf], 0)
        df_clean = df_clean.fillna(0)
        
        # Converter tipos
        for col in df_clean.columns:
            if df_clean[col].dtype in ['float64', 'float32']:
                df_clean[col] = df_clean[col].round(2).astype(float)
            elif df_clean[col].dtype in ['int64', 'int32']:
                df_clean[col] = df_clean[col].astype(int)
                
        return df_clean.to_dict('index')


# Instância global
analytics = AvalonFIAAnalytics()


@app.route('/')
def index():
    """Página principal elegante"""
    # Usar a versão corrigida
    try:
        return render_template('dashboard_fixed.html')
    except:
        try:
            return render_template('dashboard_improved.html')
        except:
            return render_template('dashboard_elegant.html')


@app.route('/api/analytics')
def get_analytics():
    """API endpoint para dados completos"""
    try:
        data = analytics.process_complete_analytics()
        return jsonify(data)
    except Exception as e:
        logger.error(f"Erro ao processar analytics: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/refresh')
def refresh_data():
    """Força atualização dos dados"""
    try:
        # Limpar cache
        for file in analytics.pickle_dir.glob(f'*_{analytics.current_date}.pkl'):
            file.unlink()
            
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("🚀 Iniciando Avalon FIA Analytics - Versão Completa")
    print("💎 Dashboard elegante disponível em http://localhost:5000")
    app.run(debug=False, host='localhost', port=5000)