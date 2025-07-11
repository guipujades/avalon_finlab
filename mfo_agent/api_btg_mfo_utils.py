"""
Bem-Vindo ao Portal do Desenvolvedor. Para acessar é muito simples, basta clicar no link abaixo e preencher com suas credenciais de acesso.
https://developer.btgpactualdigital.com/
"""

import os
import sys
import requests
import json
import base64
import uuid
import wget
import zipfile
import pandas as pd
from urllib.parse import urlparse
import time
from pathlib import Path


def sys_path(choose_path):
    sys.path.append(str(choose_path))

home = Path.home()
main_path = Path(home, 'Documents/GitHub/avaloncapital')
api_btg = Path(home, 'Documents/GitHub/avaloncapital/api_btg')
path_list = [main_path, api_btg]

if str(api_btg) not in sys.path:
    for path in path_list:
        sys_path(path)


# from api_btg_mfo_utils import get_token_btg
json_file_apiaccess = str(Path(Path.home(), 'Desktop', 'api_btg_access.json'))


def find_file(name, path):
    for root, dirs, files in os.walk(path):
        if name in files:
            return True


def remove_chars(data, chars):
    new_data = data
    for ch in chars:
        new_data = new_data.replace(ch, '')
    return new_data


def get_token_btg() -> str:
    """
    Capturar token para conta no BTG
    """

    # load data from json file
    with open(json_file_apiaccess) as json_file:
        data = json.load(json_file)

    # store client id and secret in variables
    client_id = data['client_id']
    client_secret = data['client_secret']
    
    credentials = client_id+":"+client_secret
    cred_bytes = credentials.encode("ascii")  
    base64_bytes = base64.b64encode(cred_bytes)
    base64_string = base64_bytes.decode("ascii")
    
    uuid_request = str(uuid.uuid4())
    
    url = 'https://api.btgpactual.com/iaas-auth/api/v1/authorization/oauth2/accesstoken?grant_type=client_credentials'
    headers    = {'x-id-partner-request': uuid_request,
                  'Authorization': 'Basic ' + base64_string,
                  "Content-Type": "application/x-www-form-urlencoded"
                  }
    
    data = {'grant_type':'client_credentials'}
    response = requests.post(url=url,  params=data, headers=headers)
    
    if response.headers['access_token'] == None or response.headers['access_token'] == '':
      print('\nI got a null or empty string value for data in a file')
    else:
        token = response.headers['access_token']
    
    return token


