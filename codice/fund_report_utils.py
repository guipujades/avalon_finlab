import os
import time
import json
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from pathlib import Path
from scipy.stats import norm
import base64
from io import BytesIO
import requests
import re

import tempfile
import zipfile
import xml.etree.ElementTree as ET
import MetaTrader5 as mt5



def calculate_PnL_averagePrices(df):
    portfolio = {}
    df['P&L'] = 0.0
    df['average_price'] = 0.0
    
    for index, row in df.iterrows():
        ticker = row['ticker']
        quantity = row['quantidade']
        price = row['preco']
        financial = quantity * price
        
        # Inicializar o ticker no portfólio, se não existir
        if ticker not in portfolio:
            portfolio[ticker] = {
                'flag': 1 if len(ticker) <= 6 else 2,  # Ações ou opções
                'quantity': 0,
                'total_cost': 0,
                'average_price': 0.0,
                'short_selling': False
            }
        
        if row['pos'] == 'C':  # Compra
            if portfolio[ticker]['quantity'] < 0:  # Se estava vendido
                # Calcular P&L do short antes de cobrir
                pnl = (portfolio[ticker]['average_price'] - price) * min(abs(portfolio[ticker]['quantity']), quantity)
                df.at[index, 'P&L'] = pnl
            
            # Atualizar posição
            portfolio[ticker]['quantity'] += quantity
            
            if portfolio[ticker]['quantity'] >= 0:  # Se virou long ou zerou
                if portfolio[ticker]['quantity'] == 0:
                    portfolio[ticker]['total_cost'] = 0
                    portfolio[ticker]['average_price'] = 0
                    portfolio[ticker]['short_selling'] = False
                else:
                    portfolio[ticker]['total_cost'] = portfolio[ticker]['quantity'] * price
                    portfolio[ticker]['average_price'] = price
                    portfolio[ticker]['short_selling'] = False
            
        elif row['pos'] == 'V':  # Venda
            if portfolio[ticker]['quantity'] <= 0:  # Já está vendido ou zerado
                portfolio[ticker]['quantity'] += quantity  # quantity já é negativo
                portfolio[ticker]['total_cost'] = portfolio[ticker]['quantity'] * price
                portfolio[ticker]['average_price'] = price
                portfolio[ticker]['short_selling'] = True
            else:  # Está comprado
                # Calcular P&L
                pnl = (price - portfolio[ticker]['average_price']) * min(portfolio[ticker]['quantity'], abs(quantity))
                df.at[index, 'P&L'] = pnl
                
                # Atualizar posição
                portfolio[ticker]['quantity'] += quantity  # quantity já é negativo
                
                if portfolio[ticker]['quantity'] <= 0:  # Se virou short ou zerou
                    if portfolio[ticker]['quantity'] == 0:
                        portfolio[ticker]['total_cost'] = 0
                        portfolio[ticker]['average_price'] = 0
                        portfolio[ticker]['short_selling'] = False
                    else:
                        portfolio[ticker]['total_cost'] = portfolio[ticker]['quantity'] * price
                        portfolio[ticker]['average_price'] = price
                        portfolio[ticker]['short_selling'] = True
        
        df.at[index, 'average_price'] = portfolio[ticker]['average_price']
    
    return portfolio, df

def first_pos_fia():
    # first_positions = Path(Path.home(), 'Documents', 'GitHub', 'database', 'Carteira_AVALON_FIA_21_06_2024.xlsx')
    # first_positions = Path(Path.home(), 'Documents', 'GitHub', 'database', 'Carteira_AVALON_FIA_31_10_2024.xlsx')
    first_positions = Path(Path.home(), 'Documents', 'GitHub', 'database', 'carteira_comp', 'Carteira_AVALON_FIA_31_10_2024.xlsx')
    
    # file_path = Path(Path.home(), 'Downloads', 'FD40921027000131_20241031_20241101051313_AVALON_FIA.xml')
    # df = parse_principal_xml(file_path)

    df_firstpos = pd.read_excel(first_positions)
    
    # Selecionar ativos e precos
    loc_stocks = list(df_firstpos[df_firstpos.iloc[:,0]=='Departamento'].index)[0]
    stocks_df = df_firstpos.iloc[loc_stocks + 1:].dropna(how='all').reset_index(drop=True)
    loc_end = list(stocks_df[stocks_df.iloc[:,0]=='Compromissada Over'].index)[0]
    stocks_df = stocks_df.iloc[0:loc_end,:]
    
    stocks_df = stocks_df.iloc[:, 3:7]
    stocks_df.columns = ['ticker', 'quantidade', 'preco', 'financeiro']
    stocks_df['pos'] = np.where(stocks_df['quantidade'] > 0, 'C', 'V')
    stocks_df['data'] = pd.to_datetime('2024-10-31')
    stocks_df['nome_cia'] = 'first_ops'
    stocks_df = stocks_df[['pos', 'nome_cia', 'quantidade', 'preco', 'financeiro', 'ticker', 'data']]
    
    return stocks_df

def run_manager_xml():

    df_firstpos = first_pos_fia()
    df_ops = run_xmls()

    df = pd.concat([df_firstpos, df_ops])
    df['ticker'] = df['ticker'].str.strip()
    df.reset_index(inplace=True, drop=True)
    
    # Retirei adjustments para dar um reboot nos dados
    # df = adjustments(df)
    df = df.sort_values('data')
    
    # Conferencia de posicoes
    df['quantidade'] = np.where((df['pos'] == 'V') & (df['quantidade'] > 0), df['quantidade'] * -1, df['quantidade'])
    
    portfolio, df = calculate_PnL_averagePrices(df)
    
    return portfolio, df

def auth_apiBTG(config):
    """
    Autentica-se com a API da BTG Pactual e obtem um token de acesso.

    Args:
        config (dict): Um dicionario contendo as seguintes chaves:
            - 'CLIENT_ID' (str): O ID do cliente para autenticacao da API.
            - 'CLIENT_SECRET' (str): O segredo do cliente para autenticacao da API.
            - 'GRANT_TYPE' (str): O tipo de concessao para autenticacao da API.

    Returns:
        tuple: Uma tupla contendo o token de acesso (str) e os dados (dict) usados para autenticacao.
    """
    
    # Credenciais
    client_id = 'guilherme magalhães'
    client_secret = 'Cg21092013PM#'
    grant_type = 'client_credentials'

    # URL de autenticação e relatorios
    auth_url = 'https://funds.btgpactual.com/connect/token'
   
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    # Dados para a autenticacao
    data = {
        'grant_type': grant_type,
        'client_id': client_id,
        'client_secret': client_secret,
    }
    
    # Token
    time.sleep(10)
    response = requests.post(auth_url, headers=headers, data=data)
    
    # available_data = response.json()
    token = response.json().get('access_token')
    
    return token, data

