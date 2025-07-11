import os
import base64
import logging
import requests
import numpy as np
import pandas as pd
from io import BytesIO
from datetime import datetime
import matplotlib.pyplot as plt
from flask import Flask, render_template, redirect, url_for, request, jsonify, flash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user


from api_btg_mfo_utils import process_account_data, get_total_amount


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

# Configuração de Log
logging.basicConfig(level=logging.DEBUG)

# Usuários e Data Store
users = {'admin': {'password': 'Avalon@123'}}
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
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# import os
# import sys
# from flask import Flask, render_template, redirect, url_for, request, jsonify, flash
# from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
# import pandas as pd
# from pathlib import Path
# import matplotlib.pyplot as plt
# import matplotlib.colors as mcolors
# from io import BytesIO
# import base64
# from datetime import datetime, timedelta

# def sys_path(choose_path):
#     sys.path.append(str(choose_path))

# home = Path.home()
# apibtg_path = Path(home, 'Documents/GitHub/avaloncapital/api_btg')
# local_path = Path(home, 'Documents/GitHub/avaloncapital/track_mfo_local')
# mt5_connect = Path(home, 'Documents/GitHub/avaloncapital/mt5_utils')
# path_list = [apibtg_path, local_path, mt5_connect]

# if str(mt5_connect) not in sys.path:
#     for path in path_list:
#         sys_path(path)

# # from mt5_connect import initialize, prepare_symbol, get_prices_mt5
# from api_btg_mfo_utils import process_account_data, get_total_amount

# # mt5_path = Path('C:/', 'Program Files', 'MetaTrader 5', 'terminal64.exe')
# # initialize(user_path=str(mt5_path), server='XPMT5-DEMO', login=52276888, key='Cg21092013PM#')

# # mt5_path = Path('C:/', 'Program Files', 'Rico - MetaTrader 5', 'terminal64.exe')
# # initialize(user_path=str(mt5_path), server='GenialInvestimentos-PRD', login=156691, key='Avca@1985')

# app = Flask(__name__)
# # pl_fundo = 1_700_000.00

# app.config['SECRET_KEY'] = 'Avalon@123'

# login_manager = LoginManager()
# login_manager.init_app(app)
# login_manager.login_view = 'login'


# class User(UserMixin):
#     def __init__(self, id):
#         self.id = id

# users = {'admin': {'password': 'Avalon@123'}}


# @login_manager.user_loader
# def load_user(user_id):
#     return User(user_id)


# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     print("Login page accessed")
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']
#         print(f"Attempting login with username: {username} and password: {password}")
#         if username in users and users[username]['password'] == password:
#             user = User(username)
#             login_user(user)
#             print("Login successful")
#             return redirect(url_for('index'))
#         else:
#             print("Login failed")
#             flash('Invalid username or password', 'error')
#     return render_template('login.html')


# @app.route('/logout')
# @login_required
# def logout():
#     logout_user()
#     return redirect(url_for('login'))


@app.route('/update_data', methods=['POST'])
def update_data():
    global data_store
    data = request.get_json()
    if data is None:
        return jsonify({"status": "error", "message": "No JSON data received"}), 400
    
    data_store = data
    return jsonify({"status": "success", "message": "Data updated successfully"}), 200


