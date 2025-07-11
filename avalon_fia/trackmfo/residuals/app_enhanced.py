"""
App Flask Enhanced - Versão melhorada do app.py original
Integra o sistema de captura e armazenamento com a interface web existente
"""

import os
import sys
from pathlib import Path
from flask import Flask, render_template, redirect, url_for, request, jsonify, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import pandas as pd
from datetime import datetime
import logging

# Adicionar imports locais
from mfo_data_receiver import MFODataReceiver
from data_storage import PortfolioDataStorage
from website_integration import WebsiteDataProcessor

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializa o Flask
app = Flask(__name__)

# Configurações de Limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=['200 per day', '50 per hour']
)

# Configurações do Flask
app.config['SECRET_KEY'] = 'Avalon@123'

# Inicializa o LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Inicializa componentes do sistema
storage = PortfolioDataStorage()
receiver = MFODataReceiver(storage)
web_processor = WebsiteDataProcessor(storage)

# Usuários
users = {'admin': {'password': 'Avalon@123'}}

# Data store global (mantido por compatibilidade)
data_store = None


class User(UserMixin):
    def __init__(self, id):
        self.id = id


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


@app.route('/login', methods=['GET', 'POST'])
@limiter.limit('5 per minute')
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]['password'] == password:
            user = User(username)
            login_user(user)
            logger.info(f"Login bem-sucedido: {username}")
            return redirect(url_for('index'))
        else:
            logger.warning(f"Tentativa de login falhou: {username}")
            flash('Invalid username or password', 'error')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/update_data', methods=['POST'])
def update_data():
    """Endpoint original mantido por compatibilidade"""
    global data_store
    data = request.get_json()
    
    if data is None:
        return jsonify({"status": "error", "message": "No JSON data received"}), 400
    
    # Armazenar no data_store original
    data_store = data
    
    # Processar com o novo sistema
    result = receiver.receive_data(data)
    
    # Gerar dados para website se bem-sucedido
    if result['status'] == 'success':
        web_processor.export_all_portfolios_for_web()
        web_processor.generate_dashboard_data()
    
    return jsonify(result), 200


@app.route('/api/summary', methods=['GET'])
@login_required
def get_summary():
    """Novo endpoint para obter resumo dos dados"""
    summary = receiver.get_processed_summary()
    return jsonify(summary)


@app.route('/api/portfolios', methods=['GET'])
@login_required
def get_portfolios():
    """Novo endpoint para listar portfolios"""
    portfolios_df = storage.get_all_portfolios()
    portfolios_list = portfolios_df.to_dict('records')
    return jsonify(portfolios_list)


@app.route('/api/portfolio/<portfolio_id>', methods=['GET'])
@login_required
def get_portfolio_detail(portfolio_id):
    """Novo endpoint para detalhes de um portfolio"""
    latest_capture = storage.get_latest_capture(portfolio_id)
    if latest_capture:
        return jsonify({
            'status': 'success',
            'data': web_processor.process_portfolio_for_web(portfolio_id)
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Portfolio não encontrado ou sem dados'
        }), 404


@app.route('/api/portfolio/<portfolio_id>/history', methods=['GET'])
@login_required
def get_portfolio_history(portfolio_id):
    """Novo endpoint para histórico de um portfolio"""
    days = request.args.get('days', 30, type=int)
    history = storage.get_portfolio_history(portfolio_id, days)
    return jsonify(history.to_dict('records'))


@app.route('/', methods=['GET'])
@login_required
def index():
    """Página principal - versão melhorada"""
    global data_store
    
    # Se temos dados no formato antigo, renderizar template original
    if data_store is not None:
        # Processar dados como no app.py original
        # (código mantido por compatibilidade)
        return render_template('index.html', data=data_store)
    
    # Caso contrário, mostrar dashboard novo
    summary = receiver.get_processed_summary()
    portfolios = storage.get_all_portfolios()
    
    # Preparar dados para o template
    dashboard_data = {
        'summary': summary,
        'portfolios': portfolios.to_dict('records') if not portfolios.empty else [],
        'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Verificar se existe template dashboard.html, senão usar index.html
    template = 'dashboard.html' if os.path.exists('templates/dashboard.html') else 'index.html'
    
    return render_template(template, **dashboard_data)


@app.route('/dashboard')
@login_required
def dashboard():
    """Novo dashboard com visualizações modernas"""
    # Obter dados consolidados
    dashboard_data = {}
    
    # Carregar dados do dashboard gerado
    dashboard_file = Path.home() / 'Documents' / 'GitHub' / 'avalon_fia' / 'website_data' / 'dashboard.json'
    
    if dashboard_file.exists():
        import json
        with open(dashboard_file, 'r') as f:
            dashboard_data = json.load(f)
    else:
        # Gerar dados na hora
        dashboard_data = web_processor.generate_dashboard_data()
    
    return render_template('dashboard_modern.html', data=dashboard_data)


@app.route('/reports')
@login_required
def reports():
    """Página de relatórios"""
    portfolios = storage.get_all_portfolios()
    
    # Gerar relatórios disponíveis
    reports_list = []
    for _, portfolio in portfolios.iterrows():
        try:
            report_path = storage.generate_portfolio_report(portfolio['id'])
            reports_list.append({
                'portfolio_id': portfolio['id'],
                'portfolio_name': portfolio['name'],
                'report_path': str(report_path),
                'generated_at': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Erro ao gerar relatório: {e}")
    
    return render_template('reports.html', reports=reports_list)


@app.route('/api/capture/trigger', methods=['POST'])
@login_required
def trigger_capture():
    """Endpoint para disparar captura manual"""
    # Importar e executar captura
    try:
        from portfolio_capture import PortfolioCapture, PortfolioCaptureConfig
        
        config = PortfolioCaptureConfig()
        capture = PortfolioCapture(config)
        
        # Capturar portfolio específico ou todos
        portfolio_id = request.json.get('portfolio_id') if request.json else None
        
        if portfolio_id:
            # Capturar apenas um
            if portfolio_id in config.portfolios:
                portfolio_info = config.portfolios[portfolio_id]
                if portfolio_info['type'] == 'fund':
                    result = capture.capture_fund_data(portfolio_info)
                else:
                    result = capture.capture_digital_account_data(portfolio_info)
                
                if result['success']:
                    storage.save_capture(portfolio_id, result)
                
                return jsonify(result)
            else:
                return jsonify({'status': 'error', 'message': 'Portfolio não encontrado'}), 404
        else:
            # Capturar todos
            results = capture.capture_all_portfolios()
            return jsonify({'status': 'success', 'results': results})
            
    except Exception as e:
        logger.error(f"Erro na captura: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    logger.info("Iniciando aplicação MFO Enhanced")
    logger.info(f"Storage path: {storage.base_path}")
    
    # Criar diretórios necessários
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # Executar aplicação
    app.run(debug=True, host='0.0.0.0', port=5000)