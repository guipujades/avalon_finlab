import os
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
from pathlib import Path
import pickle as pkl
from tqdm import tqdm


def parse_principal_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Header
    header = root.find('fundo/header')
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
    }
    header_df = pd.DataFrame([header_data])

    # Títulos Públicos
    titpublico = []
    for tit in root.findall('fundo/titpublico'):
        tit_data = {
            'isin': tit.find('isin').text,
            'codativo': tit.find('codativo').text,
            'cusip': tit.find('cusip').text,
            'dtemissao': tit.find('dtemissao').text,
            'dtoperacao': tit.find('dtoperacao').text,
            'dtvencimento': tit.find('dtvencimento').text,
            'qtdisponivel': float(tit.find('qtdisponivel').text),
            'pucompra': float(tit.find('pucompra').text),
            'principal': float(tit.find('principal').text),
        }
        titpublico.append(tit_data)
    titpublico_df = pd.DataFrame(titpublico)

    # Ações
    acoes = []
    for acao in root.findall('fundo/acoes'):
        acao_data = {
            'isin': acao.find('isin').text,
            'codativo': acao.find('codativo').text,
            'qtdisponivel': float(acao.find('qtdisponivel').text),
            'valorfindisp': float(acao.find('valorfindisp').text),
            'puposicao': float(acao.find('puposicao').text),
        }
        acoes.append(acao_data)
    acoes_df = pd.DataFrame(acoes)

    # Caixa
    caixa = root.find('fundo/caixa')
    caixa_data = {
        'isininstituicao': caixa.find('isininstituicao').text,
        'tpconta': caixa.find('tpconta').text,
        'saldo': float(caixa.find('saldo').text),
    }
    caixa_df = pd.DataFrame([caixa_data])

    # Provisões
    provisoes = []
    for prov in root.findall('fundo/provisao'):
        prov_data = {
            'codprov': prov.find('codprov').text,
            'credeb': prov.find('credeb').text,
            'dt': prov.find('dt').text,
            'valor': float(prov.find('valor').text),
        }
        provisoes.append(prov_data)
    provisoes_df = pd.DataFrame(provisoes)

    return {
        'header': header_df,
        'titpublico': titpublico_df,
        'acoes': acoes_df,
        'caixa': caixa_df,
        'provisoes': provisoes_df
    }


# file_path = Path(Path.home(), 'Downloads', 'FD40921027000131_20241101_20241102044458_AVALON_FIA.xml')
# df = parse_principal_xml(file_path)


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