def plot_histogram(client_id, data):
    df = pd.DataFrame(data)
    plt.figure(figsize=(10, 6))
    plt.barh(df['Produtos'], df['Percentual'], color='skyblue')
    plt.xlabel('Percentual (%)')
    plt.title(f'Percentual por Produto - Cliente {client_id}')
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return base64.b64encode(buf.getvalue()).decode('utf-8')


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    global data_store
    if data_store is None:
        return jsonify({"status": "error", "message": "No data available. Please update the data."}), 200
    
    # Datas
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    current_date = datetime.now().strftime('%Y%m%d')
    
    clients = data_store['clients']
    data_btg = pd.DataFrame.from_dict(data_store['data_btg'])

    # Guarda de dados das contas dos clientes
    pl_contas = {}
    cobranca_por_cliente = {}
    cobranca_total = 0.0
    cash = {}
    contas = {}
    count_crash = []
    
    # Administração para Avalon FIA
    avalon_fia_tax = 0.02

    for client_id, data in clients.items():
        
        if pd.to_numeric(client_id) not in list(data_btg.Conta):
            continue
        else:
            internal_id = list(data_btg[data_btg.Conta == pd.to_numeric(client_id)]['Id'])[0]

        contas[internal_id] = {}
        
        # Processar dados da conta do cliente
        (funds_df, fixed_income_df, coe_df, equities_df, derivatives_df,
         commodities_df, crypto_df, cash_df, pension_df, credits_df, pending_settlements_df, total_positions, total_equity) = process_account_data(data)
        
        # Armazenando cada um dos DataFrames retornados na estrutura do cliente
        contas[internal_id]['fundos'] = funds_df
        contas[internal_id]['renda_fixa'] = fixed_income_df
        contas[internal_id]['coe'] = coe_df
        contas[internal_id]['acoes'] = equities_df
        contas[internal_id]['derivativos'] = derivatives_df
        contas[internal_id]['commodities'] = commodities_df
        contas[internal_id]['crypto'] = crypto_df
        contas[internal_id]['cash'] = cash_df
        contas[internal_id]['previdencia'] = pension_df
        contas[internal_id]['creditos'] = credits_df
        contas[internal_id]['valores_transito'] = pending_settlements_df
        contas[internal_id]['posicoes_totais'] = total_positions
        contas[internal_id]['patrimonio_total'] = total_equity
        
        # Obter valor total da conta
        total_ammount = get_total_amount(data)
        
        # Obter taxa de gestão
        if pd.to_numeric(client_id) not in list(data_btg.Conta):
            continue
        else:
            tx_gestao = list(data_btg[data_btg.Conta == pd.to_numeric(client_id)]['Taxas'])[0]
        
        if tx_gestao == 0.0:
            tx_mes = 0.0
        
        else:
            
            # Limite mensal
            limite_mes = (total_ammount * (tx_gestao)) / 12
            
            if pd.isna(limite_mes):
                print(f"Limite mensal para cliente {client_id} é indefinido.")
                continue
            
            if isinstance(limite_mes, (int, float)):
                cobranca_total = cobranca_total + limite_mes
         
            # Verificar se o cliente tem investimento no Avalon FIA
            avalon_fia = funds_df[funds_df['FundName'] == 'Avalon FIA RL']
            cobranca_avalon_fia = 0.0
            
            if not avalon_fia.empty:
                investimento_avalon_fia = avalon_fia['GrossAssetValue'].sum()
                cobranca_avalon_fia = investimento_avalon_fia * (avalon_fia_tax / 12)
            
                tx_mes = limite_mes - cobranca_avalon_fia
            
            else:
                
                tx_mes = limite_mes
            
            if tx_mes < 0:
                count_crash.append(client_id)
        
        cobranca_por_cliente[internal_id] = tx_mes
        cash[internal_id] = cash_df
        contas[internal_id]['cash'] = cash_df
    
    # Valor cobranca mensal
    df_cobranca = pd.DataFrame(cobranca_por_cliente, index=[0]).T
    df_cobranca.reset_index(inplace=True)
    df_cobranca.columns = ['Id', current_date]
    df_cobranca = pd.merge(df_cobranca, data_btg, on='Id')
    df_cobranca.set_index('Conta', inplace=True)
    df_cobranca.index.name = ''
    df_cobranca.drop(columns=['Id'], inplace=True)
    df_cobranca.drop(columns=['index'], inplace=True)
    
    # Total em cash - clientes
    df_cash = pd.concat(cash)

    # Filtrando contas com valores maiores que 100 em cash
    df_cash_obs = df_cash[df_cash.Value>100]
    
    # Preparar dados para histograma
    data_plot = {}
    no_pl = []
    for client_id, data in contas.items():
        
        if contas[client_id]['patrimonio_total'] > 0:
            
            # Calcular os percentuais para cada tipo de produto
            percentuais = [
                data['fundos']['GrossAssetValue'].sum() / contas[client_id]['patrimonio_total'] * 100 if not data['fundos'].empty else 0,
                data['renda_fixa']['GrossValue'].sum() / contas[client_id]['patrimonio_total'] * 100 if not data['renda_fixa'].empty else 0,
                data['coe']['GrossValue'].sum() / contas[client_id]['patrimonio_total'] * 100 if not data['coe'].empty else 0,
                data['acoes']['GrossValue'].sum() / contas[client_id]['patrimonio_total'] * 100 if not data['acoes'].empty else 0,
                data['derivativos']['GrossValue'].sum() / contas[client_id]['patrimonio_total'] * 100 if not data['derivativos'].empty else 0,
                data['commodities']['GrossValue'].sum() / contas[client_id]['patrimonio_total'] * 100 if not data['commodities'].empty else 0,
                data['crypto']['GrossValue'].sum() / contas[client_id]['patrimonio_total'] * 100 if not data['crypto'].empty else 0,
                data['cash']['Value'].sum() / contas[client_id]['patrimonio_total'] * 100 if not data['cash'].empty else 0,
                data['previdencia']['GrossAssetValue'].sum() / contas[client_id]['patrimonio_total'] * 100 if not data['previdencia'].empty else 0,
                data['creditos']['GrossValue'].sum() / contas[client_id]['patrimonio_total'] * 100 if not data['creditos'].empty else 0,
                data['valores_transito']['FinancialValue'].sum() / contas[client_id]['patrimonio_total'] * 100 if not data['valores_transito'].empty else 0
            ]
            
            # Verificar se o somatório dos percentuais está em 100%
            soma_percentuais = sum(percentuais)
            if abs(soma_percentuais - 100) <= 1:
                print(f"Cliente {client_id}: Somatório de percentuais está em {soma_percentuais:.2f}% (OK)")
            else:
                print(f"Cliente {client_id}: Somatório de percentuais está em {soma_percentuais:.2f}% (ERRO)")
                break
            
            data_plot[client_id] = {
                'Produtos': ['Fundos', 'Renda Fixa', 'COE', 'Ações', 'Derivativos', 'Commodities', 'Criptomoedas', 'Caixa', 'Previdência', 'Créditos', 'Em Trânsito'],
                'Percentual': percentuais
            }
        
        else:
            print(f'Cliente {client_id} sem PL...')
            no_pl.append(client_id)

    selected_client = int(request.form.get('client_select')) if request.method == 'POST' else list(data_plot.keys())[0]

    # Verificar se o selected_client está no data_plot
    if selected_client in data_plot:
        histogram_image = plot_histogram(selected_client, data_plot[selected_client])
    else:
        print(f"Erro: Cliente {selected_client} não encontrado em data_plot")
        histogram_image = None  # Ou alguma imagem padrão ou mensagem de erro

    return render_template('index.html', df_cobranca=df_cobranca.to_html(classes='table table-striped', border=0), data_plot=data_plot, selected_client=selected_client, histogram_image=histogram_image)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