def fia_main_info(token, data):
    
    # Info principais FIA
    report_url = 'https://funds.btgpactual.com/reports/Fund'
    ticket_base_url = 'https://funds.btgpactual.com/reports/Ticket'

    payload = json.dumps({
        "contract": {},
        "webhookEndpoint": "string"
    })
    
    # Headers
    report_headers = {
        'Content-Type': 'application/json',
        'X-SecureConnect-Token': token
    }
    
    # Requisicao relatorio
    response_report = requests.post(report_url, headers=report_headers, data=payload)
    ticket = response_report.json().get('ticket')
    ticket_url = f'{ticket_base_url}?ticketId={ticket}'
    
    # Headers para ticket
    ticket_headers = {
        'Content-Type': 'application/json',
        'X-SecureConnect-Token': token
    }
    
    # Dados FIA Avalon
    time.sleep(10)
    response_ticket = requests.get(ticket_url, headers=ticket_headers)
    info = response_ticket.json()
    
    return info

def portfolio_api(token, data, start_date, end_date, type_report, page_size):
    
    # Portfolio
    report_url = 'https://funds.btgpactual.com/reports/Portfolio'
    ticket_base_url = 'https://funds.btgpactual.com/reports/Ticket'
    scope = 'reports.position'
    
    data['scope'] = scope
    payload = json.dumps({
        'contract': {
            'startDate': start_date,
            'endDate': end_date,
            'typeReport': type_report,
            'fundName': 'AVALON FIA'
        },
        
        'pageSize': page_size,
        'webhookEndpoint': 'string'
    })
    
    # Headers 
    report_headers = {
        'Content-Type': 'application/json',
        'X-SecureConnect-Token': token
    }
    
    # Requisicao 
    response_report = requests.post(report_url, headers=report_headers, data=payload)
    
    # Requisicao de relatorio
    ticket = response_report.json().get('ticket')
    ticket_url = f'{ticket_base_url}?ticketId={ticket}'
    
    # Headers
    ticket_headers = {
        'Content-Type': 'application/json',
        'X-SecureConnect-Token': token
    }
    
    # Carteira Avalon
    time.sleep(10)
    response_ticket = requests.get(ticket_url, headers=ticket_headers)
    
    return response_ticket

def parse_xml(root_or_path):
    """
    Analisa um arquivo XML ou um objeto Element já carregado
    
    Args:
        root_or_path: Caminho do arquivo XML ou objeto Element já carregado
        
    Returns:
        tuple: (DataFrame com dados, dicionário de dados XML, cabeçalho)
    """
    import os
    import xml.etree.ElementTree as ET
    import pandas as pd
    
    # Verificar se o input é um caminho de arquivo ou um objeto Element
    if isinstance(root_or_path, (str, bytes, os.PathLike)):
        # É um caminho de arquivo, precisa ser carregado
        tree = ET.parse(root_or_path)
        root = tree.getroot()
    else:
        # Assume que já é um objeto Element
        root = root_or_path
    
    data_xml = []

    fundo = root.find('fundo')
    header = fundo.find('header')

    # Extrair dados do header
    header_data = {
        'isin': header.find('isin').text,
        'cnpj': header.find('cnpj').text,
        'nome': header.find('nome').text,
        'dtposicao': header.find('dtposicao').text,
        'nomeadm': header.find('nomeadm').text,
        'cnpjadm': header.find('cnpjadm').text,
        'nomegestor': header.find('nomegestor').text,
        'cnpjgestor': header.find('cnpjgestor').text,
        'nomecustodiante': header.find('nomecustodiante').text,
        'cnpjcustodiante': header.find('cnpjcustodiante').text,
        'valorcota': float(header.find('valorcota').text),
        'quantidade': float(header.find('quantidade').text),
        'patliq': float(header.find('patliq').text),
        'valorativos': float(header.find('valorativos').text),
        'valorreceber': float(header.find('valorreceber').text),
        'valorpagar': float(header.find('valorpagar').text),
        'vlcotasemitir': float(header.find('vlcotasemitir').text),
        'vlcotasresgatar': float(header.find('vlcotasresgatar').text),
        'codanbid': header.find('codanbid').text,
        'tipofundo': header.find('tipofundo').text,
        'nivelrsc': header.find('nivelrsc').text
    }
    
    # Extrair dados dos títulos públicos
    for titpublico in fundo.findall('titpublico'):
        data_xml.append({
            'tipo': 'titpublico',
            'isin': titpublico.find('isin').text,
            'codativo': titpublico.find('codativo').text,
            'cusip': titpublico.find('cusip').text,
            'dtemissao': titpublico.find('dtemissao').text,
            'dtoperacao': titpublico.find('dtoperacao').text,
            'dtvencimento': titpublico.find('dtvencimento').text,
            'qtdisponivel': int(titpublico.find('qtdisponivel').text),
            'qtgarantia': int(titpublico.find('qtgarantia').text),
            'depgar': int(titpublico.find('depgar').text),
            'pucompra': float(titpublico.find('pucompra').text),
            'puvencimento': float(titpublico.find('puvencimento').text),
            'puposicao': float(titpublico.find('puposicao').text),
            'puemissao': float(titpublico.find('puemissao').text),
            'principal': float(titpublico.find('principal').text),
            'tributos': float(titpublico.find('tributos').text),
            'valorfindisp': float(titpublico.find('valorfindisp').text),
            'valorfinemgar': float(titpublico.find('valorfinemgar').text),
            'coupom': float(titpublico.find('coupom').text),
            'indexador': titpublico.find('indexador').text,
            'percindex': int(titpublico.find('percindex').text),
            'caracteristica': titpublico.find('caracteristica').text,
            'percprovcred': int(titpublico.find('percprovcred').text),
            'classeoperacao': titpublico.find('classeoperacao').text,
            'idinternoativo': titpublico.find('idinternoativo').text,
            'nivelrsc': titpublico.find('nivelrsc').text
        })

    # Extrair dados das ações
    for acao in fundo.findall('acoes'):
        data_xml.append({
            'tipo': 'acoes',
            'isin': acao.find('isin').text,
            'cusip': acao.find('cusip').text,
            'codativo': acao.find('codativo').text,
            'qtdisponivel': int(acao.find('qtdisponivel').text),
            'lote': int(acao.find('lote').text),
            'qtgarantia': int(acao.find('qtgarantia').text),
            'valorfindisp': float(acao.find('valorfindisp').text),
            'valorfinemgar': float(acao.find('valorfinemgar').text),
            'tributos': float(acao.find('tributos').text),
            'puposicao': float(acao.find('puposicao').text),
            'percprovcred': int(acao.find('percprovcred').text),
            'tpconta': int(acao.find('tpconta').text),
            'classeoperacao': acao.find('classeoperacao').text,
            'dtvencalug': acao.find('dtvencalug').text,
            'txalug': float(acao.find('txalug').text),
            'cnpjinter': acao.find('cnpjinter').text
        })

    # Extrair dados das provisões
    for provisao in fundo.findall('provisao'):
        data_xml.append({
            'tipo': 'provisao',
            'codprov': provisao.find('codprov').text,
            'credeb': provisao.find('credeb').text,
            'dt': provisao.find('dt').text,
            'valor': float(provisao.find('valor').text)
        })

    df = pd.DataFrame(data_xml)

    return df, data_xml, header_data

