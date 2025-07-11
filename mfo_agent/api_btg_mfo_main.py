import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import os
import sys
import requests
import base64
import uuid
import wget
import zipfile
from urllib.parse import urlparse
import time
from tqdm import tqdm
import tempfile
import pickle


def sys_path(choose_path):
    sys.path.append(str(choose_path))

home = Path.home()
main_path = Path(home, 'Documents/GitHub/avaloncapital')
api_btg = Path(home, 'Documents/GitHub/avaloncapital/api_btg')
path_list = [main_path, api_btg]

if str(api_btg) not in sys.path:
    for path in path_list:
        sys_path(path)


from api_btg_mfo_utils import find_file, remove_chars, get_token_btg, process_account_data, get_total_amount


def load_pickle(path):
    with open(path, 'rb') as file:
        return pickle.load(file)
    
def save_pickle(data, path):
    with open(path, 'wb') as file:
        pickle.dump(data, file)

def get_api_data():
    
    # Acessos e arquivos
    json_file_apiaccess = str(Path(Path.home(), 'Desktop', 'api_btg_access.json'))
    cl_data = Path(Path.home(), 'Documents', 'GitHub', 'database', 'data_cl.xlsx')
    anb_data = Path(Path.home(), 'Documents', 'GitHub', 'database', 'anb_data.csv')
    
    # Datas
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    current_date = datetime.now().strftime('%Y%m%d')
    
    # Captura de dados da API
    # Caminho para os arquivos pickle
    pickle_dir = Path(Path.home(), 'Documents', 'GitHub', 'database', 'dados_api')
    
    # TODO (20240919): ocorreu algum erro na API. 
    # A funcao nao esta retornando o token. Tive que utilizar dados antigos para rodar a precificacao
    # file_for_today = Path(pickle_dir, f'api_mfo_{current_date}.pkl')
    file_for_today = Path(pickle_dir, f'api_mfo_20240830.pkl')
    
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
    
        response = requests.get(url=url, headers=headers).text
        response = json.loads(response)
    
        if response['errors'] == None:
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
            string = open(os.path.join(path_archive, filename), encoding="utf8")
            clients[remove_chars(filename, '.json')] = string.read()
        
        save_file = Path(pickle_dir, f'api_mfo_{current_date}.pkl')
        save_pickle(clients, save_file)
        print('Dados capturados da API e salvos em arquivos serializados.')
    
    return cl_data, anb_data, clients

# Ex. de uso
# cl_data, anb_data, clients = get_api_data()












































"""
# Abrir dados
data_btg = pd.read_excel(cl_data)
data_anbima = pd.read_csv(anb_data, sep='|')
data_anbima['Valor da taxa de gestão'] = data_anbima['Valor da taxa de gestão'].apply(lambda x: pd.to_numeric(x.replace(',','.')))

# Rodar taxa de gestao (pendente atualizacao)
for i in data_btg.index:
    if data_btg.loc[i,'Id'] == 0:
        continue
    else:
        if data_btg.loc[i,'Id'] in list(data_anbima['Campo de Apoio']):
            id_client = data_btg.loc[i,'Id']
            tx_gestao = list(data_anbima[data_anbima['Campo de Apoio'] == id_client]['Valor da taxa de gestão'])[0]
        else:
            tx_gestao = 1.0 # pendente para alguns clientes
            
    data_btg.loc[i, 'tx'] = tx_gestao

# Guarda de dados das contas dos clientes
pl_contas = {}
cobranca_por_cliente = {}
cobranca_total = 0.0
cash = {}
contas = {}

# Administração para Avalon FIA
avalon_fia_tax = 0.02

for client_id, data in clients.items():
    
    contas[client_id] = {}
    
    # Processar dados da conta do cliente
    (funds_df, fixed_income_df, coe_df, equities_df, derivatives_df,
     commodities_df, crypto_df, cash_df, pension_df, credits_df, pending_settlements_df, total_positions, total_equity) = process_account_data(data)
    
    # Armazenando cada um dos DataFrames retornados na estrutura do cliente
    contas[client_id]['fundos'] = funds_df
    contas[client_id]['renda_fixa'] = fixed_income_df
    contas[client_id]['coe'] = coe_df
    contas[client_id]['acoes'] = equities_df
    contas[client_id]['derivativos'] = derivatives_df
    contas[client_id]['commodities'] = commodities_df
    contas[client_id]['crypto'] = crypto_df
    contas[client_id]['cash'] = cash_df
    contas[client_id]['previdencia'] = pension_df
    contas[client_id]['creditos'] = credits_df
    contas[client_id]['valores_transito'] = pending_settlements_df
    contas[client_id]['posicoes_totais'] = total_positions
    contas[client_id]['patrimonio_total'] = total_equity
    
    
    
    # Obter valor total da conta
    total_ammount = get_total_amount(data)
    
    # Obter taxa de gestão
    if pd.to_numeric(client_id) not in list(data_btg.Conta):
        continue
    else:
        tx_gestao = list(data_btg[data_btg.Conta == pd.to_numeric(client_id)]['tx'])[0]
    
    # Limite mensal
    limite_mes = (total_ammount * (tx_gestao/100)) / 12
    
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
    
    cobranca_por_cliente[client_id] = tx_mes
    cash[client_id] = cash_df
    contas[client_id]['cash'] = cash_df

# Valor cobranca mensal
df_cobranca = pd.DataFrame(cobranca_por_cliente, index=[0]).T
# Total em cash - clientes
cash_app = pd.concat(cash)

df_cobranca.to_excel(Path(Path.home(), 'Desktop', 'cobranca_ago24.xlsx'))
"""










