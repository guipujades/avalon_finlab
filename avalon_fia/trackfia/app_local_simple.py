#!/usr/bin/env python3
"""
Aplicação local simplificada para visualização dos dados do fundo AVALON FIA
Versão sem scipy para evitar problemas de dependências
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

# Adicionar o diretório ao path
sys.path.append(str(Path(__file__).parent))

# Importar módulos customizados
from api_btg_funds import fund_data_corrected

# Configurar Flask
app = Flask(__name__)

# Configurar logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AvalonFIATrackerSimple:
    """Classe simplificada para tracking do fundo Avalon FIA"""
    
    def __init__(self):
        self.current_date = datetime.now().strftime('%Y-%m-%d')
        self.pickle_dir = Path.home() / 'Documents' / 'GitHub' / 'database' / 'dados_api'
        self.pickle_dir.mkdir(parents=True, exist_ok=True)
        
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
            try:
                df_xml, data_xml, header = fund_data_corrected('xml')
                
                # Salvar cache
                with open(df_xml_path, 'wb') as f:
                    pkl.dump(df_xml, f)
                with open(data_xml_path, 'wb') as f:
                    pkl.dump(data_xml, f)
                with open(header_path, 'wb') as f:
                    pkl.dump(header, f)
            except Exception as e:
                logger.error(f"Erro ao obter dados da API: {e}")
                # Retornar dados vazios
                return pd.DataFrame(), [], {}
                
        return df_xml, data_xml, header
        
    def process_portfolio_data_simple(self):
        """Processa dados do portfolio de forma simplificada"""
        # Obter dados do fundo
        df_xml, data_xml, header = self.get_fund_data()
        
        if not header:
            # Retornar dados padrão se não houver dados
            return self.get_default_data()
        
        # Extrair informações do header
        pl_fundo = header.get('patliq', 0)
        data_dados = pd.to_datetime(header.get('dtposicao', datetime.now())).strftime('%d/%m/%Y')
        cota_fia = header.get('valorcota', 0)
        a_receber = header.get('valorreceber', 0)
        a_pagar = header.get('valorpagar', 0)
        
        # Processar ativos do DataFrame
        portfolio_summary = {}
        if not df_xml.empty:
            # Agrupar por tipo
            for tipo in df_xml['tipo'].unique():
                assets = df_xml[df_xml['tipo'] == tipo]
                total_val = assets['valorfindisp'].sum() if 'valorfindisp' in assets.columns else 0
                # Garantir que não há NaN ou Infinity
                if pd.isna(total_val) or np.isinf(total_val):
                    total_val = 0
                portfolio_summary[tipo] = {
                    'count': int(len(assets)),
                    'total_value': float(total_val)
                }
        
        # Calcular métricas básicas
        total_ativos = df_xml['valorfindisp'].sum() if 'valorfindisp' in df_xml.columns else 0
        if pd.isna(total_ativos) or np.isinf(total_ativos):
            total_ativos = 0
        enquadramento = total_ativos / pl_fundo if pl_fundo > 0 else 0
        
        # Limpar DataFrame antes de converter
        df_xml_clean = df_xml.copy()
        # Substituir NaN e Infinity por 0
        df_xml_clean = df_xml_clean.fillna(0)
        df_xml_clean = df_xml_clean.replace([np.inf, -np.inf], 0)
        
        # Converter para tipos básicos
        for col in df_xml_clean.columns:
            if df_xml_clean[col].dtype == 'float64':
                df_xml_clean[col] = df_xml_clean[col].astype(float)
            elif df_xml_clean[col].dtype == 'int64':
                df_xml_clean[col] = df_xml_clean[col].astype(int)
        
        # Preparar dados finais
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        portfolio_data = {
            'current_time': current_time,
            'data': data_dados,
            'current_pl': float(pl_fundo),
            'cota': float(cota_fia),
            'receber': float(a_receber),
            'pagar': float(a_pagar),
            'enquadramento': float(enquadramento),
            'total_ativos': int(len(df_xml)),
            'portfolio_summary': portfolio_summary,
            'df_assets': df_xml_clean.to_dict('records') if not df_xml_clean.empty else [],
            # Métricas simplificadas (sem cálculos complexos)
            'limits_der': 0,
            'portfolio_change': 0,
            'portfolio_change_stocks': 0,
            'portfolio_daily_change': 0,
            'portfolio_weekly_change': 0,
            'portfolio_var_1_week': [0, 0, 0],
            'portfolio_var_1_month': [0, 0, 0]
        }
        
        return portfolio_data
        
    def get_default_data(self):
        """Retorna dados padrão quando não há dados disponíveis"""
        return {
            'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data': datetime.now().strftime('%d/%m/%Y'),
            'current_pl': 0,
            'cota': 0,
            'receber': 0,
            'pagar': 0,
            'enquadramento': 0,
            'total_ativos': 0,
            'portfolio_summary': {},
            'df_assets': [],
            'limits_der': 0,
            'portfolio_change': 0,
            'portfolio_change_stocks': 0,
            'portfolio_daily_change': 0,
            'portfolio_weekly_change': 0,
            'portfolio_var_1_week': [0, 0, 0],
            'portfolio_var_1_month': [0, 0, 0]
        }


# Instância global do tracker
tracker = AvalonFIATrackerSimple()


@app.route('/')
def index():
    """Página principal"""
    return render_template('index_simple.html')


@app.route('/api/portfolio_data')
def get_portfolio_data():
    """API endpoint para obter dados do portfolio"""
    try:
        portfolio_data = tracker.process_portfolio_data_simple()
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
        portfolio_data = tracker.process_portfolio_data_simple()
        return jsonify({'status': 'success', 'message': 'Dados atualizados'})
    except Exception as e:
        logger.error(f"Erro ao atualizar: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("🚀 Iniciando Avalon FIA Tracker Local (Versão Simplificada)")
    print("📊 Acesse http://localhost:5000 para visualizar os dados")
    app.run(debug=True, host='localhost', port=5000)