def read_xml(response_portfolio):
    """
    Lê e processa um arquivo XML da resposta da API
    
    Args:
        response_portfolio: Resposta da API contendo o XML
        
    Returns:
        tuple: (DataFrame de dados, dicionário de dados XML, cabeçalho)
    """
    # Salvar o conteúdo em um arquivo temporário
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.bin')
    temp_file.write(response_portfolio.content)
    temp_file.close()
    print(f"Conteúdo salvo como {temp_file.name}")
    
    try:
        # Carregar o XML usando ElementTree
        tree = ET.parse(temp_file.name)
        root = tree.getroot()
        
        # Processamento direto do XML sem chamar parse_xml
        data_xml = []

        fundo = root.find('fundo')
        if fundo is None:
            print("Estrutura XML não encontrada: tag 'fundo' ausente")
            return pd.DataFrame(), {}, {}
            
        header = fundo.find('header')
        if header is None:
            print("Estrutura XML não encontrada: tag 'header' ausente")
            return pd.DataFrame(), {}, {}

        # Extrair dados do header
        header_data = {}
        for child in header:
            # Tentar converter para float para campos numéricos
            try:
                header_data[child.tag] = float(child.text)
            except (ValueError, TypeError):
                header_data[child.tag] = child.text
                
        # Extrair dados dos títulos públicos
        for titpublico in fundo.findall('titpublico'):
            item = {'tipo': 'titpublico'}
            for field in titpublico:
                try:
                    # Tentar converter para números quando apropriado
                    if field.tag in ['qtdisponivel', 'qtgarantia', 'depgar', 'percindex', 'percprovcred']:
                        item[field.tag] = int(field.text)
                    elif field.tag in ['pucompra', 'puvencimento', 'puposicao', 'puemissao', 
                                     'principal', 'tributos', 'valorfindisp', 'valorfinemgar', 'coupom']:
                        item[field.tag] = float(field.text)
                    else:
                        item[field.tag] = field.text
                except (ValueError, TypeError):
                    item[field.tag] = field.text
            data_xml.append(item)

        # Extrair dados das ações
        for acao in fundo.findall('acoes'):
            item = {'tipo': 'acoes'}
            for field in acao:
                try:
                    # Tentar converter para números quando apropriado
                    if field.tag in ['qtdisponivel', 'lote', 'qtgarantia', 'percprovcred', 'tpconta']:
                        item[field.tag] = int(field.text)
                    elif field.tag in ['valorfindisp', 'valorfinemgar', 'tributos', 'puposicao', 'txalug']:
                        item[field.tag] = float(field.text)
                    else:
                        item[field.tag] = field.text
                except (ValueError, TypeError):
                    item[field.tag] = field.text
            data_xml.append(item)

        # Extrair dados das provisões
        for provisao in fundo.findall('provisao'):
            item = {'tipo': 'provisao'}
            for field in provisao:
                try:
                    # Tentar converter para números quando apropriado
                    if field.tag == 'valor':
                        item[field.tag] = float(field.text)
                    else:
                        item[field.tag] = field.text
                except (ValueError, TypeError):
                    item[field.tag] = field.text
            data_xml.append(item)

        # Criar DataFrame
        df = pd.DataFrame(data_xml)
        
        return df, data_xml, header_data
        
    except ET.ParseError as e:
        print(f"Erro ao analisar o arquivo XML: {e}")
        return pd.DataFrame(), {}, {}
    except Exception as e:
        print(f"Erro inesperado ao processar o XML: {e}")
        return pd.DataFrame(), {}, {}
    
def read_xls(response_portfolio):
    content_type = response_portfolio.headers.get('Content-Type')
    if 'application/octet-stream' in content_type or 'application/zip' in content_type:
        # Salvar conteúdo binário em um arquivo temporário
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        temp_zip.write(response_portfolio.content)
        temp_zip.close()
        print(f"Conteúdo salvo como {temp_zip.name}")
    
        # Descompactar o arquivo ZIP e identificar o arquivo Excel
        with zipfile.ZipFile(temp_zip.name, 'r') as zip_ref:
            extracted_files = zip_ref.namelist()
            zip_ref.extractall(tempfile.gettempdir())
    
            # Procurar o arquivo Excel principal
            excel_file_path = None
            for file in extracted_files:
                if file.endswith('xl/worksheets/sheet1.xml'):
                    excel_file_path = os.path.join(tempfile.gettempdir(), 'xl', 'worksheets', 'sheet1.xml')
                    break
    
            if excel_file_path:
                # Reconstruir o caminho do arquivo Excel
                reconstructed_excel_path = os.path.join(tempfile.gettempdir(), 'reconstructed.xlsx')
                with zipfile.ZipFile(reconstructed_excel_path, 'w') as new_zip:
                    for file in extracted_files:
                        new_zip.write(os.path.join(tempfile.gettempdir(), file), file)
                # Ler o arquivo Excel com pandas
                df = pd.read_excel(reconstructed_excel_path, engine='openpyxl')

            else:
                print('Arquivo Excel não encontrado...')
                
            return df
    
    else:
        print('Resposta não condizente com captura... Conteúdo:')
        # print(response_portfolio.text)
        return pd.DataFrame()


def initialize_mt5():
    """
    Inicializa conexão com MetaTrader5
    """
    mt5_path = Path('C:/', 'Program Files', 'Rico - MetaTrader 5', 'terminal64.exe')
    initialize(user_path=str(mt5_path), server='GenialInvestimentos-PRD', login=156691, key='Avca@1985')
    print("MT5 initialized")
    
def initialize(user_path, server, login, key):
    """
    Inicializa conexão com o terminal MetaTrader 5
    
    Args:
        user_path (str): Caminho para o executável do MT5
        server (str): Servidor de trading
        login (int): Login da conta
        key (str): Senha da conta
    """
    if not mt5.initialize(path=user_path, login=login, server=server, password=key):
        print("initialize() failed, error code =", mt5.last_error())
        quit()
    else:
        print(f"Connected to account #{login}")

def prepare_symbol(ticker):
    """
    Prepara o símbolo para consulta no MT5
    
    Args:
        ticker (str): Símbolo a ser preparado
    """
    symbols = mt5.symbols_get(ticker)
    if len(symbols) == 0:
        mt5.symbol_select(ticker, True)
        
def get_prices_mt5(symbol, n=100, timeframe=None):
    """
    Obtém preços históricos do MT5
    
    Args:
        symbol (str): Símbolo para obter os preços
        n (int): Número de barras para obter
        timeframe: Timeframe MT5 para obter os preços
        
    Returns:
        DataFrame: Preços históricos
    """
    if timeframe is None:
        timeframe = mt5.TIMEFRAME_D1
        
    # Obter dados
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n)
    
    if rates is None or len(rates) == 0:
        print(f"No data for {symbol}")
        return pd.DataFrame()
    
    # Converter para DataFrame
    rates_frame = pd.DataFrame(rates)
    rates_frame['time'] = pd.to_datetime(rates_frame['time'], unit='s')
    
    # Renomear colunas
    rates_frame = rates_frame.rename(columns={
        'time': 'Data', 'open': 'Abertura', 'high': 'Máxima', 
        'low': 'Mínima', 'close': 'Fechamento', 'tick_volume': 'Volume'
    })
    
    # Definir índice
    rates_frame = rates_frame.set_index('Data')
    
    return rates_frame