def process_account_data(account_data):
    account_summary = json.loads(account_data)
    
    # Inicializa os totais
    total_positions = 0.0
    total_equity = 0.0
    
    # DataFrames para armazenar os dados de cada categoria
    funds_df = pd.DataFrame(columns=['FundName', 'GrossAssetValue'])
    fixed_income_df = pd.DataFrame(columns=['Issuer', 'GrossValue'])
    coe_df = pd.DataFrame(columns=['Issuer', 'GrossValue'])
    equities_df = pd.DataFrame(columns=['Ticker', 'GrossValue'])
    derivatives_df = pd.DataFrame(columns=['Description', 'GrossValue'])
    commodities_df = pd.DataFrame(columns=['Ticker', 'GrossValue'])
    crypto_df = pd.DataFrame(columns=['AssetName', 'GrossValue'])
    cash_df = pd.DataFrame(columns=['Value'])
    pension_df = pd.DataFrame(columns=['FundName', 'GrossAssetValue'])
    credits_df = pd.DataFrame(columns=['ContractCode', 'GrossValue'])
    pending_settlements_df = pd.DataFrame(columns=['Description', 'FinancialValue'])

    # Fundos de Investimento
    investment_funds = account_summary.get('InvestmentFund', []) or []
    for fund in investment_funds:
        fund_name = fund.get('Fund', {}).get('FundName', '')
        acquisitions = fund.get('Acquisition', []) or []
        for acquisition in acquisitions:
            gross_asset_value = float(acquisition.get('GrossAssetValue', 0))
            funds_df = pd.concat([funds_df, pd.DataFrame({
                'FundName': [fund_name],
                'GrossAssetValue': [gross_asset_value]
            })], ignore_index=True)
            total_positions += gross_asset_value

    # Renda Fixa
    fixed_income = account_summary.get('FixedIncome', []) or []
    for bond in fixed_income:
        issuer = bond.get('Issuer', '')
        gross_value = float(bond.get('GrossValue', 0))
        fixed_income_df = pd.concat([fixed_income_df, pd.DataFrame({
            'Issuer': [issuer],
            'GrossValue': [gross_value]
        })], ignore_index=True)
        total_positions += gross_value

    # COEs
    coes = account_summary.get('FixedIncomeStructuredNote', []) or []
    for coe in coes:
        issuer = coe.get('Issuer', '')
        gross_value = float(coe.get('GrossValue', 0))
        coe_df = pd.concat([coe_df, pd.DataFrame({
            'Issuer': [issuer],
            'GrossValue': [gross_value]
        })], ignore_index=True)
        total_positions += gross_value

    # Acoes
    equities = account_summary.get('Equities', []) or []
    for equity in equities:
        stock_positions = equity.get('StockPositions', []) or []
        for stock in stock_positions:
            ticker = stock.get('Ticker', '')
            gross_value = float(stock.get('GrossValue', 0))
            equities_df = pd.concat([equities_df, pd.DataFrame({
                'Ticker': [ticker],
                'GrossValue': [gross_value]
            })], ignore_index=True)
            total_positions += gross_value

    # Derivativos
    derivatives = account_summary.get('Derivative', []) or []
    for derivative in derivatives:
        ndf_positions = derivative.get('NDFPosition', []) or []
        for ndf in ndf_positions:
            description = ndf.get('ReferencedSecurity', '')
            gross_value = float(ndf.get('GrossValue', 0))
            derivatives_df = pd.concat([derivatives_df, pd.DataFrame({
                'Description': [description],
                'GrossValue': [gross_value]
            })], ignore_index=True)
            total_positions += gross_value

    # Commodities
    commodities = account_summary.get('Commodity', []) or []
    for commodity in commodities:
        ticker = commodity.get('Ticker', '')
        gross_value = float(commodity.get('MarketValue', 0))  # Assumindo que usamos MarketValue aqui
        commodities_df = pd.concat([commodities_df, pd.DataFrame({
            'Ticker': [ticker],
            'GrossValue': [gross_value]
        })], ignore_index=True)
        total_positions += gross_value

    # Moedas Digitais
    cryptos = account_summary.get('CryptoCoins', []) or []
    for crypto in cryptos:
        asset_name = crypto.get('asset', {}).get('name', '')
        gross_value = float(crypto.get('grossFinancial', 0))
        crypto_df = pd.concat([crypto_df, pd.DataFrame({
            'AssetName': [asset_name],
            'GrossValue': [gross_value]
        })], ignore_index=True)
        total_positions += gross_value

    # Dinheiro em Conta
    cash = account_summary.get('Cash', []) or []
    for account in cash:
        current_account_value = float(account.get('CurrentAccount', {}).get('Value', 0))
        cash_df = pd.concat([cash_df, pd.DataFrame({
            'Value': [current_account_value]
        })], ignore_index=True)
        total_equity += current_account_value

    # Previ
    pensions = account_summary.get('PensionInformations', []) or []
    for pension in pensions:
        positions = pension.get('Positions', []) or []
        for position in positions:
            fund_name = position.get('FundName', '')
            gross_asset_value = float(position.get('GrossAssetValue', 0))
            pension_df = pd.concat([pension_df, pd.DataFrame({
                'FundName': [fund_name],
                'GrossAssetValue': [gross_asset_value]
            })], ignore_index=True)
            total_positions += gross_asset_value

    # Creditos
    credits_ = account_summary.get('Credits', []) or []
    for credit in credits_:
        loans = credit.get('Loan', []) or []
        for loan in loans:
            contract_code = loan.get('ContractCode', '')
            gross_value = float(loan.get('PrincipalAmount', 0))  # Usando PrincipalAmount se GrossValue n�o estiver presente
            credits_df = pd.concat([credits_df, pd.DataFrame({
                'ContractCode': [contract_code],
                'GrossValue': [gross_value]
            })], ignore_index=True)
            total_positions += gross_value
            
    # Valores em transito
    pending_settlements = account_summary.get('PendingSettlements', []) or []
    for settlement in pending_settlements:
        for category in ['FixedIncome', 'InvestmentFund', 'Equities', 'Derivative', 'Pension', 'Others']:
            transactions = settlement.get(category, []) or []
            for transaction in transactions:
                description = transaction.get('Description', '')
                financial_value = float(transaction.get('FinancialValue', 0))
                pending_settlements_df = pd.concat([pending_settlements_df, pd.DataFrame({
                    'Description': [description],
                    'FinancialValue': [financial_value]
                })], ignore_index=True)
                total_positions += financial_value

    # PL Total = Total das posicoes + Dinheiro em Conta
    total_equity += total_positions

    return (funds_df, fixed_income_df, coe_df, equities_df, derivatives_df,
            commodities_df, crypto_df, cash_df, pension_df, credits_df, pending_settlements_df, total_positions, total_equity)


