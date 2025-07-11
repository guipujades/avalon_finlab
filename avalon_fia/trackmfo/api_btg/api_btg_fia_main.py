"""
Explicacao da Funcao fund_data

    Proposito: A funcao fund_data e projetada para obter informacoes sobre o patrimonio liquido de um fundo da API da BTG Pactual. 
    Ela pode buscar dados em dois formatos diferentes, excel ou xml, dependendo do valor passado para o parametro find_type.

    Parametros:
        find_type: Aceita dois valores, 'excel' ou 'xml', para determinar o formato dos dados a serem recuperados.

    Logica:

        Formato Excel:
            Utiliza um loop while para tentar obter os dados do portfolio para dias anteriores ate que os dados sejam encontrados.
            Utiliza a funcao read_xls para ler os dados do arquivo Excel.
            Retorna o valor do patrimonio liquido (PL) encontrado.

        Formato XML:
            Utiliza um loop while similar para obter dados em formato XML.
            Utiliza a funcao read_xml para analisar e extrair os dados do XML.
            Retorna os dados extraidos, incluindo o DataFrame, os dados XML, e o cabecalho.

Explicacao do Bloco if __name__ == "__main__"

    Proposito: Este bloco e executado apenas quando o script e executado diretamente, e nao quando importado como um modulo. 
    Ele e usado para autenticar e realizar chamadas principais da API.

    Processo:
        Carrega as configuracoes da API a partir de um arquivo JSON.
        Obtem um token de acesso para a API.
        Recupera informacoes principais do FIA usando a funcao fia_main_info.
        Solicita ao usuario uma data para pesquisa dos dados de carteira em formato Excel.
        Envia uma solicitacao para a API para obter dados da carteira para a data especificada e analisa os dados.
        Realiza outra chamada para obter e analisar dados da carteira em formato XML.

"""

import sys
import json
from pathlib import Path
from datetime import datetime
from datetime import timedelta
import pandas as pd


def sys_path(choose_path):
    sys.path.append(str(choose_path))

home = Path.home()
main_path = Path(home, 'Documents/GitHub/avaloncapital')
api_btg = Path(home, 'Documents/GitHub/avaloncapital/api_btg')
path_list = [main_path, api_btg]

if str(api_btg) not in sys.path:
    for path in path_list:
        sys_path(path)


from api_btg_fia_utils import auth_apiBTG, fia_main_info, portfolio_api, read_xls, read_xml


def fund_data(find_type='xml'):
    """
   Recupera dados do fundo da API da BTG Pactual, buscando o patrimonio liquido (PL)
   em formato Excel ou XML, de acordo com o parametro `find_type`.

   Args:
       find_type (str, opcional): O tipo de formato para buscar os dados. Pode ser 'xml' ou 'excel'. 
       O padrao e 'xml'.

   Returns:
       tuple: Se `find_type` for 'xml', retorna uma tupla contendo:
           - df_xml (pandas.DataFrame): Um DataFrame contendo os dados XML analisados.
           - data_xml (list): Uma lista de dicionarios representando dados XML extraidos.
           - header (dict): Um dicionario contendo informacoes do cabecalho.
       
       float: Se `find_type` for 'excel', retorna o valor do patrimonio liquido (PL) encontrado.
   """
    
    json_path = Path.home() / 'Desktop' / 'api_btg_info.json'
    with open(json_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Token de acesso
    token, data = auth_apiBTG(config)
    
    if find_type == 'excel':
        # Carteira xls
        counter = -1
        df = pd.DataFrame()
        while len(df) == 0:
            counter+=1
            print(f'Voltando {counter} dias para obter PL...')
            date_ref = datetime.today() - timedelta(days=counter)
            formt_time = datetime.strftime(date_ref, format='%Y-%m-%d')
            response_portfolio = portfolio_api(token, data, start_date=formt_time, end_date=formt_time, type_report=10, page_size=100)
            df = read_xls(response_portfolio)
        
        # Encontrar PL do fundo
        print(f'PL encontrado para o dia {formt_time}')
        index_pl = df.iloc[:,0]
        index_pl = list(index_pl[index_pl=='Patrimonio'].index)[0]
        pl = df.iloc[index_pl+1,0]
        
        return pl
    
    elif find_type == 'xml':
        # Carteira xml
        counter = -1
        df_xml = pd.DataFrame()
        while len(df_xml) == 0:
            counter+=1
            print(f'Voltando {counter} dias para obter PL...')
            date_ref = datetime.today() - timedelta(days=counter)
            formt_time = datetime.strftime(date_ref, format='%Y-%m-%d')
            response_portfolio = portfolio_api(token, data, start_date=formt_time, end_date=formt_time, type_report=3, page_size=100)
            
            content_type = response_portfolio.headers.get('Content-Type')
            if 'application/octet-stream' in content_type or 'application/zip' in content_type:
                df_xml, data_xml, header = read_xml(response_portfolio)               
            else:
                print('Erro na captura do arquivo xml. O formato não é compatível...')
            
        return df_xml, data_xml, header
    

if __name__ == "__main__":
    
    json_path = Path.home() / 'Desktop' / 'api_btg_info.json'
    with open(json_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Token de acesso
    token, data = auth_apiBTG(config)
    
    # Dados principais FIA
    info_fia = fia_main_info(token, data)
    
    # Carteira xls
    print('Selecione a data para pesquisa:')
    date_ref = input()
    response_portfolio = portfolio_api(token, data, start_date=date_ref, end_date=date_ref, type_report=10, page_size=100)
    df = read_xls(response_portfolio)
    
    # Encontrar PL do fundo
    index_pl = df.iloc[:,0]
    index_pl = list(index_pl[index_pl=='Patrimonio'].index)[0]
    pl = df.iloc[index_pl+1,0]
    
    # Carteira xml
    response_portfolio = portfolio_api(token, data, start_date='2024-08-02', end_date='2024-08-02', type_report=3, page_size=100)
    df_xml, data_xml, header = read_xml(response_portfolio)

    