def get_real_time_prices(portfolio):
    """
    Obtém preços em tempo real para os ativos no portfólio
    
    Args:
        portfolio (dict): Portfólio de ativos
        
    Returns:
        tuple: (dict de preços atuais, dict de DataFrames de preços históricos)
    """
    prices_full = {}
    prices = {}
    
    ex_stocks = []
        
    for ticker in portfolio.keys():
        
        if ticker in ex_stocks:
            continue
        
        if portfolio[ticker]['quantity'] > 0 or (portfolio[ticker]['quantity'] < 0 and portfolio[ticker].get('short_selling', False) == True):
            
            prepare_symbol(ticker)
            
            # Caso especial para ISAE4
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
            
            if df_.empty:
                continue
                
            df_['Volume_Financeiro'] = ((df_['Máxima'] + df_['Mínima']) / 2) * df_['Volume']
            df_ = df_[['Abertura', 'Máxima', 'Mínima', 'Fechamento', 'Volume_Financeiro']]
            df_.columns = ['Abertura', 'Maxima', 'Minima', 'Fechamento', 'Volume_Financeiro']
            df_.index.name = 'Data'
            prices_full[ticker] = df_
            last_price = df_.iloc[-1]['Fechamento']
            prices[ticker] = last_price
            
    return prices, prices_full

def get_real_time_prices_options_stocks(df_):
    """
    Obtém preços em tempo real para ativos subjacentes de opções
    
    Args:
        df_ (DataFrame): DataFrame com opções
        
    Returns:
        dict: Preços dos ativos subjacentes
    """
    prices = {}
    for ticker in list(df_.stock.unique()):
        prepare_symbol(ticker)
        df_prices = get_prices_mt5(symbol=ticker, n=100, timeframe=mt5.TIMEFRAME_D1)
        
        if df_prices.empty:
            continue
            
        df_prices['Volume_Financeiro'] = ((df_prices['Máxima'] + df_prices['Mínima']) / 2) * df_prices['Volume']
        df_prices = df_prices[['Abertura', 'Máxima', 'Mínima', 'Fechamento', 'Volume_Financeiro']]
        df_prices.columns = ['Abertura', 'Maxima', 'Minima', 'Fechamento', 'Volume_Financeiro']
        df_prices.index.name = 'Data'
        last_price = df_prices.iloc[-1]['Fechamento']
        prices[ticker] = last_price
    return prices

def calculate_pnl(portfolio, prices):
    """
    Calcula o P&L para o portfólio com base nos preços atuais
    
    Args:
        portfolio (dict): Portfólio de ativos
        prices (dict): Preços atuais dos ativos
        
    Returns:
        dict: P&L calculado
    """
    pnl = {}
    for ticker, data in portfolio.items():
        quantity = data.get('quantity', 0)
        short_selling = data.get('short_selling', False)

        if quantity > 0 or (quantity < 0 and short_selling == True):
            current_price = prices.get(ticker, 0)
            average_price = data['average_price']
            current_value = current_price * quantity
            initial_value = average_price * quantity
            profit_loss = current_value - initial_value
            
            # Evitar divisão por zero
            percentage_change = 0
            if abs(initial_value) > 0:
                percentage_change = (profit_loss / abs(initial_value))
                
            pnl[ticker] = {
                'current_price': current_price,
                'quantity': quantity,
                'average_price': average_price,
                'current_value': current_value,
                'profit_loss': profit_loss,
                'percentage_change': percentage_change
            }
    return pnl

def calculate_var(prices, weights, time_ahead):
    """
    Calcula o Value at Risk (VaR) para o portfólio
    
    Args:
        prices (DataFrame): Preços históricos
        weights (array): Pesos dos ativos no portfólio
        time_ahead (int): Horizonte de tempo em dias
        
    Returns:
        list: VaR calculado para diferentes níveis de confiança
    """
    returns = np.log(1 + prices.pct_change()).dropna()
    
    if returns.empty:
        return [0, 0, 0]
        
    cov_matrix = returns.cov() * 252
    
    # Tratamento para matriz de covariância singular
    try:
        portfolio_std_dev = np.sqrt(weights.T @ cov_matrix @ weights)
    except:
        portfolio_std_dev = np.sqrt(np.sum(np.diag(cov_matrix) * weights**2))
    
    confidence_levels = [0.90, 0.95, 0.99]
    VaRs = []
    
    for cl in confidence_levels:
        VaR = portfolio_std_dev * norm.ppf(cl) * np.sqrt(time_ahead / 252)
        VaRs.append(round(VaR * 100, 4))
    
    return VaRs

def calculate_daily_change(prices_df):
    """
    Calcula a variação diária dos preços
    
    Args:
        prices_df (DataFrame): Preços históricos
        
    Returns:
        Series: Variação diária
    """
    if len(prices_df) < 2:
        return pd.Series(0, index=prices_df.columns)
        
    today = prices_df.iloc[-1]
    yesterday = prices_df.iloc[-2]
    change = ((today - yesterday) / yesterday) * 100
    return change

def calculate_portfolio_change_pm(df):
    """
    Calcula a variação do portfólio com base no preço médio
    
    Args:
        df (DataFrame): DataFrame com dados do portfólio
        
    Returns:
        float: Variação percentual do portfólio
    """
    initial_value = (df['average_price'] * df['quantity']).sum()
    current_value = df['current_value'].sum()
    
    if abs(initial_value) < 1e-6:
        return 0
        
    portfolio_change = (current_value / initial_value) - 1
    return portfolio_change 

def get_last_monday(prices_df):
    """
    Obtém a data da última segunda-feira nos dados
    
    Args:
        prices_df (DataFrame): Preços históricos
        
    Returns:
        Timestamp: Data da última segunda-feira
    """
    today = datetime.now().date()
    last_monday = pd.to_datetime(today - timedelta(days=today.weekday()))
    
    if prices_df.empty:
        return last_monday
        
    if last_monday not in prices_df.index:
        valid_dates = prices_df.index[prices_df.index <= last_monday]
        if len(valid_dates) > 0:
            last_monday = valid_dates[-1]
    return last_monday

def calculate_weekly_change(prices_df, weights, days=5):
    """
    Calcula a variação semanal do portfólio
    
    Args:
        prices_df (DataFrame): Preços históricos
        weights (array): Pesos dos ativos no portfólio
        days (int): Número de dias para o cálculo
        
    Returns:
        float: Variação percentual semanal
    """
    if prices_df.empty or len(prices_df) <= days:
        return 0
        
    if days == 5:  # Caso semanal padrão
        last_monday = get_last_monday(prices_df)
        try:
            prices_last_monday = prices_df.loc[last_monday]
            prices_today = prices_df.iloc[-1]
            weekly_returns = np.log(prices_today / prices_last_monday)
            portfolio_weekly_change = (weekly_returns * weights).sum() * 100
            return portfolio_weekly_change
        except:
            return 0
    else:
        # Para outros períodos, usar os últimos N dias
        returns = np.log(prices_df / prices_df.shift(1))
        if returns.empty or len(returns) < days:
            return 0
        weighted_returns = returns * weights
        portfolio_change = weighted_returns.sum(axis=1).iloc[-days:].sum() * 100
        return portfolio_change