def get_total_amount(account_data):
    # Carrega os dados da conta a partir da string JSON
    account_summary = json.loads(account_data)
    
    # Extrai o valor de TotalAmmount
    total_amount = float(account_summary.get('TotalAmmount', 0.0))
    
    return total_amount


def get_account_movements(account_number: str):
    token = get_token_btg()
    uuid_request = str(uuid.uuid4())
    
    url = f'https://api.btgpactual.com/iaas-api-operation/api/v1/operation/history/{account_number}'
    headers = {
        'x-id-partner-request': uuid_request,
        'access_token': token
    }
    
    # Fazer a requisi��o
    response = requests.get(url=url, headers=headers)
    
    if response.status_code == 202:
        print(f"Request accepted for account {account_number}.")
        print("Movements will be sent via webhook.")
    elif response.status_code == 400:
        print("Validation error:", response.json())
    elif response.status_code == 401:
        print("Unauthorized: Check your access token.")
    elif response.status_code == 404:
        print("Account or URL not found.")
    elif response.status_code == 500:
        print("Internal server error.")
    else:
        print(f"Unexpected error: {response.status_code} - {response.text}")


def get_account_profitability(reference_month: str, reference_year: str):
    token = get_token_btg()
    uuid_request = str(uuid.uuid4())
    
    url = 'https://api.btgpactual.com/api-partner-report-hub/api/v1/report/customer-profitability'
    headers = {
        'x-id-partner-request': uuid_request,
        'access_token': token
    }
    
    body = {
        "referenceMonth": reference_month,
        "referenceYear": reference_year
    }
    
    # Fazer a requisi��o
    response = requests.post(url=url, headers=headers, json=body)
    
    if response.status_code == 202:
        print(f"Request accepted for reference {reference_month}/{reference_year}.")
        print("Movements will be sent via webhook.")
    elif response.status_code == 400:
        print("Validation error:", response.json())
    elif response.status_code == 401:
        print("Unauthorized: Check your access token.")
    elif response.status_code == 403:
        print("Forbidden: Check your request body or headers.")
    elif response.status_code == 404:
        print("Account or URL not found.")
    elif response.status_code == 500:
        print("Internal server error.")
    else:
        print(f"Unexpected error: {response.status_code} - {response.text}")






# Uso para PL nas contas por mes
# get_account_profitability("07", "2024")

# Uso para movimentacoes de conta
# account_number = '004300296'
# get_account_movements(account_number)



















# def position(token) -> dict:
#     """
#     Capturar posicoes para o dia
#     """

#     uuid_request = str(uuid.uuid4())
#     url = 'https://api.btgpactual.com/iaas-api-position/api/v1/position/partner'
    
#     headers    = {'x-id-partner-request': uuid_request,
#                   'access_token': get_token_btg()
#                  }
    
#     response=requests.get(url=url, headers=headers).text
#     response = json.loads(response)
    
#     if response['errors'] == None:
#         url_archive = response['response']['url']
        
#         mystrip = lambda s, ss: s[:s.index(ss) + len(ss)]
#         a = urlparse(mystrip(url_archive, ".zip"))
#         a = os.path.basename(a.path)
        
#     else:
#         url_archive = None
#         print('Ocorreu um erro ao fazer o request para pegar o url do arquivo.')
    
#     temp_dir = tempfile.TemporaryDirectory()
#     if not find_file(a, temp_dir.name):
#         archive = wget.download(url_archive, temp_dir.name)
        
#         with zipfile.ZipFile(archive, 'r') as zip_ref:
#             zip_ref.extractall(temp_dir.name)    
#     else:
#         if not find_file('posicao'+time.strftime("%Y%m%d")+'.zip', temp_dir.name):
#             try:
#                 os.rename(a, 'posicao'+time.strftime("%Y%m%d")+'.zip')
#             except:
#                 pass
#         archive = wget.download(url_archive, temp_dir.name)
#         with zipfile.ZipFile(archive, 'r') as zip_ref:
#             zip_ref.extractall(temp_dir.name)
#         print('Arquivo ja existe, criando copia de backup...')
    
#     pre_archive = os.path.splitext(archive)[0]
#     number = os.path.basename(pre_archive)[:-9]
#     path_archive = Path(temp_dir.name, 'iaas-position-holder', number, 'position')
    
#     clients = {}
#     for filename in os.listdir(path_archive):
#         string = open(os.path.join(path_archive, filename), encoding="utf8")
#         clients[remove_chars(filename, '.json')] = string.read()
    
