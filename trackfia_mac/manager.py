"""
Em algum momento proximo, o leitor_notas tera que ser transformado em um codigo de cases.
Ex.: case 1 para leitura da nota (com referencia de area e colunas), case 2 etc. Posso fazer o link especifico no comeco para cada
nota em cada data. Assim tambem acho que terei que fazer para o tratamento dos dados da nota e para encontrar a data.

Algumas coisas serao manuais agora nesse comeco, ate que eu me adapte melhor a essa leitura, inclusive integrando IA ao processo.
"""

import os
from pathlib import Path
from tqdm import tqdm
import pandas as pd
import numpy as np

from leitor_xml import *


# def calculate_PnL_averagePrices(df):
#     portfolio = {}
#     df['P&L'] = 0.0
#     df['average_price'] = 0.0
    
#     for index, row in df.iterrows():

#         ticker = row['ticker']
        
#         # if ticker == 'ABEV3':
#         #     break
        
#         quantity = row['quantidade']
#         price = row['preco']
#         financial = quantity * price
#         date = row['data']

#         # Inicializar o ticker no portfólio, se não existir
#         if ticker not in portfolio:
#             if len(ticker) <= 6:
#                 portfolio[ticker] = {'flag': 1, 'quantity': 0, 'total_cost': 0, 'average_price': 0.0}  # 1 para ação
#             elif len(ticker) >= 7:
#                 portfolio[ticker] = {'flag': 2, 'quantity': 0, 'total_cost': 0, 'average_price': 0.0}  # 2 para opção

#         portfolio[ticker]['short_selling'] = False # nao e short selling
        
#         if row['pos'] == 'C':  # Compra
#             # Atualizar dados
#             portfolio[ticker]['quantity'] += quantity
#             portfolio[ticker]['total_cost'] += financial
            
#             # PM
#             if portfolio[ticker]['quantity'] > 0: # para o caso de haver uma imprecisao na data de compra e venda e a venda aparecer antes da compra
#                 portfolio[ticker]['average_price'] = portfolio[ticker]['total_cost'] / portfolio[ticker]['quantity']
#                 df.at[index, 'average_price'] = portfolio[ticker]['average_price']
#             elif portfolio[ticker]['quantity'] == 0:
#                 portfolio[ticker]['average_price'] = 0.0
#                 df.at[index, 'average_price'] = portfolio[ticker]['average_price']
        
#         elif row['pos'] == 'V':  # Venda
#             if portfolio[ticker]['quantity'] > 0:  # Venda de posição comprada (long)
#                 # Preco e PnL
#                 average_price = portfolio[ticker]['average_price']
#                 pnl = (price - average_price) * quantity
#                 df.at[index, 'P&L'] = pnl
                
#                 # Atualizar dados
#                 portfolio[ticker]['quantity'] -= quantity
#                 portfolio[ticker]['total_cost'] -= average_price * quantity
                
#                 # Se venda completa, resetar PM
#                 if portfolio[ticker]['quantity'] == 0:
#                     portfolio[ticker]['average_price'] = 0.0
#                 df.at[index, 'average_price'] = portfolio[ticker]['average_price']
#             else:  # Short selling
#                 portfolio[ticker]['short_selling'] = True
            
#                 portfolio[ticker]['quantity'] -= quantity  # Incrementa posição short (quantidade negativa)
#                 portfolio[ticker]['total_cost'] += financial  # Atualiza o custo total com valor positivo
                
#                 # PM
#                 portfolio[ticker]['average_price'] = portfolio[ticker]['total_cost'] / abs(portfolio[ticker]['quantity'])
#                 df.at[index, 'average_price'] = portfolio[ticker]['average_price']

#     return portfolio, df


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



def adjustments(df):

    # asset_details1 = {
    # 'pos': 'C',
    # 'nome_cia': None,
    # 'quantidade': 886,
    # 'preco': 50.39,
    # 'financeiro': 886 * 50.39,
    # 'ticker': 'AZZA3',
    # 'data': pd.to_datetime('2024-08-01')
    # }
    
    # asset_details2 = {
    # 'pos': 'C',
    # 'nome_cia': None,
    # 'quantidade': 600,
    # 'preco': 27.00,
    # 'financeiro': 600 * 27.00,
    # 'ticker': 'BBAS3',
    # 'data': pd.to_datetime('2024-08-02')
    # }
    
    # # Venda simulada de AZZA3 (TODO: conferir dados na origem)
    # asset_details3 = {
    # 'pos': 'V',
    # 'nome_cia': None,
    # 'quantidade': 886,
    # 'preco': 50.39,
    # 'financeiro': 886 * 50.39,
    # 'ticker': 'AZZA3',
    # 'data': pd.to_datetime('2024-08-04')
    # }
    
    

    # em 20240801 AZZA3 substitui SOMA3 e ARZZ3. Fiz a adequacao manual, adicionando 
    # AZZA3 pelo PL que consta na carteira BTG de 20240801
    list_ex = ['SOMA3', 'ARZZ3']
    df = df[~df.ticker.isin(list_ex)]
    
    df_info1 = pd.DataFrame([asset_details1])
    df_info2 = pd.DataFrame([asset_details2])
    # df_info3 = pd.DataFrame([asset_details3])

    df = pd.concat([df, df_info1, df_info2], ignore_index=True)
    # df = pd.concat([df, df_info2], ignore_index=True)

    return df
    

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


def run_manager_brokerage_notes():
    
    df_firstpos = first_pos_fia()
    
    file_path = Path(Path.home(), 'Documents', 'GitHub', 'database', 'notas_teste')
    all_data, errors = main(file_path, broker='necton2')
       
    df_ops = pd.concat(all_data, axis=0)
    df_ops.reset_index(inplace=True, drop=True)
    
    df = pd.concat([df_firstpos, df_ops])
    df['ticker'] = df['ticker'].str.strip()
    df.reset_index(inplace=True, drop=True)
    
    df = df.sort_values('data')
    portfolio, df = calculate_PnL_averagePrices(df)
    
    return portfolio, df