def calculate_weeklyAssets_change(prices_df):
    """
    Calcula a variação semanal de cada ativo
    
    Args:
        prices_df (DataFrame): Preços históricos
        
    Returns:
        Series: Variação semanal por ativo
    """
    if prices_df.empty or len(prices_df) < 5:
        return pd.Series(0, index=prices_df.columns)
        
    last_monday = get_last_monday(prices_df)
    try:
        prices_last_monday = prices_df.loc[last_monday]
        prices_today = prices_df.iloc[-1]
        weekly_returns = np.log(prices_today / prices_last_monday) * 100
        return weekly_returns
    except:
        return pd.Series(0, index=prices_df.columns)

def get_first_day_of_month(prices_df):
    """
    Obtém o primeiro dia do mês nos dados
    
    Args:
        prices_df (DataFrame): Preços históricos
        
    Returns:
        Timestamp: Data do primeiro dia do mês
    """
    today = datetime.now().date()
    first_day_of_month = pd.to_datetime(today.replace(day=1))
    
    if prices_df.empty:
        return first_day_of_month
        
    if first_day_of_month not in prices_df.index:
        valid_dates = prices_df.index[prices_df.index <= first_day_of_month]
        if len(valid_dates) > 0:
            first_day_of_month = valid_dates[-1]
    return first_day_of_month

def calculate_monthlyAssets_change(prices_df):
    """
    Calcula a variação mensal de cada ativo
    
    Args:
        prices_df (DataFrame): Preços históricos
        
    Returns:
        Series: Variação mensal por ativo
    """
    if prices_df.empty or len(prices_df) < 20:
        return pd.Series(0, index=prices_df.columns)
        
    first_day_of_month = get_first_day_of_month(prices_df)
    try:
        prices_first_day = prices_df.loc[first_day_of_month]
        prices_today = prices_df.iloc[-1]
        monthly_returns = np.log(prices_today / prices_first_day) * 100
        return monthly_returns
    except:
        return pd.Series(0, index=prices_df.columns)

def save_pickle(data, path):
    """
    Salva dados em arquivo pickle
    
    Args:
        data: Dados para salvar
        path (str): Caminho do arquivo
    """
    with open(path, 'wb') as file:
        pickle.dump(data, file)

def load_pickle(path):
    """
    Carrega dados de arquivo pickle
    
    Args:
        path (str): Caminho do arquivo
        
    Returns:
        object: Dados carregados
    """
    with open(path, 'rb') as file:
        return pickle.load(file)

def find_invalid_floats(data, path='root'):
    """
    Encontra valores float inválidos (NaN, inf) nos dados
    
    Args:
        data: Dados para verificar
        path (str): Caminho atual na estrutura de dados
        
    Returns:
        list: Lista de tuplas (caminho, valor) com floats inválidos
    """
    invalid_floats = []

    if isinstance(data, dict):
        for key, value in data.items():
            invalid_floats.extend(find_invalid_floats(value, f"{path}.{key}"))
    elif isinstance(data, list):
        for index, value in enumerate(data):
            invalid_floats.extend(find_invalid_floats(value, f"{path}[{index}]"))
    elif isinstance(data, float):
        if np.isnan(data) or np.isinf(data):
            invalid_floats.append((path, data))

    return invalid_floats

def clean_data_for_json(data):
    """
    Limpa dados para conversão em JSON, substituindo valores NaN e inf
    
    Args:
        data: Dados para limpar
        
    Returns:
        object: Dados limpos
    """
    if isinstance(data, dict):
        return {k: clean_data_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_data_for_json(v) for v in data]
    elif isinstance(data, float):
        if np.isnan(data) or np.isinf(data):
            return 0.0  # Substitui NaN ou inf com 0
    return data

def dataframe_to_dict(df):
    """
    Converte DataFrame para dicionário no formato de registros
    
    Args:
        df (DataFrame): DataFrame para converter
        
    Returns:
        list: Lista de dicionários, um por linha
    """
    return df.reset_index().to_dict(orient='records')

def dataframe_to_dict_ts(df):
    """
    Converte DataFrame para dicionário, tratando timestamps
    
    Args:
        df (DataFrame): DataFrame para converter
        
    Returns:
        dict: Dicionário de listas, uma lista por coluna
    """
    # Converte todas as colunas datetime para strings
    df = df.copy()
    df.reset_index(inplace=True)
    for column in df.columns:
        if np.issubdtype(df[column].dtype, np.datetime64):
            df[column] = df[column].astype(str)
    return df.to_dict(orient='list')

def convert_timestamps_to_strings(data_dict):
    """
    Converte timestamps para strings em um dicionário
    
    Args:
        data_dict (dict): Dicionário com timestamps como chaves
        
    Returns:
        dict: Dicionário com chaves timestamp convertidas para strings
    """
    return {str(k): v for k, v in data_dict.items()}

def parse_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    data = []
    
    for evento in root.findall('evento'):
        cliente = evento.find('cliente')
        nome = cliente.find('nome').text
        cpfcnpj = cliente.find('cpfcnpj').text
        datadonegocio = evento.get('datadonegocio')
        
        for negocio in evento.findall('negocio'):
            qualificado = negocio.find('qualificado').text
            local = negocio.find('local').text
            natureza = negocio.find('natureza').text
            mercado = negocio.find('mercado').text
            isin = negocio.find('isin').text
            especificacao = negocio.find('especificacao').text
            quantidade = negocio.find('quantidade').text
            precoajuste = negocio.find('precoajuste').text
            volume = negocio.find('volume').text

            data.append({
                'nome': nome,
                'cpfcnpj': cpfcnpj,
                'qualificado': qualificado,
                'local': local,
                'natureza': natureza,
                'mercado': mercado,
                'isin': isin,
                'especificacao': especificacao,
                'quantidade': quantidade,
                'precoajuste': precoajuste,
                'volume': volume,
                'data': datadonegocio 
            })

    df = pd.DataFrame(data)
    df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')

    # Convertendo colunas numericas
    df['quantidade'] = pd.to_numeric(df['quantidade'].str.replace('.', '').str.replace(',', '.'))
    df['precoajuste'] = pd.to_numeric(df['precoajuste'].str.replace('.', '').str.replace(',', '.'))
    df['volume'] = pd.to_numeric(df['volume'].str.replace('.', '').str.replace(',', '.'))

    return df, pd.to_datetime(datadonegocio, format='%d/%m/%Y')


def identify_tickers(df, ticker_storage):
    # Ticker control
    for i in df.index:
        company_name = df.loc[i,'especificacao']

        if company_name not in ticker_storage:
            print('\n Nome de referência: {}'.format(company_name))           
            print('Ticker correto: ')
            ticker = str(input()).upper()
            ticker_storage[company_name] = ticker
            df.loc[i,'ticker'] = ticker
        else:
            df.loc[i,'ticker'] = ticker_storage[company_name]
    return df, ticker_storage


def calculate_average_prices(df):
    
    grouped = df.groupby(['ticker', 'natureza'])
    
    result = []
    
    # Iterar pelos grupos para calcular o preço médio
    for (ticker, natureza), group in grouped:
        total_quantidade = group['quantidade'].sum()
        total_volume = group['volume'].sum()
        especificacao = group['especificacao'].unique()[0]
        
        if total_quantidade != 0:
            preco_medio = total_volume / total_quantidade
        else:
            preco_medio = 0
        
        result.append({
            'ticker': ticker,
            'natureza': natureza,
            'quantidade_total': total_quantidade,
            'volume_total': total_volume,
            'preco_medio': preco_medio,
            'nome_cia': especificacao
        })
    
    return pd.DataFrame(result)