#     return clients


# def info_clients(pos_clientes, token) -> dict:
#     uuid_request = str(uuid.uuid4())
#     info_clientes = {}
#     counter = 0
#     for k in tqdm(pos_clientes.keys()):
#         url = 'https://api.btgpactual.com/iaas-account-management/api/v1/account-management/account/'+k+'/information'
    
#         headers    = {'x-id-partner-request': uuid_request,
#                       'access_token': token
#                      }
#         response=requests.get(url=url, headers=headers).text
#         info_clientes[k] = json.loads(response)
#         counter+=1
        
#         if counter == 50:
#             print('\nTempo de espera para habilitar novas chamadas...')
#             time.sleep(60)
#             counter = 0
        
#     return info_clientes


# def build_position(pos_clientes, info_clientes) -> dict:
#     info = {}
#     for c in info_clientes.keys():
#         temp = json.loads(pos_clientes[c])
#         try:
#             # if pd.to_numeric(temp['TotalAmmount']) > 0:
#             info[info_clientes[c]['holder']['taxIdentification']] = {'Nome': info_clientes[c]['users'][0]['name'],
#                                                                         ' Email':info_clientes[c]['users'][0]['userEmail'],
#                                                                         'PL': temp['TotalAmmount'],
#                                                                         'Disponível em conta':temp['SummaryAccounts'][0]['EndPositionValue'],
#                                                                         'Data_Pos': temp['PositionDate'],
#                                                                         'Resumo_Totais': temp['SummaryAccounts'], 
#                                                                         'RV': temp['Equities'],
#                                                                         'RF': temp['FixedIncome'],
#                                                                         'Prev': temp['PensionInformations'],
#                                                                         'Fundos': temp['InvestmentFund']
#                                                                     }
#         except:
#             print('api_btg / build_position: sem info de cliente...')
#             continue
        
#     return info


# def btg_open():
#     token = get_token_btg()
#     pos_clientes = position(token)
#     # info_clientes = info_clients(pos_clientes, token) 
#     # info_planilha = build_position(pos_clientes, info_clientes)
#     # return pos_clientes, info_clientes, info_planilha
#     return pos_clientes


# def get_resumos_btg(info_planilha, cpf):
#     """
#     Captura dados gerais (Conta Corrente, Fundo de Investimento e Margem)
#     """
    
#     filter_dict = info_planilha[cpf]['Resumo_Totais']
#     all_data = []
#     for i in filter_dict:
#         df1 = pd.DataFrame(i, index=[0])
#         all_data.append(df1)

#     df = pd.concat(all_data, axis=0)
#     df.EndPositionValue = pd.to_numeric(df.EndPositionValue)
#     return df


# def get_fundos_btg(info_planilha, cpf, cliente_pl):
#     """
#     Captura dados de fundos da API do BTG
#     """

#     filter_dict = info_planilha[cpf]['Fundos']
#     all_data = []
#     for i in filter_dict:
#         df1 = pd.DataFrame(i['Fund'], index=[0])
#         df2 = []
#         if len(i['Acquisition']) > 1:
#             for value in i['Acquisition']:
#                 df2.append(pd.DataFrame(value, index=[0]))
#             df2 = pd.concat(df2, axis=0)
#         else:
#             df2 = pd.DataFrame(i['Acquisition'])
        
#         df1['NetAssetValue'] = sum(pd.to_numeric(df2['NetAssetValue']))
#         all_data.append(df1)
    
#     df = pd.concat(all_data, axis=0)
#     df['pcts'] = df.NetAssetValue.apply(lambda x: pd.to_numeric(x)/pd.to_numeric(cliente_pl))
#     df.FundCNPJCode = df.FundCNPJCode.apply(
#            lambda x: str(x[0:2])+'.'+str(x[2:5])+'.'+str(x[5:8])+'/'+str(x[8:12])+'-'+str(x[12:14]))
 
#     return df


# def get_avista_btg(info_planilha, cpf):
    
#     """
#     Captura dados de renda variavel da API do BTG
#     """

#     filter_dict = info_planilha[cpf]['RV']
#     all_data = []
#     for i in filter_dict:
        
#         if len(filter_dict) == 1:
#             df = pd.DataFrame(i['StockPositions'])
#             df['Value'] = pd.to_numeric(df.PrevClose) * pd.to_numeric(df.Quantity)
        
#         else:
#             df1 = pd.DataFrame(i['StockPositions'], index=[0])
#             df1['Value'] = pd.to_numeric(df1.PrevClose) * pd.to_numeric(df1.Quantity)
#             all_data.append(df1)
    
