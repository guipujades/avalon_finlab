import os
import sys
import json
import uuid
import wget
import zipfile
from urllib.parse import urlparse
import time
import tempfile
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import requests
import pickle
import seaborn as sns
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from io import BytesIO
import base64
import schedule
from datetime import datetime, timedelta

def sys_path(choose_path):
    sys.path.append(str(choose_path))

home = Path.home()
apibtg_path = Path(home, 'Documents/GitHub/avaloncapital/api_btg')
local_path = Path(home, 'Documents/GitHub/avaloncapital/track_mfo_local')
mt5_connect = Path(home, 'Documents/GitHub/avaloncapital/mt5_utils')
path_list = [apibtg_path, local_path, mt5_connect]

if str(local_path) not in sys.path:
    for path in path_list:
        sys_path(path)

# from mt5_connect import initialize, prepare_symbol, get_prices_mt5
from api_btg_mfo_utils import find_file, remove_chars, get_token_btg, process_account_data, get_total_amount

# mt5_path = Path('C:/', 'Program Files', 'MetaTrader 5', 'terminal64.exe')
# initialize(user_path=str(mt5_path), server='XPMT5-DEMO', login=52276888, key='Cg21092013PM#')

# mt5_path = Path('C:/', 'Program Files', 'Rico - MetaTrader 5', 'terminal64.exe')
# initialize(user_path=str(mt5_path), server='GenialInvestimentos-PRD', login=156691, key='Avca@1985')

app = Flask(__name__)

def load_pickle(path):
    with open(path, 'rb') as file:
        return pickle.load(file)
    
def save_pickle(data, path):
    with open(path, 'wb') as file:
        pickle.dump(data, file)
        
def dataframe_to_dict(df):
    return df.reset_index().to_dict(orient='records')


def job():
    
    # Acessos e arquivos
    json_file_apiaccess = str(Path(Path.home(), 'Desktop', 'api_btg_access.json'))
    cl_data = Path(Path.home(), 'Documents', 'GitHub', 'database', 'data_cl.xlsx')

    # Datas
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    current_date = datetime.now().strftime('%Y%m%d')
    
    # Captura de dados da API
    # Caminho para os arquivos pickle
    pickle_dir = Path(Path.home(), 'Documents', 'GitHub', 'database', 'dados_api')
    file_for_today = Path(pickle_dir, f'api_mfo_{current_date}.pkl')
    
    # Verifica se os arquivos pickle do dia já existem
    if os.path.exists(file_for_today):
        clients = load_pickle(file_for_today)
        print('Dados carregados dos arquivos serializados.')
        
    else:
        # Capturar token BTG
        token = get_token_btg()
    
        # Parte de execucao de API em teste: avaliar por alguns meses assim antes de montar em funcao
        uuid_request = str(uuid.uuid4())
        url = 'https://api.btgpactual.com/iaas-api-position/api/v1/position/partner'
    
        headers    = {'x-id-partner-request': uuid_request,
                      'access_token': get_token_btg()
                     }
    
        response=requests.get(url=url, headers=headers).text
        response = json.loads(response)
    
        if response['errors'] is None:
            url_archive = response['response']['url']
            
            mystrip = lambda s, ss: s[:s.index(ss) + len(ss)]
            a = urlparse(mystrip(url_archive, ".zip"))
            a = os.path.basename(a.path)
            
        else:
            url_archive = None
            print('Ocorreu um erro ao fazer o request para pegar o url do arquivo.')
    
        temp_dir = tempfile.TemporaryDirectory()
        if not find_file(a, temp_dir.name):
            archive = wget.download(url_archive, temp_dir.name)
            
            with zipfile.ZipFile(archive, 'r') as zip_ref:
                zip_ref.extractall(temp_dir.name)    
        else:
            if not find_file('posicao'+time.strftime("%Y%m%d")+'.zip', temp_dir.name):
                try:
                    os.rename(a, 'posicao'+time.strftime("%Y%m%d")+'.zip')
                except:
                    pass
            archive = wget.download(url_archive, temp_dir.name)
            with zipfile.ZipFile(archive, 'r') as zip_ref:
                zip_ref.extractall(temp_dir.name)
            print('Arquivo ja existe, criando copia de backup...')
    
        pre_archive = os.path.splitext(archive)[0]
        number = os.path.basename(pre_archive)[:-9]
        path_archive = Path(temp_dir.name, 'iaas-position-holder', number, 'position')
    
        clients = {}
        for filename in os.listdir(path_archive):
            with open(os.path.join(path_archive, filename), encoding="utf8") as f:
                clients[remove_chars(filename, '.json')] = f.read()
        
        save_file = Path(pickle_dir, f'api_mfo_{current_date}.pkl')
        save_pickle(clients, save_file)
        print('Dados capturados da API e salvos em arquivos serializados.')

    # Abrir dados
    data_btg = pd.read_excel(cl_data)
    data_btg_dict = dataframe_to_dict(data_btg)
    
    # Preparar dados para envio
    data_to_send = {
        'clients': clients,
        'data_btg': data_btg_dict
        }
    
    url = 'https://trackmfo-8ff09a37ebe2.herokuapp.com/update_data'

    response = requests.post(url, json=data_to_send)

    if response.status_code == 200:
        print("Data updated successfully on Heroku")
    else:
        print("Failed to update data on Heroku:", response.text)
    
    
def run_scheduler():
    schedule.every(15).minutes.do(job)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    run_scheduler()
    app.run(debug=True)