def run_xmls():
    import pickle as pkl
    from tqdm import tqdm
    
    ticker_storage = pkl.load(open(Path(Path.home(), 'Desktop', 'notas_dict.pkl'),'rb'))
    # ticker_storage['AMBEV S/A  ON  EDJ'] = 'ABEV3'
    
    # adpts
    # ticker_storage['AZZAS 2154  ON      NM'] = 'AZZA3'
    
    file_path = Path(Path.home(), 'Documents', 'GitHub', 'database', 'operacoes_fia_xml')
    all_data = []
    for item in tqdm(os.listdir(Path(file_path))):
        file_rout = Path(file_path, item)
        
        file_xml, data = parse_xml(file_rout)
        df_ops, ticker_storage = identify_tickers(file_xml, ticker_storage)
        df_ops['volume'] = abs(df_ops['volume'])
        df_handle = calculate_average_prices(df_ops)
        df_handle['data'] = data
        df_handle.columns = ['ticker', 'pos', 'quantidade', 'financeiro', 'preco', 'nome_cia', 'data']
        all_data.append(df_handle)
    
    df = pd.concat(all_data)
    pkl.dump(ticker_storage, open(Path(Path.home(), 'Desktop', 'notas_dict.pkl'), 'wb'))

    return df

def id_options(opts_id):
    """
    Identifica detalhes de opções
    
    Args:
        opts_id (list): Lista de IDs de opções
        
    Returns:
        DataFrame: DataFrame com detalhes das opções
    """
    # Obter lista de ações
    url = 'https://www.dadosdemercado.com.br/bolsa/acoes'
    try:
        tables = pd.read_html(url)
        data = tables[0]
        ativos = list(data.Ticker)
    except:
        # Fallback caso a leitura da URL falhe
        print("Falha ao ler dados de mercado, usando lista vazia")
        ativos = []
        
    # Diferenciar calls e puts
    calls = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']
    puts = ['M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X']
    
    # Funções auxiliares
    def get_data(n1, n2, string):
        return string[n1:n2].replace(' ', '')
    
    def fix_price(var):
        reg = re.compile(r'[0]{10}')
        var = reg.sub('', var)
        var = pd.to_numeric(var[-6:-2] + '.' + var[-2:])
        return var
    
    def fix_ticker(var):
        if var.startswith('ON'):
            var = '3'
        elif var.startswith('PNA'):
            var = '5'
        elif var.startswith('PNB'):
            var = '6'
        elif var.startswith('PNC'):
            var = '7'
        elif var.startswith('PND'):
            var = '8'
        elif var.startswith('PN'):
            var = '4'
        elif var.startswith('UN'):
            var = '11'
        else:
            pass
        return var
    
    # Abrir arquivo histórico B3
    home = Path.home()
    txt_path = Path(home, 'Documents', 'GitHub', 'database', 'historico_b3', 'COTAHIST_D19072024.TXT')
    
    records = []
    
    if os.path.exists(txt_path):
        try:
            df_txt = pd.read_table(txt_path, encoding='Latin-1', index_col=None, header=0)
            np_txt = (df_txt.iloc[0:-1,0]).to_numpy()
            
            for i in np_txt:
                # Filtro de opções
                ticker = get_data(12, 24, i)
                if ticker not in opts_id:
                    continue
                    
                if len(ticker) >= 8:
                    # Filtro de empresas listadas
                    nome_empresa = get_data(27, 39, i)[0:4]
                    tipo_papel = get_data(39, 49, i)
                    tipo_papel = fix_ticker(tipo_papel)
                    nome_empresa = nome_empresa + tipo_papel
                    ticker_ref = ticker[0:4] + tipo_papel
                    info = i
            
                    if nome_empresa in ativos:
                        tipo_registro = get_data(0, 2, i)
                        data_pregao = pd.to_datetime(get_data(2, 10, i), format='%Y%m%d')
                        price_exe = get_data(188,201,i)
                        strike = fix_price(price_exe)
            
                        if str(ticker[4]) in calls:
                            type_option = 'c'
                        elif ticker[4] in puts:
                            type_option = 'p'
                        else:
                            print(f'Não encontrei o tipo de opção para {ticker}')
                            continue
                        
                        data_venc = pd.to_datetime(get_data(202, 210, i), format='%Y%m%d', errors='coerce')
                        
                        # Adiciona registro à lista
                        records.append({
                            'stock': ticker_ref,
                            'ticker': ticker,
                            'tipo': type_option,
                            'vencimento': data_venc,
                            'strike': strike,
                            'info': info
                        })
        except Exception as e:
            print(f"Erro ao processar arquivo B3: {e}")
    else:
        print(f"Arquivo histórico B3 não encontrado: {txt_path}")
    
    # Se não houver registros, retornar DataFrame vazio
    if not records:
        return pd.DataFrame(columns=['stock', 'ticker', 'tipo', 'vencimento', 'strike', 'info'])
        
    # Converter para DataFrame
    df_opts = pd.DataFrame(records)
    
    return df_opts