#     if len(filter_dict) > 1:
#         df = pd.concat(all_data, axis=0)
    
#     df = df.rename(columns={'Value':  'financeiroLiquido'})
    
#     return df


# def get_rendafixa_btg(info_planilha, cpf):
#     """
#     Captura dados de previdencia da API do BTG
#     """
    
#     filter_dict = info_planilha[cpf]['RF']
#     all_data = []
#     for i in filter_dict:
#         df1 = pd.DataFrame(i, index=[0])
#         df1['GrossValue'] = pd.to_numeric(df1.GrossValue)
#         all_data.append(df1)

#     df = pd.concat(all_data, axis=0)
    
#     return df


# def get_previ_btg(info_planilha, cpf):
#     """
#     Captura dados de previdencia da API do BTG
#     """
    
#     filter_dict = info_planilha[cpf]['Prev']
#     all_data = []
#     for i in filter_dict:
#         df1 = pd.DataFrame(i['Positions'], index=[0])
#         df2 = []
#         if len(i['Acquisition']) > 1:
#             for value in i['Acquisition']:
#                 df2.append(pd.DataFrame(value, index=[0]))
#             df2 = pd.concat(df2, axis=0)
#         else:
#             df2 = pd.DataFrame(i['Acquisition'])
        
#         df1['GrossAssetValue'] = sum(pd.to_numeric(df2['GrossAssetValue']))
#         all_data.append(df1)
    
#     df = pd.concat(all_data, axis=0)
    
#     return df



# def data_btg_cliente(info_planilha) -> dict:
#     """
#     Capturar todos os dados de uma vez so, de todas as contas vinculadas ao BTG
#     """
    
#     funds, rf, rv, previ = [None]*4
    
#     btg_info_pos = {}
#     for k,v in info_planilha.items():
        
#         # n. conta
#         # btg_info_pos[k] = {}
        
#         filter_dict = info_planilha[k]
#         df = pd.DataFrame.from_dict(filter_dict, orient='index')
        
#         # teste: chave como nome
#         name = list(df.loc['Nome'])[0]
       
#         btg_info_pos[name] = {}
#         btg_info_pos[name]['infos'] = df.iloc[0:5,:]
        
#         # cc, fundos e margem
#         resumo = get_resumos_btg(info_planilha, k)
#         btg_info_pos[name]['resumo'] = resumo
        
#         try:
#             # info fundos
#             funds = get_fundos_btg(info_planilha, k, list(df.loc['PL'])[0])
#             btg_info_pos[name]['fundos'] = funds
#         except:
#             # print(f"Não há fundos para {list(df.loc['Nome'])[0]}")
#             pass
        
#         try:
#             # dados de renda fixa
#             rf = get_rendafixa_btg(info_planilha, k)
#             rf.reset_index(drop=True, inplace=True)
#             # handle acquisitions
#             for index in rf.index:
#                 open_data = list(rf.loc[index,'Acquisitions'].values())
#                 rf.loc[index,'ytm'] = pd.to_numeric(open_data[2])
#                 rf.loc[index,'cost_price'] = pd.to_numeric(open_data[4])
#                 rf.loc[index,'initial_pos'] = pd.to_numeric(open_data[5])
            
#             cols = ['Quantity', 'Price', 'IncomeTax', 'IOFTax', 'NetValue']
#             rf[cols] = rf[cols].apply(pd.to_numeric, errors='coerce', downcast='float')
#             btg_info_pos[name]['rf'] = rf
#         except:
#             # print(f"Não há fundos para {list(df.loc['Nome'])[0]}")
#             pass
        
#         try:
#             # dados de renda variavel
#             rv = get_avista_btg(info_planilha, k)
#             rv['AveragePrice'] = rv['AveragePrice'].apply(lambda x: pd.to_numeric(x['Price']))
#             cols = ['Quantity', 'MarketPrice', 'PrevClose']
#             rv[cols] = rv[cols].apply(pd.to_numeric, errors='coerce', downcast='float')
#             btg_info_pos[name]['rv'] = rv
#         except:
#             # print(f"Não há fundos para {list(df.loc['Nome'])[0]}")
#             pass
        
#         try:
#             # dados de renda variavel
#             previ = get_previ_btg(info_planilha, k)
#             btg_info_pos[name]['previ'] = previ
#         except:
#             # print(f"Não há fundos para {list(df.loc['Nome'])[0]}")
#             pass
    
#     return btg_info_pos
        


# # token = get_token_btg()