def fund_data(find_type='xml'):
    
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
        counter = 0
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
    
    
def generate_html_report(portfolio_data):
    """
    Gera relatório HTML com os dados do portfólio
    
    Args:
        portfolio_data (dict): Dados do portfólio
        
    Returns:
        str: Caminho do arquivo HTML gerado
    """
    from pathlib import Path
    
    # Caminho para salvar o relatório
    report_path = Path.home() / 'Desktop' / 'portfolio_report.html'
    
    # Template HTML básico - Usando double braces {{}} para escapar chaves no CSS
    html_template = """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Relatório de Portfólio - AVALON FIA</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                color: #333;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            .header {{
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 5px;
                margin-bottom: 20px;
                border: 1px solid #ddd;
            }}
            .card {{
                background-color: white;
                border-radius: 5px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.12);
                border: 1px solid #ddd;
            }}
            .summary {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 15px;
            }}
            .summary-item {{
                padding: 15px;
                border-radius: 5px;
                background-color: #f8f9fa;
                border: 1px solid #ddd;
            }}
            .positive {{
                color: green;
            }}
            .negative {{
                color: red;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
            }}
            th, td {{
                padding: 10px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }}
            th {{
                background-color: #f8f9fa;
                font-weight: bold;
            }}
            tr:hover {{
                background-color: #f5f5f5;
            }}
            .section-title {{
                margin-top: 30px;
                margin-bottom: 15px;
                border-bottom: 2px solid #ddd;
                padding-bottom: 5px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Relatório de Portfólio - AVALON FIA</h1>
                <p>Data: {data} - Gerado em: {current_time}</p>
            </div>
            
            <div class="card">
                <h2>Resumo do Fundo</h2>
                <div class="summary">
                    <div class="summary-item">
                        <h3>Patrimônio Líquido</h3>
                        <p>R$ {pl_format}</p>
                    </div>
                    <div class="summary-item">
                        <h3>Cota</h3>
                        <p>R$ {cota}</p>
                    </div>
                    <div class="summary-item">
                        <h3>A Receber</h3>
                        <p>R$ {receber_format}</p>
                    </div>
                    <div class="summary-item">
                        <h3>A Pagar</h3>
                        <p>R$ {pagar_format}</p>
                    </div>
                    <div class="summary-item">
                        <h3>Enquadramento</h3>
                        <p>{enquadramento:.2f}%</p>
                    </div>
                    <div class="summary-item">
                        <h3>Limite Derivativos</h3>
                        <p>{limits_der:.2f}%</p>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>Performance</h2>
                <div class="summary">
                    <div class="summary-item">
                        <h3>Variação Total</h3>
                        <p class="{portfolio_change_class}">{portfolio_change:.2f}%</p>
                    </div>
                    <div class="summary-item">
                        <h3>Variação Ações</h3>
                        <p class="{portfolio_change_stocks_class}">{portfolio_change_stocks:.2f}%</p>
                    </div>
                    <div class="summary-item">
                        <h3>Variação Diária</h3>
                        <p class="{portfolio_daily_change_class}">{portfolio_daily_change:.2f}%</p>
                    </div>
                    <div class="summary-item">
                        <h3>Variação Semanal</h3>
                        <p class="{portfolio_weekly_change_class}">{portfolio_weekly_change:.2f}%</p>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>Métricas de Risco</h2>
                <div class="summary">
                    <div class="summary-item">
                        <h3>VaR Semanal (95%)</h3>
                        <p>{portfolio_var_1_week[1]:.2f}%</p>
                    </div>
                    <div class="summary-item">
                        <h3>VaR Mensal (95%)</h3>
                        <p>{portfolio_var_1_month[1]:.2f}%</p>
                    </div>
                </div>
            </div>
            
            <h2 class="section-title">Ações em Carteira</h2>
            <div class="card">
                <table>
                    <thead>
                        <tr>
                            <th>Ticker</th>
                            <th>Preço Atual</th>
                            <th>Quantidade</th>
                            <th>PM</th>
                            <th>Financeiro</th>
                            <th>PnL</th>
                            <th>Variação (%)</th>
                            <th>Peso (%)</th>
                            <th>VaR Semanal (%)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {stocks_rows}
                    </tbody>
                </table>
            </div>
            
            <h2 class="section-title">Variação dos Ativos</h2>
            <div class="card">
                <table>
                    <thead>
                        <tr>
                            <th>Ticker</th>
                            <th>Retorno Diário (%)</th>
                            <th>Retorno Semanal (%)</th>
                            <th>Retorno Mensal (%)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {change_rows}
                    </tbody>
                </table>
            </div>
            
            {options_section}
            
        </div>
    </body>
    </html>
    """
    
    try:
        # Formatar valores monetários
        pl_format = f"{portfolio_data['current_pl']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        receber_format = f"{portfolio_data['receber']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        pagar_format = f"{portfolio_data['pagar']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        # Determinar classes CSS para variações
        portfolio_change = portfolio_data['portfolio_change'] * 100 if isinstance(portfolio_data['portfolio_change'], float) else 0
        portfolio_change_stocks = portfolio_data['portfolio_change_stocks'] * 100 if isinstance(portfolio_data['portfolio_change_stocks'], float) else 0
        
        portfolio_change_class = "positive" if portfolio_change >= 0 else "negative"
        portfolio_change_stocks_class = "positive" if portfolio_change_stocks >= 0 else "negative"
        portfolio_daily_change_class = "positive" if portfolio_data['portfolio_daily_change'] >= 0 else "negative"
        portfolio_weekly_change_class = "positive" if portfolio_data['portfolio_weekly_change'] >= 0 else "negative"
        
        # Gerar linhas da tabela de ações - ORDENADAS POR PNL
        stocks_rows = ""
        
        # Ordenar os ativos por PnL (decrescente)
        sorted_stocks = sorted(portfolio_data['df_stocks_dict'], 
                              key=lambda x: x.get('profit_loss', 0), 
                              reverse=True)  # reverse=True para ordenar do maior para o menor
        
        for stock in sorted_stocks:
            ticker = stock.get('index', '')
            current_price = stock.get('current_price', 0)
            quantity = stock.get('quantity', 0)
            average_price = stock.get('average_price', 0)
            current_value = stock.get('current_value', 0)
            profit_loss = stock.get('profit_loss', 0)
            percentage_change = stock.get('percentage_change', 0)
            pcts_port = stock.get('pcts_port', 0)
            var_1_week = stock.get('VaR 1 semana', 0)
            
            # Verificar NaN e substituir
            var_1_week = 0 if isinstance(var_1_week, float) and (var_1_week != var_1_week) else var_1_week
            
            pnl_class = "positive" if profit_loss >= 0 else "negative"
            var_class = "positive" if percentage_change >= 0 else "negative"
            
            stocks_rows += f"""
            <tr>
                <td>{ticker}</td>
                <td>R$ {current_price:.2f}</td>
                <td>{quantity}</td>
                <td>R$ {average_price:.2f}</td>
                <td>R$ {current_value:,.2f}</td>
                <td class="{pnl_class}">R$ {profit_loss:,.2f}</td>
                <td class="{var_class}">{percentage_change:.2f}%</td>
                <td>{pcts_port:.2f}%</td>
                <td>{var_1_week:.2f}%</td>
            </tr>
            """
        
        # Gerar linhas da tabela de variações - ORDENADAS POR RETORNO SEMANAL
        change_rows = ""
        
        # Extrair dados de variação dos ativos
        change_df_dict = portfolio_data['change_df_dict']
        
        # Verificar o formato dos dados (list ou dict)
        if isinstance(change_df_dict, list):
            # Se for uma lista de dicionários, ordenar por Retorno Semanal (%)
            sorted_changes = sorted(change_df_dict, 
                                   key=lambda x: x.get('Retorno Semanal (%)', 0) 
                                   if not (isinstance(x.get('Retorno Semanal (%)', 0), float) and 
                                          (x.get('Retorno Semanal (%)', 0) != x.get('Retorno Semanal (%)', 0))) 
                                   else -float('inf'),  # Coloca NaN no final
                                   reverse=True)  # ordenar do maior para o menor
            
            for item in sorted_changes:
                ticker = item.get('index', '')
                daily = item.get('Retorno Diário (%)', 0)
                weekly = item.get('Retorno Semanal (%)', 0)
                monthly = item.get('Retorno Mensal (%)', 0)
                
                # Converter NaN para 0
                daily = 0 if isinstance(daily, float) and (daily != daily) else daily  # Verificação para NaN
                weekly = 0 if isinstance(weekly, float) and (weekly != weekly) else weekly
                monthly = 0 if isinstance(monthly, float) and (monthly != monthly) else monthly
                
                daily_class = "positive" if daily >= 0 else "negative"
                weekly_class = "positive" if weekly >= 0 else "negative"
                monthly_class = "positive" if monthly >= 0 else "negative"
                
                change_rows += f"""
                <tr>
                    <td>{ticker}</td>
                    <td class="{daily_class}">{daily:.2f}%</td>
                    <td class="{weekly_class}">{weekly:.2f}%</td>
                    <td class="{monthly_class}">{monthly:.2f}%</td>
                </tr>
                """
        else:
            # Se for um dicionário de listas
            if 'index' in change_df_dict:
                indices = change_df_dict.get('index', [])
                weekly_returns = change_df_dict.get('Retorno Semanal (%)', [0] * len(indices))
                
                # Criar pares (índice, retorno semanal)
                idx_returns = []
                for i, ticker in enumerate(indices):
                    weekly_return = weekly_returns[i] if i < len(weekly_returns) else 0
                    # Verificar se é NaN
                    if isinstance(weekly_return, float) and (weekly_return != weekly_return):
                        weekly_return = -float('inf')  # Colocar NaN no final da ordenação
                    idx_returns.append((i, ticker, weekly_return))
                
                # Ordenar por retorno semanal (decrescente)
                sorted_idx_returns = sorted(idx_returns, key=lambda x: x[2], reverse=True)
                
                for i, ticker, _ in sorted_idx_returns:
                    # Obter valores usando o índice original
                    if 'Retorno Diário (%)' in change_df_dict and i < len(change_df_dict['Retorno Diário (%)']):
                        daily = change_df_dict['Retorno Diário (%)'][i]
                    else:
                        daily = 0
                        
                    if 'Retorno Semanal (%)' in change_df_dict and i < len(change_df_dict['Retorno Semanal (%)']):
                        weekly = change_df_dict['Retorno Semanal (%)'][i]
                    else:
                        weekly = 0
                        
                    if 'Retorno Mensal (%)' in change_df_dict and i < len(change_df_dict['Retorno Mensal (%)']):
                        monthly = change_df_dict['Retorno Mensal (%)'][i]
                    else:
                        monthly = 0
                        
                    # Converter NaN para 0
                    daily = 0 if isinstance(daily, float) and (daily != daily) else daily
                    weekly = 0 if isinstance(weekly, float) and (weekly != weekly) else weekly
                    monthly = 0 if isinstance(monthly, float) and (monthly != monthly) else monthly
                    
                    daily_class = "positive" if daily >= 0 else "negative"
                    weekly_class = "positive" if weekly >= 0 else "negative"
                    monthly_class = "positive" if monthly >= 0 else "negative"
                    
                    change_rows += f"""
                    <tr>
                        <td>{ticker}</td>
                        <td class="{daily_class}">{daily:.2f}%</td>
                        <td class="{weekly_class}">{weekly:.2f}%</td>
                        <td class="{monthly_class}">{monthly:.2f}%</td>
                    </tr>
                    """
        
        # Seção de opções (se houver)
        options_section = ""
        if portfolio_data.get('df_opts_table', []):
            options_rows = ""
            
            for opt in portfolio_data['df_opts_table']:
                ticker = opt.get('index', '')
                tipo = opt.get('Tipo', '')
                vencimento = opt.get('Vencimento', '')
                strike = opt.get('Strike', 0)
                preco_atual = opt.get('Preço Atual', 0)
                quantidade = opt.get('Quantidade', 0)
                pm = opt.get('PM', 0)
                valor_atual = opt.get('Valor Atual', 0)
                pnl = opt.get('PnL', 0)
                variacao = opt.get('Variação', 0)
                ativo_subjacente = opt.get('Ativo Subjacente', '')
                preco_atual_ativo = opt.get('Preço Atual Ativo', 0)
                
                pnl_class = "positive" if pnl >= 0 else "negative"
                var_class = "positive" if variacao >= 0 else "negative"
                
                options_rows += f"""
                <tr>
                    <td>{ticker}</td>
                    <td>{tipo}</td>
                    <td>{vencimento}</td>
                    <td>R$ {strike:.2f}</td>
                    <td>R$ {preco_atual:.2f}</td>
                    <td>{quantidade}</td>
                    <td>R$ {pm:.2f}</td>
                    <td>R$ {valor_atual:,.2f}</td>
                    <td class="{pnl_class}">R$ {pnl:,.2f}</td>
                    <td class="{var_class}">{variacao:.2f}%</td>
                    <td>{ativo_subjacente}</td>
                    <td>R$ {preco_atual_ativo:.2f}</td>
                </tr>
                """
            
            if options_rows:
                options_section = f"""
                <h2 class="section-title">Opções em Carteira</h2>
                <div class="card">
                    <table>
                        <thead>
                            <tr>
                                <th>Ticker</th>
                                <th>Tipo</th>
                                <th>Vencimento</th>
                                <th>Strike</th>
                                <th>Preço Atual</th>
                                <th>Quantidade</th>
                                <th>PM</th>
                                <th>Financeiro</th>
                                <th>PnL</th>
                                <th>Variação (%)</th>
                                <th>Ativo Base</th>
                                <th>Preço Ativo</th>
                            </tr>
                        </thead>
                        <tbody>
                            {options_rows}
                        </tbody>
                    </table>
                </div>
                """
        
        # Substituir valores no template
        cota = portfolio_data.get('cota', 0)
        enquadramento = portfolio_data.get('enquadramento', 0) * 100
        limits_der = portfolio_data.get('limits_der', 0) * 100
        portfolio_var_1_week = portfolio_data.get('portfolio_var_1_week', [0, 0, 0])
        portfolio_var_1_month = portfolio_data.get('portfolio_var_1_month', [0, 0, 0])
        
        # Garantir que temos pelo menos 3 elementos nos arrays
        if len(portfolio_var_1_week) < 2:
            portfolio_var_1_week = [0, 0, 0]
        if len(portfolio_var_1_month) < 2:
            portfolio_var_1_month = [0, 0, 0]
        
        html_content = html_template.format(
            current_time=portfolio_data.get('current_time', ''),
            data=portfolio_data.get('data', ''),
            pl_format=pl_format,
            cota=cota,
            receber_format=receber_format,
            pagar_format=pagar_format,
            enquadramento=enquadramento,
            limits_der=limits_der,
            portfolio_change=portfolio_change,
            portfolio_change_class=portfolio_change_class,
            portfolio_change_stocks=portfolio_change_stocks,
            portfolio_change_stocks_class=portfolio_change_stocks_class,
            portfolio_daily_change=portfolio_data.get('portfolio_daily_change', 0),
            portfolio_daily_change_class=portfolio_daily_change_class,
            portfolio_weekly_change=portfolio_data.get('portfolio_weekly_change', 0),
            portfolio_weekly_change_class=portfolio_weekly_change_class,
            portfolio_var_1_week=portfolio_var_1_week,
            portfolio_var_1_month=portfolio_var_1_month,
            stocks_rows=stocks_rows,
            change_rows=change_rows,
            options_section=options_section
        )
        
        # Salvar o relatório HTML
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Relatório HTML gerado e salvo em: {report_path}")
        return str(report_path)
        
    except Exception as e:
        print(f"Erro ao gerar relatório HTML: {e}")
        print(f"Tipo do erro: {type(e)}")
        import traceback
        traceback.print_exc()
        
        # Criar um relatório de erro simples
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Erro ao Gerar Relatório</title>
        </head>
        <body>
            <h1>Erro ao Gerar Relatório</h1>
            <p>Ocorreu um erro durante a geração do relatório: {str(e)}</p>
        </body>
        </html>
        """
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(error_html)
            
        return str(report_path)